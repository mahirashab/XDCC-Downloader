#!/usr/bin/python3
import socket
import select
import scripts.messages as messages
import scripts.replies as replies


class IRC_Client:

    def __init__(self, server="irc.freenode.net", port=6667, nick_name="scker", user="mahir", realname="mahir ashab"):
        self.server = server
        self.real_server = None
        self.port = port
        self.nick_name = nick_name
        self.user = user
        self.real_name = realname

        self.user_registered = False
        self.joined_channel = False

        self.message_queue = []
        self.replies_buffer = ""

        self.message_handler = messages.HandleMessage(self)
        self.replies_handler = replies.HandleReplies(self)

    def connect(self):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((self.server, self.port))
            self.message_queue.append("SENT_CONNECTION")
            # self.connection.setblocking(False)
        except:
            print("Couldn't connect to server....\r\n")
            return False


    def register_user(self):
        try:
            self.message_handler.NICK_message()
            self.message_handler.USER_message()
            self.message_queue.append("SENT_REGISTER")
        except:
            print("Nickname Couldn't be registered.......\r\n")

    
    def run_once(self, timeout=1):
        readable, writeable, error = select.select([self.connection], [], [self.connection], timeout)

        if readable:
            res_data = self.response()
            if res_data:
                splitted_message = res_data.split("\r\n")
                splitted_message[0] = self.replies_buffer + splitted_message[0]
                self.replies_buffer = splitted_message[-1]

                for reply in splitted_message[:-1]:
                    if reply:
                        self.replies_handler.process_replies(reply)
        elif error:
            pass


    def response(self):
        return self.connection.recv(512).decode("utf-8")



