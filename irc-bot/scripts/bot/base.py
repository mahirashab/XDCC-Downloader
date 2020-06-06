
import re
import socket
import logging
import schedule
import functools
from cmd2.ansi import style
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


class BaseClient:

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
        self.real_server = None
        self.connected = False
        self.user_registered = False

        #  Connection socket.
        self.socket = None

        self.connect_factory = Connect_Factory()
        self.schedule_jobs()



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
                self.LEAVE_all_channels()
                self.quit_msg("Leaving now.")
            self.socket.close()
        except:
            self.socket = None
            self.connected = False
        finally:
            self.remove_jobs()
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
        

    def schedule_jobs(self):
        # Starts all the jobs that run in background.
        self.jobs = [
            schedule.every(15).seconds.do(self.check_channel_joins),
            schedule.every(100).seconds.do(self.ping_ponger)
        ]


    def remove_jobs(self):
        # Remove all the jobs for this client...
        if self.jobs:
            [schedule.cancel_job(job) for job in self.jobs]
            self.jobs = None


    def check_channel_joins(self):
        # Check to join and leave channels...
        if self.is_connected():
            join = set(self.channels) - set(self.joined_channels)
            leave = set(self.joined_channels) - set(self.channels)

            if join:
                self.join_msg(list(join))
            if leave:
                self.part_msg(list(leave))


    def ping_ponger(self):
        # Pings the server in the background...
        if self.connected and self.real_server:
            self.pong_msg(self.real_server)


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
        try:
            regexp = re.compile("^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?"
                                "(?P<command>[^ ]+)( *(?P<argument> .+))?")
            match = regexp.match(response).group
        except:
            return

        prefix = match('prefix')
        command = match('command')
        argument = match('argument')

        command = events.numeric.get(command, command).lower()

        # stores the real server name...
        if prefix and not self.real_server:
            self.real_server = prefix


        if command == "privmsg":
            self.prvt_handler(prefix, argument)
            return
        
        self.msg_log.info(response)

        if command == "welcome":
            self.welcome_handler()

        elif command == 'endofnames':
            channel = re.search(r'(?P<channel>#[^ ]+)', argument).group('channel')
            self.join_handler(channel)


        elif command == 'ping':
            cookie = re.search(r'( :(?P<cookie>.*))', argument).group('cookie')
            self.pong_msg(cookie)
        

        elif command == "nicknameinuse":
            if self.connected:
                self.nickname += "a"
                self.register_user()
            else:
                self.reconnect()
                self.register_user()



    def prvt_handler(self, prefix, argument):
        # This will be replaced by the child
        pass
        
            

    def welcome_handler(self):
        # Handles welcome message from server...
        #
        self.main_log.info(
                "logged as (nick= % s) (real= % s) on (server=%s)",
                           self.nickname, 
                           self.realname, 
                           self.server)

        self.user_registered = True
        self.join_msg(self.channels)


    def join_handler(self, channel):
        # Handles the join message from server...
        self.joined_channels.append(channel.lower())
        self.joined_channels = list(set(self.joined_channels))


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


    def LEAVE_all_channels(self):
        msg = "JOIN 0"
        self.send_msg(msg)


    def pong_msg(self, message):
        msg = "PONG :{}".format(message)
        self.send_msg(msg)



    def is_channel(self, target):
        # Return true if the target is a channel...
        return target.startswith('#')

    def is_connected(self):
        # Return true if socket is connected...
        return self.connected
