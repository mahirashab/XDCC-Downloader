#!./env/bin/python3

import threading
import os.path as path
import scripts.irc as IRC
import scripts.db.database as db


try:
    import config
except ImportError as err:
    raise Exception("No config file....")


def main():
    '''This is the main (Bot) that manages all the connections..'''
    IRC_Bot = IRC.IRC_Bot_Object()

    nick, user, real, password, ssl = config.get_user()
    servers = config.get_servers()

    if servers:
        for server in servers:
            client = IRC_Bot.create_connection()
            client.connect(server["Address"], server["Port"], server["Channels"], nick, user, real, db.session)
    
    '''This initiates the database...'''
    db.init_db()

    '''This thread runs the IRC_Bot object main controller in the background...'''
    # IRC_Bot_thread = threading.Thread(target=IRC_Bot.run, daemon=True)
    # IRC_Bot_thread.start()

    '''This runs the main loop...'''
    IRC_Bot.run()
        

if __name__ == "__main__": 
    main()
    