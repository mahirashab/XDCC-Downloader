
import os

class Pack:
    
    def __init__(self, server, channel, bot, package):
        self.server = server
        self.channel = channel
        self.bot = bot
        self.package = package
        
        self.file_name = None 
        self.ip = None 
        self.port = None 
        self.size = None 

        self.info = {}
        
        
    def store_file_info(self, filename, info):
        self.info[filename] = info    
        
    def get_package_req(self):
        return "PRIVMSG {} :\001XDCC send {}\001".format(self.bot, self.package)
    
    def get_resume_req(self):
        return "PRIVMSG {} :\001DCC RESUME {} {} {}\001".format(self.bot, 
                                                                self.file_name, 
                                                                self.port, 
                                                                self.position)
    
    def file_exists(self, file_name):
        return os.path.exists(file_name)
    

    @property
    def position(self):
        if not self.file_name:
            return None

        return os.path.getsize(self.file_name)

    def set_info(self, file_name, ip, port, size):
        self.file_name = file_name
        self.ip = ip
        self.port = int(port)
        self.size = int(size)


    def set_filename(self, file_name):
        self.file_name = file_name

    def get_file_name(self):
        return self.file_name
    
    def set_ip(self, ip):
        self.ip = ip
    
    def get_ip(self):
        return self.ip
        
    def set_port(self, port):
        self.port = int(port)

    def get_port(self):
        return int(self.port)

    def set_size(self, size):
        self.size = int(size)
    
    def get_size(self):
        return int(self.size)
    