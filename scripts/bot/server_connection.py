import time
import socket
from scripts.bot.exceptions import ConnectionFailure

class ServerConnection:
    sock = None
    server = None
    client_addr = None
    ip_type = socket.AF_INET

    max_retries = 2
    current_retries = 1

    def __init__(self, server, CODEC, BUFFER_SIZE, port=6667, reversed_conn=False, ipv6=False):
        if ipv6:
            self.ip_type = socket.AF_INET6

        self.CODEC = CODEC
        self.BUFFER_SIZE = BUFFER_SIZE
        self.REVERSED_CONN = reversed_conn
        
        self.server = str(server)
        self.port = int(port)
        self.addr = (self.server, self.port)


    def create_pipe(self, timeout=3):
        if self.REVERSED_CONN:
            self.as_server()
        else:
            self.as_client(timeout=timeout)
        

    def as_client(self, timeout=3):
        try:
            self.sock = socket.socket(self.ip_type, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect(self.addr)
            self.sock.setblocking(False)
        except socket.error:
            self.sock = None
            if self.current_retries >= self.max_retries:
                raise ConnectionFailure()

            time.sleep(3)
            self.current_retries += 1
            self.as_client()

    
    def as_server(self):
        try:
            self.server = socket.socket(self.ip_type, socket.SOCK_STREAM)
            self.server.bind(self.addr)
            self.server.listen(1)
            print("started listening")
            self.sock, self.client_addr = self.server.accept()
            print('Connected to client..')
        except socket.error as err:   
            print('reverse dcc server creation error')
            print(err)


    def close_pipe(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    
    def recv(self):
        try:
            if self.CODEC:
                chunk = self.sock.recv(self.BUFFER_SIZE).decode(self.CODEC)
            else:
                chunk = self.sock.recv(self.BUFFER_SIZE)
            return chunk
        except UnicodeDecodeError:
            pass


    def send(self, data):
        if not self.sock:
            return

        if self.CODEC:
            data = data.encode(self.CODEC)
        self.sock.sendall(data)

    def set_blocking(self, flag):
        if self.sock:
            self.sock.setblocking(flag)
    
    def set_codec(self, CODEC):
        self.CODEC = CODEC

    def set_buffer_size(self, BUFFER_SIZE):
        self.BUFFER_SIZE = BUFFER_SIZE

    def fileno(self):
        if self.sock:
            return self.sock.fileno()

    def is_connected(self):
        return True if self.sock else False