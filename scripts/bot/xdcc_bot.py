import time
import select
import socket
import struct
from colorama import Fore, Back
from scripts.bot.pack import Pack
from scripts.bot.user import User
from puffotter.print import pprint
from threading import Thread, Lock
from scripts.bot.exceptions import *
from scripts.bot.client import IRC_Client
from puffotter.units import human_readable_bytes 
from scripts.bot.utilities import Event, colored_print
from scripts.bot.server_connection import ServerConnection


class XDCC_Downloader(IRC_Client):
    
    def __init__(self, server_connection, pack, user, iter_count=1):
        if iter_count > 5:
            raise TooManyRetries()
        
        super().__init__(server_connection, user)
        self.iter_count = iter_count
        self.display_message = ''
        
        self.pack = pack
        self.fallback_channels = [c.lower() for c in pack.fallback_channels]
        
        self.reverse_dcc = False
        self.downloading = False
        self.progress = 0

        self.struct_format = b"!I"
        self.ack_lock = Lock()

        self.FILE_MODE = 'wb'
        self.xdcc_file = None
        self.BUFFER_SIZE = 2048
        self.xdcc_connection = None
        

        self.process_printing_thread = Thread(target=self.progress_printer, daemon=True)
        self.message_printing_thread = Thread(target=self.message_printer, daemon=True)
        
        self.chunk_time_stamps = []

        self.file_req_times = 0
        self.last_request_time = 0
        self.file_requested = False
        self.file_req_reply = False

        self.add_event_handler('privmsg', self.on_prvt)
        self.add_event_handler('notice', self.on_notice)
        self.add_event_handler('welcome', self.on_welcome)
        self.add_event_handler('dcc_data', self.write_dcc_data)
        self.add_event_handler('endofwhois', self.on_endofwhois)
        self.add_event_handler('endofnames', self.on_endofnames)
        self.add_event_handler('whoischannels', self.on_whoischannels)
        self.add_event_handler('xdcc_disconnect', self.on_xdcc_disconnect)


    def connect(self):
        self.server_connection.create_pipe()
        self.display_message = '[+] Connected to server..'

    
    def close(self):
        if self.server_connection:
            self.leave_irc_server()
            self.server_connection.close_pipe()
        
        if self.xdcc_connection:
            self.xdcc_connection.close_pipe()
        
        if self.xdcc_file:
            self.xdcc_file.close()

        self.runloop = False
        self.downloading = False
        self.connected = False
        self.display_message = ''


    def process_once(self, timeout=0):
        conns = self.connections
        readable, _, _ = select.select(conns, [], conns, timeout)
    
        if readable:
            for sock in readable:
                if sock == self.xdcc_connection:
                    try:
                        data = self.xdcc_connection.recv()
                        self.write_dcc_data(data)
                    except socket.error:
                        print(socket.errno)
                        event = Event('xdcc_disconnect', _, _)
                        self._handle_event(event)   
                elif sock == self.server_connection:
                    self.recv_data()
        else:
            self.check_replies()
            time.sleep(timeout)


    def process_forever(self, timeout=0.1):
        while self.runloop:
            self.process_once(timeout=timeout)
        

    def download(self):
        pause = 0
        message = ''
        retry = False
        error = False
        color =  Back.LIGHTGREEN_EX, Fore.BLACK

        try:
            self.connect()

            self.connected = True
            self.register_user()

            self.process_printing_thread.start()
            self.message_printing_thread.start()

            self.process_forever()
        except ConnectionFailure:
            retry = True
            error = True
            message = "Failed to connect to server.."
        except NoReply:
            error = True
            message = "Bot didn't send any reply.."
        except NoSuchNick:
            error = True
            message = "No bot or user has the given nickname {}..".format(self.pack.bot)
        except AckerError:
            retry = True
            pause = 3
            self.logger.debug("Acker error")
        except XDCCSocketError:
            error = True
            message = "XDCC connection reset by peer. Check logs for Cause.."
        except DownloadIncomplete:
            pause = 3
            retry = True
            message = "Download incomplete.."
        except DownloadComplete:
            message = "Download completed successfully.."    
        except AlreadyDownloaded:
            message = "File already downloaded.."
        except TooManyRetries:
            error = True
            message = "Tried too meny times. Check main log for cause of Failure.."
        except KeyboardInterrupt:
            error = True
            message = "Cancelled the current download.."
        finally:
            self.close()
            time.sleep(0.5)

        if error:
            color = Back.LIGHTYELLOW_EX, Fore.LIGHTRED_EX
        
        colored_print(message, color)
        time.sleep(pause)

        if retry:
            new_instance = XDCC_Downloader.from_previous_bot(self)
            new_instance.download()


    
    def on_welcome(self, event):
        self.display_message = '[+] User registered successfully..'

        self.whois(self.pack.bot)
        self.pong(self.real_server)
        self.join(self.fallback_channels)
        
    
    def on_whoischannels(self, event):
        channels = event.argument.channels
        self.channels.update(channels)
    
    
    def on_endofwhois(self, event):
        if self.channels:
            self.join(self.channels)

    
    def on_endofnames(self, event):
        self.joined_channels.update(event.argument.channels)
        
        if len(self.joined_channels) >= len(self.channels) and not self.file_requested:
            time.sleep(0.5)
            self.request_package()
        
    
    def on_xdcc_disconnect(self, _):
        if self.progress >= self.pack.size:
            raise DownloadComplete()
        else:
            raise XDCCSocketError()


    def write_dcc_data(self, data):
        self.xdcc_file.write(data)

        chunk_size = len(data)
        self.progress += chunk_size
        self._ack()

        if self.progress >= self.pack.size:
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
                print(socket.errno)
                self.logger.debug('Arker failure...')
                raise AckerError()
            finally:
                self.ack_lock.release()
        acker()
        

    def on_prvt(self, event):
        if event.argument.receiver != self.nickname:
            return
        
        message = event.argument.message
        if 'DCC' in message:
            self.logger.debug(message)
            if 'SEND' in message:
                self.file_req_reply = True
                payload = message.strip('\001').split('SEND')[1].split()

                numeric_info = []
                token = ''
                for index, word in enumerate(reversed(payload)):
                    if word.isnumeric():
                        numeric_info.insert(0, int(word))
                    else:
                        if len(payload[:-index]) > 1:
                            file_name = ' '.join(payload[:-index]).strip('"')
                        else:
                            file_name = ''.join(payload[:-index])
                        self.logger.debug(file_name)
                        break
                
                ip = numeric_info[0]
                port = int(numeric_info[1])
                size = int(numeric_info[2])
                if len(numeric_info) == 4:
                    self.reverse_dcc = True
                    token = numeric_info[3]

                self.pack.set_info(file_name, ip, port, size, token)

                
                if self.pack.file_exists(file_name):
                    if self.pack.current_size() >= self.pack.size:
                        raise AlreadyDownloaded()
                    
                    if self.reverse_dcc:
                        resume_req = self.pack.get_reversed_dcc_resume_req()
                    else:
                        resume_req = self.pack.get_resume_req()
                        
                    self.ctcp(self.pack.bot, resume_req)
                else:
                    if self.reverse_dcc:
                        ack_msg = self.pack.get_reversed_dcc_accept_msg()
                        self.ctcp(self.pack.bot, ack_msg)
                    
                    self.start_download()
                    
            if 'ACCEPT' in message:
                payload = message.split('ACCEPT')[1].rstrip('\001').split()

                numeric_info = []
                for index, word in enumerate(reversed(payload)):
                    if word.isnumeric():
                        numeric_info.insert(0, int(word))
                    else:
                        break
                
                if self.reverse_dcc:
                    self.progress = int(numeric_info[-2])
                    ack_msg = self.pack.get_reversed_dcc_accept_msg()
                    self.ctcp(self.pack.bot, ack_msg)
                else:
                    self.progress = int(numeric_info[-1])

                self.start_download(resume=True)
        else:
            self.logger.debug("PRIVMSG form %s ::%s", event.source.sender, event.argument.message)
                   

    def start_download(self, resume=False):
        if resume:
            self.FILE_MODE = 'ab'

        try:
            self.xdcc_connection = ServerConnection(self.pack.ip, 
                                                    None,
                                                    self.BUFFER_SIZE,
                                                    port=self.pack.port,
                                                    reversed_conn=self.reverse_dcc)
            
            self.xdcc_connection.create_pipe()
            self.xdcc_file = open(self.pack.get_file_path(), self.FILE_MODE)

            self.downloading = True
        except socket.error:
            raise XDCCSocketError()  


    def message_printer(self):
        while not self.display_message:
            pass

        previous_message = ''
        printing = self.display_message and not self.downloading
        while printing:
            printing = self.display_message and not self.downloading

            pprint(' '*len(previous_message), end="\r", bg="black")
            pprint(' '+self.display_message, end='\r', bg='lgreen', fg='black')

            previous_message = self.display_message + ' '
            time.sleep(0.1)
        self.logger.info('Message printer exitted')


    def progress_printer(self):
        while not self.downloading:
            pass

        printing = self.downloading
        last_printed = ''
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
                self.pack.file_name,
                percentage,
                human_readable_bytes(
                    self.progress, remove_trailing_zeroes=False
                ),
                human_readable_bytes(self.pack.size),
                speed
            )

            pprint(' '*len(last_printed), end="\r", bg="black")
            pprint(message, end="\r", bg="lyellow", fg="black")
            last_printed = message

            time.sleep(0.1)

        self.logger.info('Download printer exitted')

    
    def check_replies(self):
        time_delta = time.time() - self.last_request_time

        if time_delta < 60 or self.file_req_reply or not self.file_requested:
            return

        if self.file_req_times > 5:
            raise NoReply()
        
        self.request_package()


    def request_package(self):
        self.display_message = '[+] Requested the package..'

        self.file_req_times += 1
        self.file_requested = True
        self.last_request_time = time.time()

        message = self.pack.get_package_req()
        self.prvt(self.pack.bot, message)


    @classmethod
    def from_previous_bot(cls, pre_xdcc_bot):
        server_connection = ServerConnection(pre_xdcc_bot.server_connection.server,
                                            'utf-8',
                                            512)
        
        pack =  Pack(pre_xdcc_bot.fallback_channels, 
                    pre_xdcc_bot.pack.bot, 
                    pre_xdcc_bot.pack.package, 
                    file_path=pre_xdcc_bot.pack.file_path)
        
        user = User() 
        
        return cls(server_connection, pack, user,
                    iter_count=pre_xdcc_bot.iter_count+1)
        

    @property
    def connections(self):
        return [conn 
                for conn in [self.server_connection, self.xdcc_connection] 
                if conn and conn.is_connected()]