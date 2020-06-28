import os
import struct
import socket
import random
import os.path as path
from typing import Union

class Pack:
    
    def __init__(self, 
                channels: list, 
                bot: str, 
                package: str, 
                file_path: str=os.getcwd()):
        '''
        Initializes a pack instance.
        It holds all the info needed to download a single package.
        :param channels: List of channels.
        :param bot: The bot name serving the package.
        :param package: The Package to be downloaded.
        :param file_path: Location the file will be stored.
        '''
        self.bot = bot
        self.package = package
        self.fallback_channels = channels
        self.file_path = self._prepare_file_path(file_path)

        self.ip = None 
        self.port = None 
        self.size = None
        self.token = None
        self.file_name = None 

        
    def get_package_req(self):
        '''Returns the request message.'''
        return "xdcc send {}".format(self.package)
    

    def get_reversed_dcc_accept_msg(self):
        '''Returns the reversed xdcc accept message.'''
        return "DCC SEND {} {} {} {} {}".format(self._formatted_filename(), 
                                                self.ip,
                                                self.port,
                                                self.size,
                                                self.token)

    def get_resume_req(self):
        '''Returns the resume request message.'''
        return "DCC RESUME {} {} {}".format(self._formatted_filename(), 
                                                self.port, 
                                                self.current_size(self.file_name))


    def get_reversed_dcc_resume_req(self):
        '''Returns the reversed xdcc request message.'''
        return "DCC RESUME {} 0 {} {}".format(self._formatted_filename(),
                                            self.size,
                                            self.token)
      

    def set_info(self, file_name: str, 
                ip: int, port: int, size: int, 
                token: Union[str, int]):
        '''
        Sets the package info.
        Used to Download and save the file.
        :param filename: Actual filename of the pack.
        :param ip: IP address of the bot.
        :param port: Opened port by the bot.
        :param size: Size of the file in bytes.
        :param token: Unique int used by reversed xdcc communication.
        :return: None.
        '''
        if port == 0:
            ip = '192.168.0.106' # Your LOCAL IP. STILL HAS PROBLEMS.
            packedIP = socket.inet_aton(ip)
            self.ip = struct.unpack("!L", packedIP)[0]
            self.port = random.randint(10000, 50000)
        else:
            self.ip = ip
            self.port = port 
        
        self.size = size
        self.token = token
        self.file_name = file_name

    
    def file_exists(self, file_name: str):
        '''
        Returns true if the file alredy exists 
        in the download location folder.
        :param file_name: Name of the file.
        :return: Bool.
        '''
        file_path = os.path.join(self.file_path, file_name)
        return os.path.exists(file_path)


    def set_filename(self, file_name: str):
        '''Sets the file_name.'''
        self.file_name = file_name

    def set_ip(self, ip: str):
        '''Sets the ip of the bot.'''
        self.ip = ip
    
    def set_port(self, port: int):
        '''Sets the opeded port by bot.'''
        self.port = int(port)
    
    def set_size(self, size: int):
        '''Sets the file size.'''
        self.size = int(size)


    def get_file_path(self):
        '''
        Returns the absolute path of the file.
        :return: Absolute path of the file store location.
        '''
        return path.join(self.file_path, self.file_name)
    

    def _formatted_filename(self):
        '''
        Adds '"' to the beginning and the end of file_name
        If the filename contains blank spaces.
        :return: File_name that can be used in server messages. 
        '''
        file_name = self.file_name
        if ' ' in file_name:
            file_name = '"' + self.file_name + '"'
        return file_name


    def _prepare_file_path(self, file_path):
        '''
        Returns absolute path if relative and
        creates the folders if needed.
        :param file_path: file path to be fixed.
        :return: Fixed file path.
        '''
        if not path.isabs(file_path):
            file_path = path.abspath(file_path)

        file_path = path.expanduser(file_path)
        if not path.exists(file_path):
            os.makedirs(file_path)
        
        return file_path
             

    def current_size(self, file_name):
        '''
        Returns the file size if found else 0.
        :return: The size of file in bytes.
        '''
        try:
            joined_path = path.join(self.file_path, file_name)
            return path.getsize(joined_path)
        except FileNotFoundError:
            return 0


    @classmethod
    def from_message(cls, channels: list, message: str, file_path: str='./'):
        '''
        Creates Pack instances from message.
        :param channels: List of channels.
        :param message: download message of the pack(s).
        :param file_path: Location the file will be stored.
        :return: List of Pack instances.
        '''
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