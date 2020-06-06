
import os
import tqdm
import socket
from scripts.bot.base import Connect_Factory
from concurrent.futures import ThreadPoolExecutor


# Executor = ThreadPoolExecutor(max_workers=1)


class DCC_Client():
    BUFFER_SIZE = 2048
    FILE_MODE = 'wb'

    def __init__(self, ip, port, filename, filesize, offset=None):
        self.ip = ip
        self.port = port
        self.addr = (ip, port)
        
        self.connect_factory = Connect_Factory()

        self.filename = filename
        self.filesize = filesize

        self.offset = 0
        if offset:
            self.FILE_MODE = 'ab'
            self.offset = int(offset)        

    
    def connect(self):
        try:
            self.socket = self.connect_factory.connect(self.addr)
            self.socket.settimeout(3)
        except socket.error as err:
            print('socket error...')
            print(err)


    def recv_data(self, timeout=0.3):
        progress = tqdm.tqdm(range(self.filesize), f"Receiving {self.filename}", unit="B", unit_scale=True, unit_divisor=1024, leave=False, initial=self.offset)
        
        with open(self.filename, self.FILE_MODE) as f:
            while True:
                try:
                    data = self.socket.recv(self.BUFFER_SIZE)
                except (socket.error, socket.timeout):
                    break

                if not data:
                    print("not data..")
                    continue
                    
                f.write(data)
                progress.update(len(data))

                
            print('download complete')
            progress.close()
            self.socket.close()