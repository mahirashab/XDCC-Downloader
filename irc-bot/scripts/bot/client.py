
import re
import os
import socket
from cmd2.ansi import style
from scripts.db.models import Download
from scripts.threader import Executor
from scripts.bot.xdcc import DCC_Client
from scripts.bot.base import BaseClient


class IRC_Client(BaseClient):
    '''This is the main connection that is connected to the server...
       This parses the data, handles server messages and stores the data...
    '''

    def __init__(self, Main_Bot=None):
        super().__init__()
        self.Main_Bot = Main_Bot
        self.temp_data = {}
        print(style("[+] New Client created.", fg='bright_cyan'))

    def connect(
            self,
            server,
            channels,
            port=6667,
            nick=None,
            user=None,
            real=None,
            password=None,
            ssl=None):
        
        self.server = server
        self.port = port
        self.address = (server, port)
        self.channels = channels

        self.nickname = nick or 'defaltee'
        self.username = user or 'user_defa'
        self.realname = real or 'defaulteen'

        self.password = password
        self.ssl = ssl

        try:
            self.socket = self.connect_factory.connect(self.address)
            self.socket.settimeout(None)

            print(style("[+] Connected to server..", fg='bright_cyan'))
            self.main_log.info(
                    "Connected to (server=%s) on (port=%d)", 
                                self.server, 
                                self.port)

        except socket.error:
            print(style("[+] Connection failed to server..", fg='bright_cyan'))
            self.main_log.critical(
                    "Couldn't connect to (server=%s) (port=%d)", 
                                self.server, 
                                self.port)

            self.socket = None
            return None

        self.connected = True
        if self.password:
            self.pass_msg(self.password)

        self.register_user()


    def prvt_handler(self, prefix, argument):
        # print(prefix, argument)
        sender = re.search(r'((?P<sender>.*)!)', prefix)
        regexp = re.compile(r"( ?(?P<receiver>[\w]*) :(?P<message>.*))")
        match = regexp.match(argument)

        if not match and sender: return
        
        receiver = match.group('receiver')
        sender = sender.group('sender')

        if self.nickname in receiver:
            self.main_log.debug("PRVT message :: %s", argument)

            message = match.group('message')
            if "SEND" in message:
                regexp = re.compile(r"((?P<file_name>[^ ]+) (?P<ip>[^ ]\d+) (?P<port>[^ ]\d+) (?P<size>[^ ]\d+)?)")
                match = regexp.search(message).group

                ip = match('ip')
                port = match('port')
                size = match('size')
                file_name = match('file_name')

                if os.path.exists(file_name):
                    length = os.path.getsize(file_name)
                    self.temp_data[sender] = {
                        'ip': ip,
                        'file_name': file_name,
                        'port': port,
                        'size':size
                    }

                    self.dcc_resume_request(sender, file_name, port, length)
                    return
 
                dcc = DCC_Client(ip, int(port), file_name, int(size))
                dcc.connect()
                Executor.submit(dcc.recv_data)
                # dcc.recv_data()

            elif "ACCEPT" in message:
                regexp = re.compile(r"(?P<file_name>[^ ]+) (?P<port>[^ ]\d+) (?P<offset>[^ ]\d+)")
                match = regexp.search(message).group

                data = self.temp_data[sender]

                file_name = match('file_name')
                port = match('port')
                offset = match('offset')
                size = data['size']
                ip = data['ip']

                print(ip, port)

                dcc = DCC_Client(ip, int(port), file_name, int(size), offset=offset)
                dcc.connect()
                Executor.submit(dcc.recv_data)
                # dcc.recv_data()


    def dcc_resume_request(self, sender, file_name, port, position):
        msg = "PRIVMSG {} :\001DCC RESUME {} {} {}\001".format(sender, file_name, port, position)
        self.send_msg(msg)

    
    def xdcc_request(self, target, file_name):
        msg = "PRIVMSG {} :\001XDCC send {}\001".format(target, file_name)

        msg_bytes = self.prepare_msg(msg)

        if not self.is_connected():
            print(style("[+] Server connection problem.", fg='bright_cyan'))
            return

        try:
            self.socket.send(msg_bytes)
            self.temp_data[target] = file_name
            
            print(style("[+] Dcc message sent.", fg='bright_cyan'))
        except socket.error:
            print(style("[+] Socket connection problem.", fg='bright_cyan'))
