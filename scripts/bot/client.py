
import re
import time
import socket
import logging
import scripts.bot.events as events

class Connect_Factory():
    ip_type = socket.AF_INET

    def __init__(self, bind_address=None, ipv6=False):
        self.bind_address = bind_address
        if ipv6:
            self.ip_type = socket.AF_INET6

    def connect(self, address):
        sock = socket.socket(self.ip_type, socket.SOCK_STREAM)
        self.bind_address and sock.bind(self.bind_address)
        sock.settimeout(3)
        sock.connect(address)

        return sock
    
    __call__ = connect


class Source(str): 
            
    @property
    def sender(self):
        return self.split('!')[0]
    
    def __repr__(self):
        return "< Source sender:%s >" % (self.sender)

    def __str__(self):
        return "< Source sender:%s >" % (self.sender)


class Argument(str):

    @property
    def data(self):
        if isinstance(self, bytes):
            return self
        else:
            None
    
    @property
    def receiver(self):
        temp = self.split(':')[0].split(' ')
        temp = filter(lambda x: x, temp)
        return list(temp)[0]
        
    
    @property
    def message(self):
        return self.split(':')[1]
    
    @property
    def channels(self):
        channels = re.findall(r'(?P<channel>#[^ ]+)', self)
        return [channel.lower() for channel in channels]
    
    def __repr__(self):
        return "< Argument receiver:%s channels:%s message:%s>" % (self.receiver, self.channels, self.message)

    def __str__(self):
        return "< Argument receiver:%s channels:%s message:%s>" % (self.receiver, self.channels, self.message)

class Event:
    
    def __init__(self, type, source, argument):
        self.type = type
        self.source = source
        self.argument = argument



class IRC_Client:

    logger = logging.getLogger("mainlogger")
    messages = logging.getLogger("messagelogger")

    def __init__(self):
        # Temp 
        self.replies_buffer = ""

        self.max_reconn_tries = 3
        self.reconn_tries = 0

        # Client info
        self.nickname = None
        self.username = None
        self.realname = None
        self.channels = set([])

        # Server info
        self.server = None
        self.port = None

        #  Connection status
        self.joined_channels = set([])
        self.real_server = None
        self.connected = False

        #  Connection socket.
        self.socket = None

        self.handlers = {}
        
        self.add_event_handler('ping', self.on_ping)
        self.add_event_handler('part', self.on_part)
        

        self.connect_factory = Connect_Factory()

    def disconnect(self):
        # Disconnects from the server...
        self.logger.info("Removing server %s on port %d", 
                            self.server, 
                            self.port)
        try:
            if self.connected:
                self.leave_all_channels()
                self.quit_msg("Leaving now.")
            self.socket.close()
        except:
            self.socket = None
            self.connected = False
        finally:
            self.socket = None
            self.connected = False


    def register_user(self):
        # Registers the user...
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


    def read_data(self):
        # Receives the response and decodes it...
        try:
            return self.socket.recv(512).decode("utf-8")
        except:
            return None


    def recv_data(self):
        # Receives response and processess them...
        res_data = self.read_data()
        if res_data:
            splitted_message = res_data.split("\r\n")
            splitted_message[0] = self.replies_buffer + splitted_message[0]
            self.replies_buffer = splitted_message[-1]

            for reply in splitted_message[:-1]:
                if reply:
                    self.process_replies(reply)
        


    def process_replies(self, response):
        # This processes each reply and handles the counter message...
        self.messages.info(response)
        match = self.match_pattern("^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?"
                                    "(?P<command>[^ ]+)( *(?P<argument> .+))?", response)
        
        if not match: return

        command = match('command')
        prefix = Source(match('prefix'))
        argument = Argument(match('argument'))

        command = events.numeric.get(command, command).lower()


        # stores the real server name...
        if prefix and not self.real_server:
            self.real_server = match('prefix')
            
        event = Event(command, prefix, argument)
        self._handle_event(event)
        
    
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
        
        

    def on_part(self, event):
        if event.source.sender == self.nickname:
            channels = event.argument.channel
            self.channels.difference_update(channels)
            self.joined_channels.difference_update(channels)
        
    
    def on_ping(self, event):
        target = event.argument.message
        self.pong(target)
        

    def send_msg(self, string):
        # Sends a string to the server...
        try:
            msg_bytes = string.encode('utf-8') + b'\r\n'
            self.socket.send(msg_bytes)
            self.logger.info('Server message: %s', string)
        except socket.error:
            self.logger.debug('Socket error. Message failed :: %s', string)
        

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
        self.socket.send(msg)


    def join(self, channels):
        if isinstance(channels, str):
            channels = [channels]

        channels = ','.join(filter(None, channels))
        msg = "JOIN {}".format(channels)
        self.send_msg(msg)


    def part(self, channels):
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


    def match_pattern(self, pattern, string):
        try:
            regexp = re.compile(pattern)
            match = regexp.search(string).group
            return match
        except AttributeError:
            self.logger.debug("Pattern match failed for ::%s %s", pattern, string)
            return None