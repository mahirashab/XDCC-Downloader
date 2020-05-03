#!./env/bin/python3

import os
import sys
import time
import select
import logging
import logging.config
import scripts.client as client
import scripts.interpreter as interpreter

class IRC_Bot_Object:
    '''This Class is the main bot that manages all the connections.
       It keeps all the clients in the list connections.
       And used select() sysyem call to monitor incoming data in the run() function.
    '''

    def __init__(self):
        self.connections = []
        self.setup_logger()

    
    '''This creates and returns client object..'''
    def create_connection(self):
        cnt = client.IRC_Client()
        self.connections.append(cnt)
        return cnt

    
    '''This removes a client object...'''
    def remove_connection(self, connection):
        try:
            connection.disconnect()
            self.connections.remove(connection)
        except ValueError:
            print("\nInvalid server given...")

    
    '''This sets up the main loggers...
       The logger.ini file is used to configure the loggers...
       This is called by the IRC_Bot in __init__ function...
    '''
    def setup_logger(self):
        parent_dir = os.getcwd()
        log_folder = os.path.join(parent_dir, "logs/")
        log_config_file = os.path.join(parent_dir, "logger.ini")

        if not os.path.exists(log_folder):
            os.mkdir(log_folder)

        if not os.path.exists(log_config_file):
            print("No log formatter file")
            sys.exit(1)
        else:
            logging.config.fileConfig(log_config_file, disable_existing_loggers=False)
        


    '''This function is ran on a seperate thread....
       So it runs as a daemon along side the prompt process...
       It used select() system call to monitor the sockets of clients...
       The timeout ammount is slept if no incoming data... 
    '''
    def run(self, timeout=1):
        while True:
            sockets = map(lambda c: c.get_socket(), self.connections)
            sockets = list(filter(lambda s: s != None, sockets))

            if sockets:
                readable, writable, error = select.select(sockets, [], sockets, timeout)

                for s in readable: 
                    for c in self.connections:
                        if s == c.get_socket():
                            c.run_once()
            else:
                time.sleep(1)