
import re
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
    def channel(self):
        channels = re.findall(r'(?P<channel>#[^ ]+)', self)
        return channels[0] if len(channels) == 1 else channels
    
    def __repr__(self):
        return "< Argument receiver:%s message:%s channel:%s>" % (self.receiver, self.channel, self.message)

    def __str__(self):
        return "< Argument receiver:%s channel:%s message:%s>" % (self.receiver, self.channel, self.message)

class Event:
    
    def __init__(self, type, source, argument):
        self.type = type
        self.source = source
        self.argument = argument



class IRC_Client:

    main_log = logging.getLogger("mainlogger")
    msg_log = logging.getLogger("messagelogger")

    def __init__(self):
        # Temp 
        self.replies_buffer = ""
        self.recon_tries = 1

        # Client info
        self.nickname = None
        self.username = None
        self.realname = None
        self.channels = []

        # Server info
        self.server = None
        self.port = None
        self.address = (self.server, self.port)

        #  Connection status
        self.joined_channels = []
        self.downloads = []
        self.real_server = None
        self.connected = False
        self.user_registered = False

        #  Connection socket.
        self.socket = None
        
        self.handlers = {
            'ping': self.on_ping,
            'welcome': self.on_welcome,
        }

        self.connect_factory = Connect_Factory()



    def reconnect(self):
        # Tries to reconnect to the server...
        try:
            self.socket = self.connect_factory.connect(self.address)
            self.main_log.info(
                    "Reconnected to (server=%s) on (port=%d)", 
                                self.server, 
                                self.port)                        
        except socket.error:
            self.main_log.critical(
                    "Connection failed (time=%d) to (server=%s) (port=%d)",
                                self.recon_tries, 
                                self.server, 
                                self.port)
            
            self.connected = False
            self.socket = None
            self.recon_tries += 1
            return 0

        self.connected = True
        self.register_user()


    def disconnect(self):
        # Disconnects from the server...
        self.main_log.info("Removing server %s on port %d", 
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
        self.main_log.info(
                "Registering user as (nick=%s) (user=%s)", 
                            self.nickname, 
                            self.username)

        self.nick_msg(self.nickname)
        self.user_msg(self.username, self.realname)


    def add_channels(self, channels):
        self.channels += channels
        self.channels = self.remove_duplicates(self.channels)

    def leave_channels(self, channels):
        self.part_msg(channels)
        self.channels = list(set(self.channels) - set(channels))
    
    def response(self):
        # Receives the response and decodes it...
        try:
            return self.socket.recv(512).decode("utf-8")
        except:
            return None


    def recv_data(self):
        # Receives response and processess them...
        res_data = self.response()
        if res_data:
            splitted_message = res_data.split("\r\n")
            splitted_message[0] = self.replies_buffer + splitted_message[0]
            self.replies_buffer = splitted_message[-1]

            for reply in splitted_message[:-1]:
                if reply:
                    self.process_replies(reply)
        


    def process_replies(self, response):
        # This processes each reply and handles the counter message...
        match = self.match_pattern("^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?"
                                    "(?P<command>[^ ]+)( *(?P<argument> .+))?", response)
        
        if not match: return

        command = match('command')
        prefix = Source(match('prefix'))
        argument = Argument(match('argument'))

        command = events.numeric.get(command, command).lower()


        # stores the real server name...
        if prefix and not self.real_server:
            self.real_server = prefix
            
        event = Event(command, prefix, argument)
        self._handle_event(event)
        

    def _handle_event(self, event):
        handler = self.handlers.get(event.type, None)
        if handler:
            handler(event)
        

    def on_welcome(self, event):
        # Handles welcome message from server...
        #
        self.main_log.info(
                "logged as (nick= % s) (real= % s) on (server=%s)",
                           self.nickname, 
                           self.realname, 
                           self.server)

        self.user_registered = True
        self.join_msg(self.channels)
        


    def on_part(self, event):
        if event.source.sender == self.nickname:
            channel = event.argument.channel
            self.channels.remove(channel)
        
    
    def on_ping(self, event):
        target = event.argument.message
        self.pong_msg(target)
        

    def prepare_msg(self, string):
        # Encodes a string and returns it...
        return string.encode('utf-8') + b'\r\n'


    def send_msg(self, string):
        # Sends a string to the server...
        if not self.is_connected():
            self.main_log.debug(
                    "Server not connected.Couldn't send Message :: %s", string)
            return

        try:
            msg_bytes = self.prepare_msg(string)
            self.socket.send(msg_bytes)
            self.main_log.info('Server message: %s', string)
        except socket.error:
            self.main_log.debug('Socket error. Message failed :: %s', string)


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


    def join_msg(self, channels, keys=[]):
        channels = ','.join(filter(None, channels))
        keys = ','.join(filter(None, keys))

        msg = "JOIN {} {}".format(channels, keys)
        self.send_msg(msg)


    def part_msg(self, channels):
        self.joined_channels = list(
            set(self.joined_channels) - set(channels))
        channels = ','.join(filter(None, channels))

        msg = "PART {}".format(channels)
        self.send_msg(msg)


    def leave_all_channels(self):
        msg = "JOIN 0"
        self.send_msg(msg)


    def whois(self, nick):
        msg = "WHOIS {}".format(nick)
        self.send_msg(msg)


    def pong_msg(self, target):
        msg = "PONG :{}".format(target)
        self.send_msg(msg)


    def match_pattern(self, pattern, string):
        try:
            regexp = re.compile(pattern)
            match = regexp.search(string).group
            return match
        except AttributeError:
            self.main_log.debug("Pattern match failed for ::%s", string)
            return None


    def is_connected(self):
        # Return true if socket is connected...
        return self.connected


    def remove_duplicates(self, l):
        return list(set(l))