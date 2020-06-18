
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
from scripts.bot.server_connection import ServerConnection
from more_itertools import consume, repeatfunc
from puffotter.units import human_readable_bytes
from scripts.bot.client import IRC_Client, Event, Source, Argument



class XDCC_Downloader(IRC_Client):

    def __init__(self, server_connection, user, pack):
        super().__init__(server_connection, user)
        
        self.pack = pack
        self.fallback_channel = pack.fallback_channel
        
        self.downloading = False
        self.progress = 0


        self.struct_format = b"!I"
        self.ack_lock = Lock()

        self.xdcc_file = None
        self.FILE_MODE = 'wb'
        self.BUFFER_SIZE = 2048
        self.xdcc_connection = None

        self.process_printing_thread = Thread(target=self.progress_printer, daemon=True)
        self.message_printing_thread = Thread(target=self.message_printer, daemon=True)
        
        self.chunk_time_stamps = []

        self.file_requested = False
        self.file_req_reply = False

        self.last_set = time.time()
        self.iter_count = 0

        self.add_event_handler('welcome', self.on_welcome)
        self.add_event_handler('privmsg', self.on_prvt)
        self.add_event_handler('notice', self.on_notice)
        self.add_event_handler('dcc_data', self.write_dcc_data)
        self.add_event_handler('endofnames', self.on_endofnames)
        self.add_event_handler('endofwhois', self.on_endofwhois)
        self.add_event_handler('whoischannels', self.on_whoischannels)
        self.add_event_handler('xdcc_disconnect', self.on_xdcc_disconnect)


    def times_in_sec(self):
        if int(time.time() - self.last_set) > 1:
            print(self.iter_count, " times in one sec...")
            self.iter_count = 0
        else:
            self.iter_count += 1


    def connect(self):
        self.server_connection.create_pipe()
        self.display_message = '[+] Connected to server..'
        # colored_print('[+] Connected to server..', Fore.WHITE, Back.GREEN)



    def process_once(self, timeout=None):
        conns = self.connections

        if conns:
            readable, _, _ = select.select(conns, [], conns, timeout)
        
            for sock in readable:
                if sock == self.xdcc_connection:
                    try:
                        data = self.xdcc_connection.recv()
                        self.write_dcc_data(data)
                    except socket.error:
                        event = Event('xdcc_disconnect', _, _)
                        self._handle_event(event)   
                elif sock == self.server_connection:
                    self.recv_data()
        else:
            pass
            # time.sleep(timeout)


    def start(self, timeout=0.2):
        # Run the main infinite loop...
        once = functools.partial(self.process_once, timeout=timeout)
        consume(repeatfunc(once))

    

    def download(self):

        retry = False
        error = False
        pause = 0
        message = ''
        
        try:
            self.connect()

            self.connected = True
            self.register_user()

            self.process_printing_thread.start()
            self.message_printing_thread.start()

            self.start()
        except ConnectionFailure:
            error = True
            message = "Failed to connect to server.."

        except NoReply:
            message = "Bot didn't send any reply"
        
        except NoSuchNick:
            error = True
            message = "No bot or user has the given nickname {}..".format(self.pack.bot)

        except DownloadComplete:
            message = "Download completed successfully.."
            if self.xdcc_file is not None:
                self.xdcc_file.close()
        
        except AlreadyDownloaded:
            message = "File already downloaded.."

        finally:
            self.close()
        
        if error:
            colored_print(message + '\n', Back.LIGHTYELLOW_EX, Fore.LIGHTRED_EX)
        else:
            colored_print(message + '\n', Back.LIGHTGREEN_EX, Fore.BLACK)

        time.sleep(pause)

        if not retry:
            sys.exit(0)

    
    def close(self):
        if self.server_connection:
            self.leave_irc_server()
            self.server_connection.close_pipe()
        
        if self.xdcc_connection:
            self.xdcc_connection.close_pipe()
        
        if self.xdcc_file:
            self.xdcc_file.close()
        

        self.downloading = False
        self.connected = False
        self.display_message = ''

        
    
    def on_welcome(self, event):
        self.display_message = '[+] User registered successfully..'
        # colored_print('[+] User registered successfully...', Fore.WHITE, Back.GREEN)

        self.whois(self.pack.bot)
        self.pong(self.real_server)
        self.join(self.fallback_channel)
        
    
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
        
    
    def on_xdcc_disconnect(self, _):
        print("xdcc_disconnect")
        self.xdcc_connection = None
        if self.xdcc_file is not None:
            self.xdcc_file.close()

        if self.progress < self.pack.size:
            raise DownloadIncomplete()
        else:
            raise DownloadComplete()
    

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
                self.xdcc_connection.send(payload)
            except socket.error:
                print(self.xdcc_connection)
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
                    if self.pack.current_size() >= self.pack.size:
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
            self.xdcc_connection = ServerConnection(self.pack.get_ip(), 
                                                    None,
                                                    self.BUFFER_SIZE,
                                                    port=self.pack.get_port())

            self.xdcc_connection.create_pipe()

            self.xdcc_file = open(self.pack.get_file_name(), self.FILE_MODE)
        except socket.error:
            raise XDCCSocketError()  


    def message_printer(self):
        previous_message = ''
        while not self.display_message:
            pass

        printing = self.display_message and not self.downloading
        while printing:
            printing = self.display_message and not self.downloading

            pprint(' '*len(previous_message), end="\r", bg="black")
            pprint(' '+self.display_message, end='\r', bg='lgreen', fg='black')

            previous_message = self.display_message
            time.sleep(0.1)



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


    def request_package(self):
        self.display_message = '[+] Requested the package..'
        # colored_print('[+] Requested the package..', Fore.WHITE, Back.GREEN)

        self.file_requested = True
        message = self.pack.get_package_req()
        self.prvt(self.pack.bot, message)

    @property
    def connections(self):
        return [conn 
                for conn in [self.server_connection, self.xdcc_connection] 
                if conn and conn.is_connected()]