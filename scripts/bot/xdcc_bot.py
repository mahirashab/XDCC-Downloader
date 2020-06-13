
import tqdm
import time
import select
import socket
import logging
import functools
import itertools
from threading import Thread, Lock
import struct
from scripts.bot.client import IRC_Client, Event, Source, Argument, Connect_Factory
from more_itertools import consume, repeatfunc


class XDCC_Downloader(IRC_Client):

    main_log = logging.getLogger("mainlogger")
    msg_log = logging.getLogger("messagelogger")

    def __init__(self, user, pack):
        super().__init__()
        
        self.user = user
        self.pack = pack
        
        self.server = pack.server
        self.port = 6667
        self.addr = (self.server, self.port)
        
        self.channels = [pack.channel]
        self.nickname = user.nick
        self.username = user.user
        self.realname = user.real
        
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
        
        self.handlers.update({
            'privmsg': self.on_prvt,
            'notice': self.on_notice,
            'dcc_data': self.write_dcc_data,
            'endofnames': self.on_endofnames,
            'endofwhois': self.on_endofwhois,
            'whoischannels': self.on_whoischannels,
        })
        
    def connect(self):
        try:
            self.socket = self.connect_factory(self.addr)
            self.socket.settimeout(None)

            self.main_log.info(
                    "Connected to (server=%s) on (port=%d)", 
                                self.server, 
                                self.port)
            print('[+] Connected to server..')
        except socket.error:
            self.main_log.critical(
                    "Couldn't connect to (server=%s) (port=%d)", 
                                self.server, 
                                self.port)

            self.socket = None
            return None

        self.connected = True
        self.register_user()

    
    def process_once(self, timeout=None):
        sockets = self.connections
        readable, writable, error = select.select(sockets, [], sockets, timeout)

        if readable or error:
            for sock in readable:
                if sock == self.xdcc_socket:
                    data = self.xdcc_socket.recv(self.BUFFER_SIZE)
                    # event = Event('dcc_data', Source(''), Argument(data))
                    self.write_dcc_data(data)
                else:
                    self.recv_data()

            for sock in error:
                if sock == self.xdcc_socket:
                    print('[+] XDCC socket error..')
                    self.xdcc_file.close()
        else:
            time.sleep(timeout)       


    def process_forever(self, timeout=0.2):
        # Run the main infinite loop...
        self.connect()
        once = functools.partial(self.process_once, timeout=timeout)
        consume(repeatfunc(once))
        
        
    
    def on_welcome(self, event):
        print('[+] User registered successfully...')
        self.user_registered = True
        self.whois(self.pack.bot)
    
    def on_notice(self, event):
        self.main_log.debug("Notice from %s :: %s", event.source.sender, event.argument.message)
        
    
    def on_whoischannels(self, event):
        self.add_channels(event.argument.channel)
    
    
    def on_endofwhois(self, event):
        self.join_msg(self.channels)

    
    def on_endofnames(self, event):
        self.joined_channels.append(event.argument.channel.lower())
        self.joined_channels = self.remove_duplicates(self.joined_channels)
        
        if len(self.joined_channels) >= len(self.channels):
            self.request_package()

    

    def write_dcc_data(self, data):
        length = len(data)

        self.xdcc_file.write(data)

        self.progress += length
        self.progress_bar.update(length)
        self._ack()

        if self.progress >= self.pack.get_size():
            print('[+] Download complete...')
            self.xdcc_file.close()

    
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
            except socket.timeout:
                print('[+] arker timeout...')
            finally:
                self.ack_lock.release()
        Thread(target=acker).start()
        
        
    def on_prvt(self, event):
        if event.argument.receiver != self.nickname:
            return
        
        message = event.argument.message
        print(message)
        if 'DCC' in message:
            if 'SEND' in message:
                payload = message.rstrip('\001').split('SEND')[1].split()
                
                file_name = payload[0]
                ip = payload[1]
                port = payload[2]
                size = payload[3]

                self.pack.set_info(file_name, ip, port, size)
                
                
                if self.pack.file_exists(file_name):
                    resume_req = self.pack.get_resume_req()
                    self.send_msg(resume_req)
                
                else:
                    self.start_download()
                    

                    
            if 'ACCEPT' in message:
                file_name, port, offset = message.split('ACCEPT')[1].rstrip('\001').split()
                
                self.pack.set_port(port)
                self.progress = int(offset)
                
                self.start_download(resume=True)
                
        
                
    def start_download(self, resume=False):
        if resume:
            self.FILE_MODE = 'ab'

        self.progress_bar = tqdm.tqdm(range(self.pack.get_size()), 
                                    f"\rReceiving {self.pack.get_file_name()}", 
                                    unit="B", 
                                    unit_scale=True, 
                                    unit_divisor=1024, 
                                    disable=False,
                                    initial=self.progress)

        try:
            addr = (self.pack.get_ip(), self.pack.get_port())
            self.xdcc_socket = Connect_Factory()(addr)

            self.xdcc_file = open(self.pack.get_file_name(), self.FILE_MODE)
        except socket.error:
            print('[+] XDCC socket connection error...')        
       
    
    def request_package(self):
        print('[+] Requesting package..')
        msg = self.pack.get_package_req()
        self.send_msg(msg)

    
    @property
    def connections(self):
        return [conn 
                for conn in [self.socket, self.xdcc_socket] 
                if conn is not None]