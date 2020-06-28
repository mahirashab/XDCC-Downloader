import re
import time
import socket
import logging
import scripts.bot.events as events

from scripts.bot.user import User
from typing import Optional, Any, List, Union, Callable 
from scripts.bot.server_connection import ServerConnection
from scripts.bot.exceptions import ConnectionFailure, NoSuchNick
from scripts.bot.utilities import Buffer, Event, Source, Argument

class IRC_Client:
    replies_buffer = Buffer()
    logger = logging.getLogger("mainlogger")
    message_log = logging.getLogger("messagelogger")

    irc_rfc_regexp = "^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?""(?P<command>[^ ]+)( *(?P<argument> .+))?"


    def __init__(self, 
                server_connection: ServerConnection, 
                user: User, 
                channels: Optional[list] =['#mg-chat']):
        '''
        Initiates the base class for XDCC_Downloader.
        It serves the basic irc server connunication functionalities.

        :param server_connection: Handles socket connection to server.
        :param user: Represents basic user info.
        :param channels: List of channels to be joined.
        '''

        # Client info
        self.user = user
        self.nickname = user.nick
        self.username = user.user
        self.realname = user.real

        # Server connection
        self.server_connection = server_connection

        #  Connection status
        self.joined_channels = set([])
        self.real_server = None
        self.connected = False

        # other
        self.runloop = True
        self.channels = set([c.lower() for c in channels])

        # Handlers
        self.handlers = {}
        self.add_event_handler('ping', self.on_ping)
        self.add_event_handler('part', self.on_part)
        self.add_event_handler('nosuchnick', self.on_nosuchnick)
        self.add_event_handler('nicknameinuse', self.on_nicknameinuse)


    def register_user(self):
        '''
        Registers the user when connected to server.
        :return: None
        '''
        self.logger.info(
                "Registering user as (nick=%s) (user=%s)", 
                            self.nickname, 
                            self.username)

        self.nick_msg(self.nickname)
        self.user_msg(self.username, self.realname)


    def add_channels(self, channels: list):
        '''
        Joins the received channels and
        adds them to the self.channels.
        :param channels: List of channels to be joined.
        :return: None.
        '''
        self.join(channels)
        self.channels.update(channels)


    def leave_channels(self, channels: list):
        '''
        Leaves the received channels and
        removes them from the self.channels
        :param channels: List of channels to be left.
        :return: None.
        '''
        self.part(channels)
        self.channels.difference_update(channels)


    def recv_data(self):
        '''
        Receives irc server replies and 
        processes each complete reply.
        :return: None
        '''
        res_data = self.server_connection.recv()
        if res_data:
            self.replies_buffer.feed(res_data)
            for reply in self.replies_buffer:
                self.process_replies(reply)
        

    def process_replies(self, response: str):
        '''
        Processes sicgle server reply using event handlers.
        :param response: Single reply message from server.
        :return: None
        '''
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
        # self.messages.info(response)
        

    def on_part(self, event: Event):
        '''
        Handles the part event.
        Updates the channels list when a channel is left.
        :param event: the received event.
        :return: None
        '''
        if event.source.sender == self.nickname:
            channels = event.argument.channel
            self.channels.difference_update(channels)
            self.joined_channels.difference_update(channels)
        
    
    def on_ping(self, event: Event):
        '''
        Handles the ping event.
        Pings the server.
        :param event: the received event.
        :return: None
        '''
        target = event.argument.message
        self.pong(target)

    
    def on_nicknameinuse(self, _: Event):
        '''
        Handles nicknameinuse event.
        Sends nick message with new randomly generated nickname.
        :param event: the received event.
        :return: None
        '''
        self.nickname = self.user.new_nick()
        self.nick_msg(self.nickname)

    
    def on_nosuchnick(self, _: Event):
        '''
        Handles nosuchnick event.
        Occures when a nickname dosen't exist.
        :param event: the received event.
        :return: None
        '''
        raise NoSuchNick()

    
    def on_notice(self, event: Event):
        '''
        Handles notice event.
        Occures when a notice message is received.
        :param event: the received event.
        :return: None
        '''
        self.logger.debug(
                "Notice from %s :: %s", 
                            event.source.sender,
                            event.argument.message)


    def add_event_handler(self, 
                        event_name: str, 
                        fn: Callable[[Event], Any]):
        '''
        Adds new handler for the passed event.
        :param event: String representing event.
        :param fn: Handler function for that event.
        :return: None
        '''
        handlers = self.handlers.get(event_name, None)
        if handlers is None:
            self.handlers[event_name] = []
        
        self.handlers[event_name].append(fn)


    def remove_event_handler(self, 
                            event_name: str, 
                            fn: Callable[[Event], Any]):
        '''
        Removes passed handler for event.
        :param event: String representing event.
        :param fn: Handler function for that event.
        :return: None
        '''
        try:
            self.handlers[event_name].remove(fn)
        except KeyError:
            pass


    def _handle_event(self, event: Event):
        '''
        Handles a sicgle event.
        :param event: The received event.
        :return: None
        '''
        handlers = self.handlers.get(event.type, None)
        if handlers:
            for fn in handlers:
                fn(event)
        

    def send_msg(self, string: str):
        '''
        Sends a message to the server.
        :param string: The passed message.
        :return: None
        '''
        try:
            msg = string + '\r\n'
            self.server_connection.send(msg)
            self.logger.info(
                    "Server message: %s", string)   
        except socket.error:
            self.logger.debug(
                    "Server message failed ::%s", string)




    def pass_msg(self, password: str):
        msg = "PASS {}".format(password)
        self.send_msg(msg)

    def nick_msg(self, nick_name: str):
        msg = "NICK {}".format(nick_name)
        self.send_msg(msg)

    def user_msg(self, user_name: str, real_name: str):
        msg = "USER {} * * :{}".format(user_name, real_name)
        self.send_msg(msg)

    def quit_msg(self, message: str):
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

    def whois(self, nick: str):
        msg = "WHOIS {}".format(nick)
        self.send_msg(msg)

    def pong(self, target: str):
        msg = "PONG :{}".format(target)
        self.send_msg(msg)

    def prvt(self, target: str, message: str):
        msg = "PRIVMSG {} :{}".format(target, message)
        self.send_msg(msg)
    
    def ctcp(self, target: str, message: str):
        msg = "PRIVMSG {} :\001{}\001".format(target, message)
        self.send_msg(msg)

    def leave_all_channels(self):
        msg = "JOIN 0"
        self.send_msg(msg)

    def leave_irc_server(self):
        self.leave_all_channels()
        self.quit_msg("Leaving now.")



    def match_pattern(self, pattern: str, string: str):
        try:
            regexp = re.compile(pattern)
            match = regexp.search(string).group
            return match
        except AttributeError:
            self.logger.debug("Pattern match failed for ::%s %s", pattern, string)
            return None