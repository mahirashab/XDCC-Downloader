#!./env/bin/python3

import re
import socket
import logging
import scripts.events as events
from scripts.db.models import Message, Server


class IRC_Client:
    '''This is the main connection that is connected to the server...
       This pars the data, handles server messages and stores the data...
    '''

    def __init__(self, ):
        self.user_registered = False
        self.joined_channel = False
        self.replies_buffer = ""

        self.message_logger = logging.getLogger("MessageLogger")
        self.activity_logger = logging.getLogger("ActivityLogger")

        self.regexp = re.compile("^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?"
                            "(?P<command>[^ ]+)( *(?P<argument> .+))?")


    '''This function is used to connect to the server...
       This configures the first connection...
    '''
    def connect(self, server, port, channels, nick_name, user, realname, session, password=None, ssl=None):
        self.server = server
        self.port = port
        self.real_server = None

        self.user = user
        self.nick_name = nick_name
        self.real_name = realname

        self.db_session = session

        self.channels = channels
        self.password = password
        self.ssl = ssl
        self.connected = False

        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(5)
            self.connection.connect((self.server, self.port))
            self.connection.settimeout(None)
            self.activity_logger.info("Connected to server %s on port %d", self.server, self.port)
        except socket.error:
            self.connection.close()
            self.connected = False
            self.activity_logger.error("Couldn't connect to %s on port %d", self.server, self.port)
            return

        self.connected = True
        
        self.register_user()

    
    '''This function splits each message from the reply stream...
       And then sends tthe messages to be processed by process_replies()...
    '''
    def run_once(self):
        res_data = self.response()
        if res_data:
            splitted_message = res_data.split("\r\n")
            splitted_message[0] = self.replies_buffer + splitted_message[0]
            self.replies_buffer = splitted_message[-1]

            for reply in splitted_message[:-1]:
                if reply:
                    self.process_replies(reply)

    
    '''This is used to reconnect to the server is found disconnected....'''
    def reconnect(self):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(5)
            self.connection.connect((self.server, self.port))
            self.connection.settimeout(None)
            self.activity_logger.info("Retried connecting to server %s on port %d", self.server, self.port)
        except socket.error as err:
            self.connection.close()
            self.connected = False
            self.activity_logger.info("Retry connection failed to server %s on port %d", self.server, self.port)
            print("Error ::: ", err)
            return
        self.connected = True

    
    '''This disconnects from the server...'''
    def disconnect(self):
        try:
            self.LEAVE_all_channels()
            self.KILL_message("Leaving now.")
            self.connection.close()
        except:
            pass


    '''Registers the user...'''
    def register_user(self):
        self.NICK_message(self.nick_name)
        self.USER_message(self.user, self.real_name)
        self.activity_logger.info("Tried as %s(nick) on %s", self.nick_name, self.server)
        

    '''Receives the response snd decodes it...'''
    def response(self):
        return self.connection.recv(512).decode("utf-8")


    '''Returns the connection socket....'''
    def get_socket(self):
        if self.connected:
            return self.connection
        else: 
            return None


    '''This extracts the valid pvt message and stores it.'''
    def store_pvt_message(self, res):
        try:
            sender = re.match(r'^(:[^ ]+)', res).group(0)
            serial = re.search(r'(#[\d]+)', res).group(0)
            size = re.search(r'(\[[ .0-9]+[M|G]\])', res).group(0).replace(' ', '')
            file_name = re.search(r'([^ ]+)$', res).group(0)
            
            channel = re.search(r'(#[a-zA-Z]+)', res).group(0)
        except AttributeError:
            return None

        # This try block stores the data to the database...
        try:
            new_message = Message(sender=sender, serial=serial, size=size, name=file_name)

            server = self.db_session.query(Server).\
            filter(Server.server==self.server).\
            filter(Server.channel==channel).\
            first()

            if server:
                server.messages.append(new_message)
            else:
                server = Server(server=self.server, channel=channel)
                server.messages.append(new_message)

            self.db_session.add(server)
            self.db_session.commit()
        except IndexError:
            return None


        
    
    '''This processes each reply and handles the counter message...'''
    def process_replies(self, response):
        m = self.regexp.match(response)

        tags = m.group('tags')
        prefix = m.group('prefix')
        command = m.group('command')
        argument = m.group('argument')

        command = events.numeric.get(command, command).lower()
        # print("Command    ", prefix)
        # print("main response    ", response, "\r\n")

        if command == "privmsg":
            self.message_logger.info(response)
            self.store_pvt_message(response)
            return

        if command == "welcome":
            self.real_server = prefix
            self.user_registered = True
            self.activity_logger.info("logged as %s(nick) %s(real) on %s on port %s", self.nick_name, self.real_name, self.real_server, self.port)
            self.JOIN_message(self.channels)

        elif command == "nicknameinuse":
            if self.connected:
                self.nick_name += "a"
                self.register_user()
            else:
                self.reconnect()
                self.register_user()

        elif command == 'ping':
            self.PONG_message(self.real_server)

        elif command == "error":
            if "closing link" in argument.lower():
                self.connected = False
                self.connection.close()
        
        else:
            pass
            # print("Command    ", command)
            # print("main response    ", response, "\r\n")


    '''The below functions are used to send different messages to the server...
       Used RFC for reference...
    '''

    # 3.1.2 Nick message
    def NICK_message(self, nick_name):
        msg = f"NICK {nick_name}\r\n".encode("utf-8")
        self.connection.send(msg)

    # 3.1.3 User message
    def USER_message(self, user_name, real_name):
        msg = f"USER {user_name} * * :{real_name}\r\n".encode("utf-8")
        self.connection.send(msg)

    # 3.1.5 User mode message
    def MODE_message(self, nickname, mode, activate=True):
        if not self.user_registered: raise Exception("User not registered...") 
        if mode not in 'iwo0r': raise Exception('Invalid Mode.')

        if activate:
            msg = "MODE {} +{}\r\n".format(nickname, mode).encode("utf-8")
        else:
            msg = "MODE {} -{}\r\n".format(nickname, mode).encode("utf-8") 

        self.connection.send(msg)

    # 3.1.7 Quit
    def QUIT_message(self, message):
        msg = "QUIT :{}\r\n".format(message).encode("utf-8")
        self.connection.send(msg)

    # 3.2.1 Join message
    def JOIN_message(self, channels, keys=[]):
        channels = self.join_list(channels)
        keys = self.join_list(keys)

        msg = f"JOIN {channels} {keys}\r\n".encode("utf-8")
        self.connection.send(msg)

    def LEAVE_all_channels(self):
        msg = "JOIN 0\r\n".encode("utf-8")
        self.connection.send(msg)
        self.activity_logger.info("Leaving all channels of server %s", self.server)

    
    def KILL_message(self, message):
        msg = f"KILL {self.nick_name} {message}\r\n".encode("utf-8")
        self.connection.send(msg)
        self.activity_logger.info("Leaving server %s", self.server)
        


    def PONG_message(self, server):
        msg = "PONG :{}\r\n".format(server).encode("utf-8")
        self.connection.send(msg)
        print(msg.decode("utf-8"))


    def join_list(self, lst):
        joined = ""
        for i in range(0, len(lst)):
            if i == len(lst)-1:
                joined += lst[i]
            else:
                joined += lst[i] + ","
            
        return joined



