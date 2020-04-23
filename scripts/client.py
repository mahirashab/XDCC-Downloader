#!/usr/bin/python3
import socket
import re
import logging
import scripts.events as events


class IRC_Client:

    def __init__(self, ):
        self.user_registered = False
        self.joined_channel = False
        self.message_logger = logging.getLogger("MessageLogger")
        self.activity_logger = logging.getLogger("ActivityLogger")

        self.replies_buffer = ""

        self.regexp = re.compile("^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?"
                            "(?P<command>[^ ]+)( *(?P<argument> .+))?")
        

    def connect(self, server, port, channels, nick_name, user, realname):
        self.server = server
        self.real_server = None
        self.port = port
        self.nick_name = nick_name
        self.user = user
        self.real_name = realname
        self.channels = channels

        self.connected = False

        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((self.server, self.port))
            self.activity_logger.info("Connected to server %s on port %d", self.server, self.port)
        except socket.error as err:
            self.connection.close()
            self.connected = False
            self.activity_logger.error("Couldn't connect to %s on port %d", self.server, self.port)
            print("Error ::: ", err)
            return

        self.connected = True
        
        self.register_user()

    
    def run_once(self):
        res_data = self.response()
        if res_data:
            splitted_message = res_data.split("\r\n")
            splitted_message[0] = self.replies_buffer + splitted_message[0]
            self.replies_buffer = splitted_message[-1]

            for reply in splitted_message[:-1]:
                if reply:
                    self.process_replies(reply)
        



    def process_replies(self, response):
        m = self.regexp.match(response)

        tags = m.group('tags')
        prefix = m.group('prefix')
        command = m.group('command')
        argument = m.group('argument')

        command = events.numeric.get(command, command).lower()
        print("Command    ", prefix)
        # print("main response    ", response, "\r\n")

        if command == "privmsg":
            print("main response    ", response, "\r\n")
            self.message_logger.info(response)
            return

        if command == "welcome":
            self.real_server = prefix
            self.user_registered = True
            self.activity_logger.info("logged as %s %s on %s on port %s", self.nick_name, self.real_name, self.real_server, self.port)
            self.JOIN_message(self.channels)

        elif command == "nicknameinuse":
            if self.connected:
                self.nick_name += "a"
                self.register_user()
            else:
                self.reconnect()
                print("server reconnected")
                self.register_user()

        elif command == "error":
            if "closing link" in argument.lower():
                self.connected = False
                self.connection.close()
                print("closed connection...")

    def register_user(self):
        self.NICK_message(self.nick_name)
        self.USER_message(self.user, self.real_name)
        self.activity_logger.info("Tried as %s %s on %s on port %s", self.nick_name, self.real_name, self.real_server, self.port)
        

    def response(self):
        return self.connection.recv(512).decode("utf-8")

    def get_socket(self):
        if self.connected:
            return self.connection
        else: 
            return None

    def reconnect(self):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((self.server, self.port))
            self.activity_logger.info("Retried connecting to server %s on port %d", self.server, self.port)
        except socket.error as err:
            self.connection.close()
            self.connected = False
            self.activity_logger.info("Retry connection failed to server %s on port %d", self.server, self.port)
            print("Error ::: ", err)
            return
        self.connected = True



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
        print(msg.decode("utf-8"))
        self.connection.send(msg)

    def LEAVE_all_channels(self):
        msg = "JOIN 0\r\n".encode("utf-8")
        self.connection.send(msg)

    # 3.2.2 Part message
    def PART_message(self, channels, message="See You In Hell..."):
        cnl_code = ','.join(channels)
        
        msg = "PART {} {}\r\n".format(cnl_code, message).encode("utf-8")
        self.connection.send(msg)

    # 3.2.4 Topic message
    def TOPIC_message(self, channel, topic=" ", change=False):
        if change:
            msg = "TOPIC {} :{}\r\n".format(channel, topic).encode("utf-8")
        else:
            msg = "TOPIC {}\r\n".format(channel).encode("utf-8")
        
        self.connection.send(msg)

    # 3.2.5 Names message
    def NAMES_message(self, channels, target=""):
        cnl_code = ','.join(channels)

        msg = "NAMES {}\r\n".format(cnl_code).encode("utf-8")
        self.connection.send(msg)

    # 3.2.6 List message
    def LIST_message(self, channels, topic=""):
        cnl_code = ','.join(channels)

        msg = "LIST {}\r\n".format(cnl_code).encode("utf-8")
        self.connection.send(msg)

    # 3.2.7 Invite message
    def INVITE_message(self, channels, nicknames, comment="Go Fuck Yourself."):
        cnl_code = ','.join(channels)
        user_code = ','.join(nicknames)

        msg = "INVITE {} {}\r\n".format(user_code, cnl_code).encode("utf-8")
        self.connection.send(msg)

    # 3.2.8 Kick command
    def KICK_message(self, channels, nicknames, comment="See ya Fellas!!!!"):
        cnl_code = ','.join(channels)
        user_code = ','.join(nicknames)

        msg = "KICK {} {} :{}\r\n".format(cnl_code, user_code, comment).encode("utf-8")
        self.connection.send(msg)

    # 3.3.1 Private messages
    def PRIVMSG_message(self, targets, message):
        tar_code = ','.join(targets)

        msg = "PRIVMSG {} :{}\r\n".format(tar_code, message).encode("utf-8")
        self.connection.send(msg)

    # 3.3.2 Notice
    def NOTICE_message(self, targets, message):
        tar_code = ','.join(targets)

        msg = "NOTICE {} :{}\r\n".format(tar_code, message).encode("utf-8")
        self.connection.send(msg)

    # 3.4.1 Motd message
    def MOTD_command(self, target):
        msg = "MOTD {}\r\n".format(target).encode("utf-8")
        self.connection.send(msg)
    
    # 3.4.2 Lusers message
    def LUSERS_command(self, target):
        msg = "LUSERS {}\r\n".format(target).encode("utf-8")
        self.connection.send(msg)

    # 3.4.3 Version message
    def VERSION_command(self, target):
        msg = "VERSION {}\r\n".format(target).encode("utf-8")
        self.connection.send(msg)

    # 3.4.4 Stats message
    def STATS_command(self, querry, target):
        if querry not in 'lmou': raise Exception("Invalid querry..")

        msg = "STATS {} {}\r\n".format(querry, target).encode("utf-8")
        self.connection.send(msg)

    # 3.4.5 Links message
    def LINKS_message(self, remoter_server):
        msg = "LINKS {}\r\n".format(remoter_server).encode("utf-8")
        self.connection.send(msg)

    # 3.4.6 Time message
    def TIME_command(self, target):
        msg = "TIME {}\r\n".format(target).encode("utf-8")
        self.connection.send(msg)


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



