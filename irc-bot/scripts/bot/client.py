#!./.env/bin/python3

import os
import re
import socket
import logging
import schedule
import functools
import scripts.bot.events as events
from scripts.db import DB_Session
from scripts.db.models import Message, Server


class Connect_Factory():

    ip_type = socket.AF_INET

    def __init__(self, bind_address=None, ipv6=False):
        self.bind_address = bind_address
        if ipv6:
            self.ip_type = socket.AF_INET6

    def connect(self, address):
        sock = socket.socket(self.ip_type, socket.SOCK_STREAM)
        self.bind_address and sock.bind(self.bind_address)
        sock.connect(address)

        return sock


class IRC_Client:
    '''This is the main connection that is connected to the server...
       This parses the data, handles server messages and stores the data...
    '''

    main_log = logging.getLogger("mainlogger")
    msg_log = logging.getLogger("messagelogger")

    def __init__(self):
        # self.session = self.db_session()
        self.replies_buffer = ""

        self.reconnect_tries = 1
        self.max_reconnect_tries = 5

        self.joined_channels = []
        self.real_server = None
        self.connected = False
        self.user_registered = False

        self.socket = None
        self.connect_factory = Connect_Factory()

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
        '''This function is used to connect to the server...
            This configures the first connection...
        '''
        self.server = server
        self.port = port
        self.address = (server, port)
        self.channels = channels

        self.nick = nick or os.environ.get('NICK_NAME') or 'defaltee'
        self.user = user or os.environ.get('USER_NAME') or 'user_default'
        self.real = real or os.environ.get('REAL_NAME') or 'real default'

        self.password = password
        self.ssl = ssl

        # Schedule all the jobs...
        self.schedule_jobs()

        # Create the sock connection..
        try:
            self.socket = self.connect_factory.connect(self.address)
            self.main_log.info(
                "Connected to (server=%s) on (port=%d)", self.server, self.port)

        except socket.error:
            self.main_log.critical(
                "Couldn't connect to (server=%s) (port=%d)", self.server, self.port)
            self.socket = None
            return 0

        self.connected = True
        self.register_user()
        return 1

    def reconnect(self):
        # Tries to reconnect to the server...
        # 
        try:
            self.socket = self.connect_factory.connect(self.address)
            self.main_log.info(
                "Reconnected to (server=%s) on (port=%d)", self.server, self.port)
        except socket.error:
            self.main_log.critical("Connection failed (time=%d) to (server=%s) (port=%d)",
                                   self.reconnect_tries, self.server, self.port)
            self.reconnect_tries += 1
            return 0

        self.connected = True
        self.register_user()

    def disconnect(self):
        # Disconnects from the server...
        # 
        self.main_log.info(
                "Disconnecting from server %s on port %d", self.server, self.port)

        try:
            if self.connected: 
                self.LEAVE_all_channels()
                self.KILL_message("Leaving now.")

            self.socket.close()
            self.cancel_jobs()

            self.socket = None
            self.connected = False
        except:
            self.socket = None
            self.connected = False

    def register_user(self):
        # Registers the user...
        # 
        self.main_log.info(
            'Registering user as (nick=%s) (user=%s)', self.nick, self.user)
        self.NICK_message(self.nick)
        self.USER_message(self.user, self.real)

    def schedule_jobs(self):
        # Starts all the jobs that run in background.
        # These monitors the client and handles errors....
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
        


    def check_channel_joins(self):
        # Check if all the channels are connected...
        #
        if self.connected and len(self.channels) != len(self.joined_channels) :
            join = set(self.channels) - set(self.joined_channels)
            leave = set(self.joined_channels) - set(self.channels)


            if join:
                self.JOIN_message(list(join))
            if leave:
                self.PART_message(list(leave))

            print(self.channels)
            print(self.joined_channels)

    def ping_ponger(self):
        # Pings the server in the background...
        #
        if self.connected and self.real_server:
            self.PONG_message(self.real_server)

    def log_status(self):
        # Logs the clients current ststus...
        #
        self.main_log.debug('Status of [ server=%s ] on [ port=%s ] [ real_adress=%s ] is [ connected=%r ] and [ registed=%r ]:  [ nick=%s ] [ user=%s ] [ real=%s ]',
                            self.server, self.port, self.real_server, self.connected, self.user_registered,  self.nick, self.user, self.real)

    def response(self):
        # Receives the response and decodes it...
        #
        try:
            return self.socket.recv(512).decode("utf-8")
        except:
            return None

    def run_once(self):
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

        # Runs the jobs...
        schedule.run_pending()

    def extract_pvtmsg_parts(self, msg):
        # This extracts the valid pvt message and returns them...
        #
        try:
            sender = re.match(r'^(:[^ ]+)', msg).group(0)
            serial = re.search(r'(#[\d]+)', msg).group(0)
            size = re.search(r'(\[[ .0-9]+[M|G]\])',
                             msg).group(0).replace(' ', '')
            file_name = re.search(r'([^ ]+)$', msg).group(0)
            channel = re.search(r'(#[a-zA-Z]+)', msg).group(0)

            return (sender, serial, size, file_name, channel)
        except AttributeError:
            return (None, None, None, None, None)


    def store_pvt_message(self, res):
        # Stores the msg in the db...
        #
        sender, serial, size, file_name, channel = self.extract_pvtmsg_parts(
            res)

        if not sender:
            return

        new_message = Message(
            sender=sender, serial=serial, size=size, name=file_name)

        with DB_Session() as session:
            server = session.query(Server).\
                filter(Server.server == self.server).\
                filter(Server.channel == channel).\
                first()

            if server:
                new_message.server = server
            else:
                server = Server(server=self.server, channel=channel)
                new_message.server = server

            session.add(new_message)

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

        if command == "privmsg":
            self.store_pvt_message(response)
            return

        self.msg_log.info(response)

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
        self.main_log.info("logged as (nick= % s) (real= % s) on (server=%s)",
                           self.nick, self.real, self.server)
        
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
        return string.encode('utf-8') + b'\r\n'

    def send_msg(self, string):
        '''Sends a string to the server...
        '''
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
