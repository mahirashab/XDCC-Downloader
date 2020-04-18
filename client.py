#!/usr/bin/python3
import socket
import messages
import replies


class IRC_Client:

    def __init__(self, server="irc.freenode.net", port=6667, nick_name="scker", user="mahir", realname="mahir ashab"):
        self.server = server
        self.port = port
        self.nick_name = nick_name
        self.user = user
        self.real_name = realname

        self.connection = None
        self.user_registered = False
        self.joined_channel = False

        self.message_handler = messages.HandleMessage(self)
        self.replies_handler = replies.HandleReplies(self)

    def connect(self):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((self.server, self.port))
            print("Connected to server....\r\n")
            self.register_user()
            print("Registered to server....\r\n")
        except:
            print("Couldn't connect to server....\r\n")
            return False


    def register_user(self):
        try:
            self.message_handler.NICK_message()
            self.message_handler.USER_message()
        except:
            print("Nickname Couldn't be registered.......\r\n")


    def response(self):
        return self.connection.recv(512).decode("utf-8")

    

    # def msg_to_channel(self, channel, massage):
    #     command = "PRIVMSG {}".format(channel)
    #     massage = ":" + massage
    #     self.send(command, massage)        



