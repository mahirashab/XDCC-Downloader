#!/usr/bin/python3
import re
import events

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

        command = events.numeric.get(command, command)

        if command == 'notice':
            print(argument, '\r\n')
        elif command == 'nicknameinuse':
            self.client.nick_name = "qweqweew"
            self.client.register_user()
        
        print(command)


    
    def get_prefix(self, reg_obj):
        try:
            prefix = reg_obj.group('prefix')
            return prefix
        except AttributeError:
            return None

    def get_command(self, reg_obj):
        try:
            command = reg_obj.group('command')
            return command
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





        