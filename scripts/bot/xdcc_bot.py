
import sys
import time
import tqdm
import select
import socket
import struct
import logging
import functools
import itertools
from scripts.bot.utilities import *
from scripts.bot.exceptions import *
from threading import Thread, Lock
from puffotter.print import pprint
from colorama import Fore, Back, Style
from more_itertools import consume, repeatfunc
from puffotter.units import human_readable_bytes
from scripts.bot.client import IRC_Client, Event, Source, Argument, Connect_Factory



class XDCC_Downloader(IRC_Client):

    logger = logging.getLogger("mainlogger")

    def __init__(self, user, pack):
        super().__init__()
        
        self.user = user
        self.pack = pack
        
        self.server = pack.server
        self.port = 6667
        self.addr = (self.server, self.port)
        
        self.channels = set([])
        self.nickname = user.nick
        self.username = user.user
        self.realname = user.real
        self.fallback_channel = pack.channel
        
        self.downloading = False
        self.progress = 0
        self.progress_bar = None

        self.xdcc_file = None

        self.struct_format = b"!I"
        self.ack_lock = Lock()

        self.socket = None
        self.xdcc_socket = None

        self.BUFFER_SIZE = 2048
        self.FILE_MODE = 'wb'

        self.process_printing_thread = Thread(target=self.progress_printer, daemon=True)
        self.chunk_time_stamps = []

        self.file_requested = False
        self.file_req_reply = False

        self.add_event_handler('welcome', self.on_welcome)
        self.add_event_handler('privmsg', self.on_prvt)
        self.add_event_handler('notice', self.on_notice)
        self.add_event_handler('dcc_data', self.write_dcc_data)
        self.add_event_handler('endofnames', self.on_endofnames)
        self.add_event_handler('endofwhois', self.on_endofwhois)
        self.add_event_handler('whoischannels', self.on_whoischannels)
        self.add_event_handler('xdcc_disconnect', self.on_xdcc_disconnect)


    def connect(self):
        try:
            self.socket = self.connect_factory(self.addr)
            colored_print('[+] Connected to server..', Fore.WHITE, Back.GREEN)
        except socket.error:
            if not self.reconn_tries >= self.max_reconn_tries:
                self.reconn_tries += 1
                
                time.sleep(3)
                self.connect()
            else:
                raise ConnectionFailure()


    def process_once(self, timeout=None):
        sockets = self.connections
        readable, _, _ = select.select(sockets, [], sockets, timeout)

        if readable:
            for sock in readable:
                if sock == self.xdcc_socket:
                    try:
                        data = self.xdcc_socket.recv(self.BUFFER_SIZE)
                        self.write_dcc_data(data)
                    except socket.error:
                        event = Event('xdcc_disconnect', _, _)
                        self._handle_event(event)
                        
                if sock == self.socket:
                    self.recv_data()
        else:
            time.sleep(timeout)


    def on_xdcc_disconnect(self, _):
        if self.xdcc_file is not None:
            self.xdcc_file.close()

        if self.progress < self.pack.size:
            raise DownloadIncomplete()
        else:
            raise DownloadComplete()


    def start(self, timeout=0.2):
        # Run the main infinite loop...
        once = functools.partial(self.process_once, timeout=timeout)
        consume(repeatfunc(once))

    

    def download(self):

        retry = False
        pause = 0
        message = ''
        
        try:
            self.connect()

            self.connected = True
            self.register_user()

            self.process_printing_thread.start()

            self.start()
        except ConnectionFailure:
            message = "Failed to connect to server.."

        except NoReply:
            message = "Bot didn't send any reply"
        
        except DownloadComplete:
            message = "Download completed successfully.."
            if self.xdcc_file is not None:
                self.xdcc_file.close()
        
        except AlreadyDownloaded:
            message = "File already downloaded.."
        
        
        colored_print(message, Fore.GREEN)
        time.sleep(pause)

        if not retry:
            sys.exit(0)

        
    
    def on_welcome(self, event):
        colored_print('[+] User registered successfully...', Fore.WHITE, Back.GREEN)

        self.whois(self.pack.bot)
        self.pong(self.real_server)
        self.join(self.fallback_channel)

    
    def on_notice(self, event):
        self.logger.debug("Notice from %s :: %s", event.source.sender, event.argument.message)
        
    
    def on_whoischannels(self, event):
        channels = event.argument.channels
        self.channels.update(channels)
    
    
    def on_endofwhois(self, event):
        if self.channels:
            self.join(self.channels)

    
    def on_endofnames(self, event):
        self.joined_channels.update(event.argument.channels)
        
        if len(self.joined_channels) >= len(self.channels) and not self.file_requested:
            self.request_package()

    

    def write_dcc_data(self, data):
        chunk_size = len(data)

        self.xdcc_file.write(data)

        self.progress += chunk_size
        self._ack()

        if self.progress >= self.pack.get_size():
            raise DownloadComplete()

    

    def _ack(self):
        try:
            payload = struct.pack(self.struct_format, self.progress)
        except struct.error:

            if self.struct_format == b"!I":
                self.struct_format = b"!L"
            elif self.struct_format == b"!L":
                self.struct_format = b"!Q"
            else:
                return

            self._ack()
            return

        def acker():
            self.ack_lock.acquire()
            try:
                self.xdcc_socket.send(payload)
            except socket.error:
                print(self.xdcc_socket)
                print('[+] arker timeout...')
            finally:
                self.ack_lock.release()
        Thread(target=acker).start()
        
    

    def on_prvt(self, event):
        if event.argument.receiver != self.nickname:
            return
        
        message = event.argument.message
        if 'DCC' in message:
            if 'SEND' in message:
                payload = message.rstrip('\001').split('SEND')[1].split()
                
                file_name = payload[0]
                ip = payload[1]
                port = payload[2]
                size = payload[3]

                self.pack.set_info(file_name, ip, port, size)
                
                if self.pack.file_exists(file_name):
                    if self.pack.current_size >= self.pack.size:
                        raise AlreadyDownloaded()
                    else:
                        resume_req = self.pack.get_resume_req()
                        self.ctcp(self.pack.bot, resume_req)
                
                else:
                    self.start_download()
                    
            if 'ACCEPT' in message:
                offset = message.split('ACCEPT')[1].rstrip('\001').split()[2]
                
                self.progress = int(offset)
                self.start_download(resume=True)
                
        
                
    def start_download(self, resume=False):
        if resume:
            self.FILE_MODE = 'ab'

        self.downloading = True

        try:
            addr = (self.pack.get_ip(), self.pack.get_port())
            self.xdcc_socket = Connect_Factory()(addr)
            self.xdcc_socket.settimeout(5)

            self.xdcc_file = open(self.pack.get_file_name(), self.FILE_MODE)
        except socket.error:
            raise XDCCSocketError()   

    
    def request_package(self):
        colored_print('[+] Requested the package..', Fore.WHITE, Back.GREEN)

        self.file_requested = True
        message = self.pack.get_package_req()
        self.prvt(self.pack.bot, message)


    def progress_printer(self):
        while not self.downloading:
            pass

        printing = self.downloading
        while printing:
            printing = self.downloading

            self.chunk_time_stamps.append({
                'timestamp': time.time(),
                'progress': self.progress
            })

            if len(self.chunk_time_stamps) > 0 and \
                time.time() - self.chunk_time_stamps[0]['timestamp'] > 7:
                self.chunk_time_stamps.pop(0)

            if len(self.chunk_time_stamps) > 0:
                progress_diff = self.progress - self.chunk_time_stamps[0]['progress']
                time_diff = time.time() - self.chunk_time_stamps[0]['timestamp']
                ratio = int(progress_diff / time_diff)
                speed = human_readable_bytes(ratio) + "/s"
            else:
                speed = "0B/s"

            
            percentage = "%.2f" % (100 * (self.progress / self.pack.size))

            message = " [{}]: ({}%) |{}/{}| ({})".format(
                self.pack.get_file_name(),
                percentage,
                human_readable_bytes(
                    self.progress, remove_trailing_zeroes=False
                ),
                human_readable_bytes(self.pack.get_size()),
                speed
            )

            pprint(message, end="\r", bg="lyellow", fg="black")
            time.sleep(0.1)
        self.logger.info('printer exitted')


    @property
    def connections(self):
        return [conn 
                for conn in [self.socket, self.xdcc_socket] 
                if conn is not None]