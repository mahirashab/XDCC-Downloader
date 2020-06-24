import os
import struct
import socket
import random
import os.path as path

class Pack:
    file_name = None 
    ip = None 
    port = None 
    size = 0 
    token = ''
    
    def __init__(self, channels, bot, package, file_path=os.getcwd()):
        self.bot = bot
        self.package = package
        self.fallback_channels = channels
        
        self.file_path = self._prepare_file_path(file_path)
    
        
    def get_package_req(self):
        return "xdcc send {}".format(self.package)
    
    def get_reversed_dcc_accept_msg(self):

        return "DCC SEND {} {} {} {} {}".format(self._formatted_filename(), 
                                                self.ip,
                                                self.port,
                                                self.size,
                                                self.token)

    def get_resume_req(self):
        return "DCC RESUME {} {} {}".format(self._formatted_filename(), 
                                                self.port, 
                                                self.current_size())

    def get_reversed_dcc_resume_req(self):
        return "DCC RESUME {} 0 {} {}".format(self._formatted_filename(),
                                            self.size,
                                            self.token)
    
    

    def set_info(self, file_name, ip, port, size, token):
        if port == 0:
            ip = '' # Your LOCAL IP. STILL HAS PROBLEMS.
            packedIP = socket.inet_aton(ip)
            self.ip = struct.unpack("!L", packedIP)[0]
            self.port = random.randint(10000, 50000)
        else:
            self.ip = ip
            self.port = port 
        
        self.size = size
        self.token = token
        self.file_name = file_name

    
    def file_exists(self, file_name):
        file_path = os.path.join(self.file_path, file_name)
        return os.path.exists(file_path)

    def set_filename(self, file_name):
        self.file_name = file_name
    
    def _formatted_filename(self):
        file_name = self.file_name
        if ' ' in file_name:
            file_name = '"' + self.file_name + '"'
        return file_name

    def get_file_path(self):
        return path.join(self.file_path, self.file_name)
    

    def set_ip(self, ip):
        self.ip = ip
    
    def set_port(self, port):
        self.port = int(port)
    
    def set_size(self, size):
        self.size = int(size)
    

    def _prepare_file_path(self, file_path):
        if not path.isabs(file_path):
            file_path = path.abspath(file_path)

        file_path = path.expanduser(file_path)

        if not path.exists(file_path):
            os.makedirs(file_path)
        
        return file_path
             

    def current_size(self):
        if not self.file_name:
            return None
        
        try:
            joined_path = path.join(self.file_path, self.file_name)
            return path.getsize(joined_path)
        except FileNotFoundError:
            return 0


    @classmethod
    def from_message(cls,channels, message, file_path='./'):
        message_parts = message.split()
        if not len(message_parts) == 5:
            print('Invalid message..')
            return

        bot = message_parts[1]
        packages = message_parts[4]

        pack_numbers = []
        for package_number in packages.replace('#', '').replace(' ', '').split(','):
            if '-' in package_number:
                l, t = package_number.split('-')
                pack_numbers += list(range(int(l), int(t) + 1))
            else:
                pack_numbers.append(int(package_number))   
        pack_numbers = ['#'+str(n) for n in list(set(pack_numbers))]

        return [cls(channels, bot, pack_num, file_path=file_path) 
                for pack_num in pack_numbers]