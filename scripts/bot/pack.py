
import os
import sys
import os.path as path

class Pack:
    
    def __init__(self, channel, bot, package, file_path=os.getcwd()):

        self.bot = bot
        self.package = package
        self.fallback_channel = channel
        
        self.file_path = self._prepare_file_path(file_path)
        self.file_name = None 
        self.ip = None 
        self.port = None 
        self.size = 0 
    
        
    def get_package_req(self):
        return "xdcc send {}".format(self.package)
    
    def get_resume_req(self):
        return "DCC RESUME {} {} {}".format(self.file_name, 
                                                self.port, 
                                                self.current_size())
    
    def file_exists(self, file_name):
        file_path = os.path.join(self.file_path, self.file_name)
        return os.path.exists(file_path)
    

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



    def _prepare_file_path(self, file_path):
        if not path.isabs(file_path):
            file_path = path.abspath(file_path)

        file_path = path.expanduser(file_path)
        if not path.isdir(file_path):
            file_path = path.abspath(path.join(file_path, os.pardir))

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
    def from_message(cls,channel, message, file_path='./'):

        message_parts = message.split()
        if not len(message_parts) == 5:
            print('Invalid message..')
            sys.exit()

        bot = message_parts[1]
        package = message_parts[4]

        return cls(channel, bot, package, file_path=file_path)


            
    

    