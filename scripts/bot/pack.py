
import os

class Pack:
    
    def __init__(self, server, channel, bot, package, file_path=None):

        self.bot = bot
        self.server = server
        self.channel = channel
        self.package = package
        
        self.file_path = file_path
        self.file_name = None 
        self.ip = None 
        self.port = None 
        self.size = 0 
    
        
    def get_package_req(self):
        return "xdcc send {}".format(self.package)
    
    def get_resume_req(self):
        return "DCC RESUME {} {} {}".format(self.file_name, 
                                                self.port, 
                                                self.current_size)
    
    def file_exists(self, file_name):
        if self.file_path:
            return os.path.join(self.file_path, self.file_name)
        else:
            return os.path.exists(file_name)
    

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

    @property
    def current_size(self):
        if not self.file_name:
            return None
        
        if self.file_path:
            joined_path = os.path.join(self.file_path, self.file_name)
            return os.path.getsize(joined_path)
        else:
            return os.path.getsize(self.file_name)
    