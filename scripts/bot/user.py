
import names

class User:
    
    def __init__(self, 
                nick=None, 
                user=None, 
                real=None):
        
        self.nick = nick or names.get_first_name()
        self.user = user or names.get_last_name()
        self.real = real or names.get_full_name()
    
    def new_nick(self):
        self.nick = names.get_first_name()