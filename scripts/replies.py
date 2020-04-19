#!/usr/bin/python3
import re
import scripts.events as events

class HandleReplies:

    def __init__(self, irc_client):
        self.client = irc_client
        self.regexp = re.compile("^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?"
                            "(?P<command>[^ ]+)( *(?P<argument> .+))?")
        
    def process_replies(self, response):

        m = self.regexp.match(response)
        tags = self.get_tags(m)
        prefix = self.get_prefix(m)
        command = self.get_command(m)
        argument = self.get_argument(m)

        print(command)
        command = events.numeric.get(command, command)
        print(command)

        last_message = self.client.message_queue[0]

        # print(response)
        if command == "welcome":
            self.client.real_server = prefix
            self.client.user_registered = True
            print("Welcome.", command,  response)

        # elif command == "yourhost":
        #     print("yourhost")

        # elif command == "created":
        #     print("displaying created.")
        #     print(response)

        elif command == "nicknameinuse":
            print("nickname in use")

        elif command == "notice":
            self.handle_NOTICE_reply(response, last_message)

        elif command == "ping":
            self.handle_PING_reply(response, last_message)

        else:
            # print(response)
            pass


    def handle_NOTICE_reply(self, response, last_message):
        if last_message == "SENT_CONNECTION" and "No Ident response" in response:
            self.client.register_user()
            del self.client.message_queue[0]

    
    def handle_PING_reply(self, response, last_message):
        if self.client.user_registered:
            self.client.message_handler.PONG_message(self.client.real_server)
        

    
    def get_prefix(self, reg_obj):
        try:
            prefix = reg_obj.group('prefix')
            return prefix
        except AttributeError:
            return None

    def get_command(self, reg_obj):
        try:
            command = reg_obj.group('command')
            return command.lower()
        except AttributeError:
            return None

    def get_argument(self, reg_obj):
        try:
            argument = reg_obj.group('argument')
            return argument
        except AttributeError:
            return None

    def get_tags(self, reg_obj):
        try:
            tags = reg_obj.group('tags')
            return tags
        except AttributeError:
            return None





        