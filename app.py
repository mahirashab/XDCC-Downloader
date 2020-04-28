#!./env/bin/python3

import threading
import os.path as path
import scripts.irc as IRC
from scripts.interpreter import Interpreter

try:
    import config
except ImportError as err:
    raise Exception("No config file....")


def main():
    '''This is the main (Bot) that manages all the connections..'''
    IRC_Bot = IRC.IRC_Bot_Object()

    '''This is the prompt that controls IRC_Bot....'''
    Prompt = Interpreter(IRC_Bot)

    nick, user, real, password, ssl = config.get_user()
    servers = config.get_servers()

    if servers:
        for server in servers:
            client = IRC_Bot.create_connection()
            client.connect(server["Address"], server["Port"], server["Channels"], nick, user, real)
    
    '''This thread runs the IRC_Bot object main controller in the background...'''
    IRC_Bot_thread = threading.Thread(target=IRC_Bot.run, daemon=True)
    IRC_Bot_thread.start()

    '''This is an infinite loop that gets user command to control the IRC_Bot...'''
    Prompt.run_prompt()
        

if __name__ == "__main__": 
    main()
    