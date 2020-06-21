import re
import time
import socket
import logging
import scripts.bot.events as events
from scripts.bot.exceptions import ConnectionFailure, NoSuchNick
from scripts.bot.utilities import Buffer, Event, Source, Argument

class IRC_Client:
    runloop = True
    display_message = ''
    replies_buffer = Buffer()

    logger = logging.getLogger("mainlogger")
    messages = logging.getLogger("messagelogger")

    irc_rfc_regexp = "^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?""(?P<command>[^ ]+)( *(?P<argument> .+))?"

    def __init__(self, server_connection, user, channels=[]):
        # Client info
        self.user = user
        self.nickname = user.nick
        self.username = user.user
        self.realname = user.real
        self.channels = set(channels)

        # Server
        self.server_connection = server_connection

        #  Connection status
        self.joined_channels = set([])
        self.real_server = None
        self.connected = False

        self.handlers = {}
        self.add_event_handler('ping', self.on_ping)
        self.add_event_handler('part', self.on_part)
        self.add_event_handler('nosuchnick', self.on_nosuchnick)
        self.add_event_handler('nicknameinuse', self.on_nicknameinuse)


    def register_user(self):
        self.logger.info(
                "Registering user as (nick=%s) (user=%s)", 
                            self.nickname, 
                            self.username)

        self.nick_msg(self.nickname)
        self.user_msg(self.username, self.realname)


    def add_channels(self, channels):
        self.join(channels)
        self.channels.update(channels)

    def leave_channels(self, channels):
        self.part(channels)
        self.channels.difference_update(channels)


    def recv_data(self):
        res_data = self.server_connection.recv()
        if res_data:
            self.replies_buffer.feed(res_data)
            for reply in self.replies_buffer:
                self.process_replies(reply)
        

    def process_replies(self, response):
        # This processes each reply and handles the counter message...
        self.messages.info(response)
        match = self.match_pattern(self.irc_rfc_regexp, response)
        
        if not match:
            return

        command = match('command')
        prefix = Source(match('prefix'))
        argument = Argument(match('argument'))
        command = events.numeric.get(command, command).lower()

        # stores the real server name...
        if prefix and not self.real_server:
            self.real_server = prefix.sender
            
        event = Event(command, prefix, argument)
        self._handle_event(event)
        

    def on_part(self, event):
        if event.source.sender == self.nickname:
            channels = event.argument.channel
            self.channels.difference_update(channels)
            self.joined_channels.difference_update(channels)
        
    
    def on_ping(self, event):
        target = event.argument.message
        self.pong(target)

    
    def on_nicknameinuse(self, _):
        self.nickname = self.user.new_nick()
        self.nick_msg(self.nickname)

    
    def on_nosuchnick(self, _):
        raise NoSuchNick()

    
    def on_notice(self, event):
        self.logger.debug("Notice from %s :: %s", event.source.sender, event.argument.message)
        

    def send_msg(self, string):
        # Sends a string to the server...
        try:
            msg = string + '\r\n'
            self.server_connection.send(msg)
            self.logger.info('Server message: %s', string)   
        except socket.error:
            self.logger.debug("Server message failed ::%s", string)

    def pass_msg(self, password):
        msg = "PASS {}".format(password)
        self.send_msg(msg)

    def nick_msg(self, nick_name):
        msg = "NICK {}".format(nick_name)
        self.send_msg(msg)

    def user_msg(self, user_name, real_name):
        msg = "USER {} * * :{}".format(user_name, real_name)
        self.send_msg(msg)

    def quit_msg(self, message):
        msg = "QUIT :{}".format(message)
        self.send_msg(msg)

    def join(self, channels):
        if isinstance(channels, str):
            channels = [channels]

        channels = ','.join(filter(None, channels))
        msg = "JOIN {}".format(channels)
        self.send_msg(msg)

    def part(self, channels):
        if isinstance(channels, str):
            channels = [channels]

        channels = ','.join(filter(None, channels))
        msg = "PART {}".format(channels)
        self.send_msg(msg)

    def whois(self, nick):
        msg = "WHOIS {}".format(nick)
        self.send_msg(msg)

    def pong(self, target):
        msg = "PONG :{}".format(target)
        self.send_msg(msg)

    def prvt(self, target, message):
        msg = "PRIVMSG {} :{}".format(target, message)
        self.send_msg(msg)
    
    def ctcp(self, target, message):
        msg = "PRIVMSG {} :\001{}\001".format(target, message)
        self.send_msg(msg)

    def leave_all_channels(self):
        msg = "JOIN 0"
        self.send_msg(msg)

    def leave_irc_server(self):
        self.leave_all_channels()
        self.quit_msg("Leaving now.")


    def add_event_handler(self, event, fn):
        handlers = self.handlers.get(event, None)
        if handlers is None:
            self.handlers[event] = []
        
        self.handlers[event].append(fn)


    def remove_event_handler(self, event, fn):
        try:
            self.handlers[event].remove(fn)
        except KeyError:
            pass


    def _handle_event(self, event):
        handlers = self.handlers.get(event.type, None)
        if handlers:
            for fn in handlers:
                fn(event)


    def match_pattern(self, pattern, string):
        try:
            regexp = re.compile(pattern)
            match = regexp.search(string).group
            return match
        except AttributeError:
            self.logger.debug("Pattern match failed for ::%s %s", pattern, string)
            return None