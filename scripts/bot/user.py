
import names

class User:
    
    def __init__(self, 
                nick=None, 
                user=None, 
                real=None):
        
        self.nick = nick or self.generate_new_nick()
        self.user = user or self.generate_new_user()
        self.real = real or names.get_full_name()
    

    def generate_new_nick(self):
        new_nick = names.get_first_name()
        while len(new_nick) >= 9:
            new_nick = names.get_first_name()
        
        return new_nick

    def generate_new_user(self):
        new_user = names.get_last_name()
        while len(new_user) >= 9:
            new_user = names.get_last_name()
        
        return new_user

    
    def new_nick(self):
        self.nick = self.generate_new_nick()
        return self.nick