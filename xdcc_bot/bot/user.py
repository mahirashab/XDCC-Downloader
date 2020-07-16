import names

class User:
     
    def __init__(self, nick=None, user=None, real=None):
        '''
        Initiates a User instance.
        It represents a basic user. nick, user, real.
        '''
        self.nick = nick or self.generate_new_nick()
        self.user = user or self.generate_new_user()
        self.real = real or names.get_full_name()

    def generate_new_nick(self):
        '''
        Returns a new nickname.
        :return: A new nick_name.
        '''
        new_nick = names.get_first_name()
        while len(new_nick) >= 9:
            new_nick = names.get_first_name()
        
        return new_nick

    def generate_new_user(self):
        '''
        Returns a new username.
        :return: A new user_name.
        '''
        new_user = names.get_last_name()
        while len(new_user) >= 9:
            new_user = names.get_last_name()
        
        return new_user

    def new_nick(self):
        '''
        Sets a new nick to instance and returns it.
        :return: A new nick.
        '''
        self.nick = self.generate_new_nick()
        return self.nick