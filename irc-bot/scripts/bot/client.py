
import re
import socket
import logging
import schedule
import functools
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
        sock.settimeout(5)
        sock.connect(address)
        sock.settimeout(None)

        return sock


class IRC_Client:
    '''This is the main connection that is connected to the server...
       This parses the data, handles server messages and stores the data...
    '''

    main_log = logging.getLogger("mainlogger")
    msg_log = logging.getLogger("messagelogger")

    def __init__(self):
        self.replies_buffer = ""

        self.reconnect_tries = 1
        self.max_reconnect_tries = 5

        self.joined_channels = []
        self.real_server = None
        self.connected = False
        self.user_registered = False

        self.socket = None
        self.connect_factory = Connect_Factory()
        self.schedule_jobs()

    def connect(
            self,
            server,
            channels,
            port=6667,
            nick=None,
            user=None,
            real=None,
            password=None,
            ssl=None):
        
        self.server = server
        self.port = port
        self.address = (server, port)
        self.channels = channels

        self.nick = nick or 'defaltee'
        self.user = user or 'user_defa'
        self.real = real or 'defaulteen'

        self.password = password
        self.ssl = ssl

        try:
            self.socket = self.connect_factory.connect(self.address)
            self.main_log.info(
                    "Connected to (server=%s) on (port=%d)", 
                                self.server, 
                                self.port)

        except socket.error:
            self.main_log.critical(
                    "Couldn't connect to (server=%s) (port=%d)", 
                                self.server, 
                                self.port)

            self.socket = None
            return None

        self.connected = True
        if self.password:
            self.PASS_message(self.password)

        self.register_user()



    def reconnect(self):
        # Tries to reconnect to the server...
        #
        try:
            self.socket = self.connect_factory.connect(self.address)
            self.main_log.info(
                    "Reconnected to (server=%s) on (port=%d)", 
                                self.server, 
                                self.port)
                                
        except socket.error:
            self.main_log.critical(
                    "Connection failed (time=%d) to (server=%s) (port=%d)",
                                self.reconnect_tries, 
                                self.server, 
                                self.port)

            self.reconnect_tries += 1
            return 0

        self.connected = True
        self.register_user()


    def disconnect(self):
        # Disconnects from the server...
        #
        self.main_log.info("Removing server %s on port %d", 
                            self.server, 
                            self.port)

        try:
            if self.connected:
                self.LEAVE_all_channels()
                self.KILL_message("Leaving now.")
            self.socket.close()

        except:
            self.socket = None
            self.connected = False

        finally:
            self.cancel_jobs()
            self.socket = None
            self.connected = False


    def register_user(self):
        # Registers the user...
        #
        self.main_log.info(
                "Registering user as (nick=%s) (user=%s)", 
                            self.nick, 
                            self.user)

        self.NICK_message(self.nick)
        self.USER_message(self.user, self.real)
        

    def schedule_jobs(self):
        # Starts all the jobs that run in background.
        # 
        self.jobs = [
            schedule.every(15).seconds.do(self.check_channel_joins),
            schedule.every(100).seconds.do(self.ping_ponger),
            schedule.every(10).minutes.do(self.log_status)
        ]


    def cancel_jobs(self):
        # Remove all the jobs for this client...
        #
        if self.jobs:
            [schedule.cancel_job(job) for job in self.jobs]


    def message(self):
        with open('message.txt', 'r') as file: 
            for line in file.readlines():
                self.send_msg(line)

    def check_channel_joins(self):
        # Check to join and leave channels...
        #
        if self.connected and len(self.channels) != len(self.joined_channels):
            join = set(self.channels) - set(self.joined_channels)
            leave = set(self.joined_channels) - set(self.channels)

            if join:
                self.JOIN_message(list(join))
            if leave:
                self.PART_message(list(leave))


    def ping_ponger(self):
        # Pings the server in the background...
        #
        if self.connected and self.real_server:
            self.PONG_message(self.real_server)


    def log_status(self):
        # Logs the clients current ststus...
        #
        self.main_log.debug(
                "Status of [ server=%s ] on [ port=%s ] \
                as [ real_adress=%s ] \
                is now [ connected=%r ] and [ registed=%r ] as: \
                [ nick=%s ] [ user=%s ] [ real=%s ]",
                            self.server, self.port, self.real_server, 
                            self.connected, self.user_registered,  
                            self.nick, self.user, self.real)


    def response(self):
        # Receives the response and decodes it...
        #
        try:
            return self.socket.recv(512).decode("utf-8")
        except:
            return None


    def recv_data(self):
        # Receives response and processess them...
        #
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
        #
        regexp = re.compile("^(@(?P<tags>[^ ]*) )?(:(?P<prefix>[^ ]+) +)?"
                            "(?P<command>[^ ]+)( *(?P<argument> .+))?")

        m = regexp.match(response).group

        tags = m('tags')
        prefix = m('prefix')
        command = m('command')
        argument = m('argument')

        command = events.numeric.get(command, command).lower()

        # stores the real server name...
        if prefix and not self.real_server:
            self.real_server = prefix


        self.msg_log.info(response)


        if command == "privmsg":
            return

        if command == "welcome":
            self.welcome_reply_handler()

        elif command == 'join':
            self.join_reply_handler(prefix, argument)

        elif command == "nicknameinuse":
            if self.connected:
                self.nick += "a"
                self.register_user()
            else:
                self.reconnect()
                self.register_user()

        elif command == 'ping':
            self.PONG_message(self.real_server)

        elif command == "error":
            if "closing link" in argument.lower():
                self.connected = False
                self.socket.close()

    def welcome_reply_handler(self):
        # Handles welcome message from server...
        #
        self.main_log.info(
                "logged as (nick= % s) (real= % s) on (server=%s)",
                           self.nick, 
                           self.real, 
                           self.server)

        self.user_registered = True
        self.JOIN_message(self.channels)


    def join_reply_handler(self, prefix, argument):
        # Handles the join message from server...
        #
        receiver = prefix.split('@')[0]
        myself = self.nick + '!' + self.user

        if myself == receiver:
            channel_name = argument.replace(':', '').replace(' ', '').lower()
            self.joined_channels.append(channel_name)
            self.joined_channels = list(set(self.joined_channels))

    '''The below functions are used to send different messages to the server...
       Used RFC for reference...
    '''

    def prepare_msg(self, string):
        # Encodes a string and returns it...
        # 
        return string.encode('utf-8') + b'\r\n'


    def send_msg(self, string):
        # Sends a string to the server...
        #
        if not self.connected:
            self.main_log.debug(
                    "Server not connected.Couldn't send Message :: %s", string)
            return

        try:
            msg_bytes = self.prepare_msg(string)
            self.socket.send(msg_bytes)
            self.main_log.info('Server message: %s', string)
        except socket.error:
            self.main_log.debug('Failed to send message.')


    def PASS_message(self, password):
        msg = "PASS {}".format(password)
        self.send_msg(msg)

    # 3.1.2 Nick message
    def NICK_message(self, nick_name):
        msg = "NICK {}".format(nick_name)
        self.send_msg(msg)

    # 3.1.3 User message
    def USER_message(self, user_name, real_name):
        msg = "USER {} * * :{}".format(user_name, real_name)
        self.send_msg(msg)

    # 3.1.5 User mode message
    def MODE_message(self, nickname, mode, activate=True):
        if not self.user_registered:
            raise Exception("User not registered...")
        if mode not in 'iwo0r':
            raise Exception('Invalid Mode.')

        if activate:
            msg = "MODE {} +{}".format(nickname, mode)
        else:
            msg = "MODE {} -{}".format(nickname, mode)

        self.socket.send(msg)

    # 3.1.7 Quit
    def QUIT_message(self, message):
        msg = "QUIT :{}".format(message)
        self.socket.send(msg)

    # 3.2.1 Join message
    def JOIN_message(self, channels, keys=[]):
        channels = ','.join(filter(None, channels))
        keys = ','.join(filter(None, keys))

        msg = "JOIN {} {}".format(channels, keys)
        self.send_msg(msg)

    def PART_message(self, channels):
        self.joined_channels = list(
            set(self.joined_channels) - set(channels))
        channels = ','.join(filter(None, channels))

        msg = f"PART {channels}"
        self.send_msg(msg)

    def LEAVE_all_channels(self):
        msg = "JOIN 0"
        self.send_msg(msg)

    def KILL_message(self, message):
        msg = f"KILL {self.nick} {message}"
        self.send_msg(msg)

    def PONG_message(self, server):
        msg = "PONG :{}".format(server)
        self.send_msg(msg)
