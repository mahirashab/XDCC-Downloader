import time
import socket

from ..bot.exceptions import ConnectionFailure

class ServerConnection:
    ip_type = socket.AF_INET

    sock = None
    max_retries = 2
    current_retries = 1

    def __init__(self, server: str, 
                CODEC: str, BUFFER_SIZE: int, 
                port: int=6667, 
                reversed_conn: bool=False, 
                ipv6: bool=False):
        '''
        Initializes a ServerConnection instance.
        Handles TCP socket connections for irc and xdcc communication.
        :param server: Server address or IP.
        :param CODEC: Unicode format the data is tranfered.
        :param BUFFER_SIZE: Receive bytes for each receive.
        :param port: The port for tcp communication.
        :param reversed_conn: If true instance acts as a server else client.
        :param ipv6: If true uses IPV6
        '''
        if ipv6:
            self.ip_type = socket.AF_INET6

        self.CODEC = CODEC
        self.BUFFER_SIZE = BUFFER_SIZE
        self.REVERSED_CONN = reversed_conn
        
        self.server = str(server)
        self.port = int(port)
        self.addr = (self.server, self.port)


    def create_pipe(self, timeout=3):
        '''Creates a connection pipe as a server or client.'''
        if self.REVERSED_CONN:
            self.as_server()
        else:
            self.as_client(timeout=timeout)
        

    def as_client(self, timeout=3):
        '''Connects to a server.'''
        try:
            self.sock = socket.socket(self.ip_type, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect(self.addr)
            self.sock.setblocking(False)
        except socket.error:
            self.sock = None
            if self.current_retries >= self.max_retries:
                raise ConnectionFailure()

            time.sleep(2)
            self.current_retries += 1
            self.as_client()

    
    def as_server(self):
        '''Creates a server and takes only one client.'''
        try:
            self.server_sock = socket.socket(self.ip_type, socket.SOCK_STREAM)
            self.server_sock.bind(('', self.port))
            self.server_sock.listen(1)
            print("started listening")
            self.sock, self.client_addr = self.server_sock.accept()
            print('Connected to client..')
        except socket.error as err:   
            print('reverse dcc server creation error')
            print(err)


    def close_pipe(self):
        '''Closes the TCP connection.'''
        if self.sock:
            self.sock.close()
            self.sock = None

    
    def recv(self):
        '''Receives data.'''
        try:
            if self.CODEC:
                chunk = self.sock.recv(self.BUFFER_SIZE).decode(self.CODEC)
            else:
                chunk = self.sock.recv(self.BUFFER_SIZE)
            return chunk
        except UnicodeDecodeError:
            pass


    def send(self, data):
        '''Sends data.'''
        if not self.sock:
            return

        if self.CODEC:
            data = data.encode(self.CODEC)
        self.sock.sendall(data)


    def set_blocking(self, flag):
        '''Changes the socket blocking flag.'''
        if self.sock:
            self.sock.setblocking(flag)
    
    def set_codec(self, CODEC):
        '''Sets unicode format.'''
        self.CODEC = CODEC

    def set_buffer_size(self, BUFFER_SIZE):
        '''Sets buffer_size.'''
        self.BUFFER_SIZE = BUFFER_SIZE

    def fileno(self):
        '''Returns fileno descriptor of socket.'''
        if self.sock:
            return self.sock.fileno()

    def is_connected(self):
        '''Checks if the socket is connected or not.'''
        return True if self.sock else False