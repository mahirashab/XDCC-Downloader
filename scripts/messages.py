#!/usr/bin/python3

class HandleMessage:

    def __init__(self, irc_client):
        self.client = irc_client

    # 3.1.2 Nick message
    def NICK_message(self):
        msg = "NICK {}\r\n".format(self.client.nick_name).encode("utf-8")
        self.client.connection.send(msg)

    # 3.1.3 User message
    def USER_message(self):
        msg = "USER {} {} {} :{}\r\n".format(self.client.user, "*", "*", self.client.real_name).encode("utf-8")
        self.client.connection.send(msg)

    # 3.1.5 User mode message
    def MODE_message(self, nickname, mode, activate=True):
        if not self.client.user_registered: raise Exception("User not registered...") 
        if mode not in 'iwo0r': raise Exception('Invalid Mode.')

        if activate:
            msg = "MODE {} +{}\r\n".format(nickname, mode).encode("utf-8")
        else:
            msg = "MODE {} -{}\r\n".format(nickname, mode).encode("utf-8") 

        self.client.connection.send(msg)

    # 3.1.7 Quit
    def QUIT_message(self, message):
        msg = "QUIT :{}\r\n".format(message).encode("utf-8")
        self.client.connection.send(msg)

    # 3.2.1 Join message
    def JOIN_message(self, channels, keys=[]):
        cnl_code = ','.join(channels)
        key_code = ','.join(keys)

        msg = "JOIN {} {}\r\n".format(cnl_code, key_code).encode("utf-8")
        self.client.connection.send(msg)

    def LEAVE_all_channels(self):
        msg = "JOIN 0\r\n".encode("utf-8")
        self.client.connection.send(msg)

    # 3.2.2 Part message
    def PART_message(self, channels, message="See You In Hell..."):
        cnl_code = ','.join(channels)
        
        msg = "PART {} {}\r\n".format(cnl_code, message).encode("utf-8")
        self.client.connection.send(msg)

    # 3.2.4 Topic message
    def TOPIC_message(self, channel, topic=" ", change=False):
        if change:
            msg = "TOPIC {} :{}\r\n".format(channel, topic).encode("utf-8")
        else:
            msg = "TOPIC {}\r\n".format(channel).encode("utf-8")
        
        self.client.connection.send(msg)

    # 3.2.5 Names message
    def NAMES_message(self, channels, target=""):
        cnl_code = ','.join(channels)

        msg = "NAMES {}\r\n".format(cnl_code).encode("utf-8")
        self.client.connection.send(msg)

    # 3.2.6 List message
    def LIST_message(self, channels, topic=""):
        cnl_code = ','.join(channels)

        msg = "LIST {}\r\n".format(cnl_code).encode("utf-8")
        self.client.connection.send(msg)

    # 3.2.7 Invite message
    def INVITE_message(self, channels, nicknames, comment="Go Fuck Yourself."):
        cnl_code = ','.join(channels)
        user_code = ','.join(nicknames)

        msg = "INVITE {} {}\r\n".format(user_code, cnl_code).encode("utf-8")
        self.client.connection.send(msg)

    # 3.2.8 Kick command
    def KICK_message(self, channels, nicknames, comment="See ya Fellas!!!!"):
        cnl_code = ','.join(channels)
        user_code = ','.join(nicknames)

        msg = "KICK {} {} :{}\r\n".format(cnl_code, user_code, comment).encode("utf-8")
        self.client.connection.send(msg)

    # 3.3.1 Private messages
    def PRIVMSG_message(self, targets, message):
        tar_code = ','.join(targets)

        msg = "PRIVMSG {} :{}\r\n".format(tar_code, message).encode("utf-8")
        self.client.connection.send(msg)

    # 3.3.2 Notice
    def NOTICE_message(self, targets, message):
        tar_code = ','.join(targets)

        msg = "NOTICE {} :{}\r\n".format(tar_code, message).encode("utf-8")
        self.client.connection.send(msg)

    # 3.4.1 Motd message
    def MOTD_command(self, target):
        msg = "MOTD {}\r\n".format(target).encode("utf-8")
        self.client.connection.send(msg)
    
    # 3.4.2 Lusers message
    def LUSERS_command(self, target):
        msg = "LUSERS {}\r\n".format(target).encode("utf-8")
        self.client.connection.send(msg)

    # 3.4.3 Version message
    def VERSION_command(self, target):
        msg = "VERSION {}\r\n".format(target).encode("utf-8")
        self.client.connection.send(msg)

    # 3.4.4 Stats message
    def STATS_command(self, querry, target):
        if querry not in 'lmou': raise Exception("Invalid querry..")

        msg = "STATS {} {}\r\n".format(querry, target).encode("utf-8")
        self.client.connection.send(msg)

    # 3.4.5 Links message
    def LINKS_message(self, remoter_server):
        msg = "LINKS {}\r\n".format(remoter_server).encode("utf-8")
        self.client.connection.send(msg)

    # 3.4.6 Time message
    def TIME_command(self, target):
        msg = "TIME {}\r\n".format(target).encode("utf-8")
        self.client.connection.send(msg)


    def PONG_message(self, server):
        msg = "PONG :{}\r\n".format(server).encode("utf-8")
        self.client.connection.send(msg)
        print(msg.decode("utf-8"))


    # def send(self, command, massage):
    #     msg = "{} {}\r\n".format(command, massage).encode("utf-8")
    #     self.connection.send(msg)