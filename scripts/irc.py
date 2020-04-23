#!/usr/bin/python3

import select
import time
import logging
import logging.config
import sys
import os
import scripts.client as client

class IRC_Object:

    def __init__(self):
        self.connections = []
        self.setup_logger()

    
    def setup_logger(self):
        parent_dir = os.getcwd()
        log_folder = os.path.join(parent_dir, "logs/")
        log_config_file = os.path.join(parent_dir, "logger.ini")

        if not os.path.exists(log_config_file):
            print("No log formatter file")
            sys.exit(1)
        else:
            print("Setup config")
            logging.config.fileConfig(log_config_file, disable_existing_loggers=False)
        

        if not os.path.exists(log_folder):
            os.mkdir(log_folder)

        # activity_log_file = os.path.join(log_folder, "activity.log")
        # m_log_file = os.path.join(log_folder, "messages.log")

        activity_logger = logging.getLogger("ActivityLogger")
        message_logger = logging.getLogger("MessageLogger")

        activity_logger.info("Logging")
        
        
    def create_connection(self):
        cnt = client.IRC_Client()
        self.connections.append(cnt)
        return cnt

    def process_all_connections(self, timeout=1):
        while True:

            sockets = map(lambda c: c.get_socket(), self.connections)
            sockets = list(filter(lambda s: s != None, sockets))

            if sockets:
                start = time.perf_counter()
                writable, readable, error = select.select(sockets, [], sockets, timeout)
                stop = time.perf_counter()

                print(f"Took {round(stop - start, 3)} seconds...")

                for s in writable:
                    for c in self.connections:
                        if s == c.get_socket():
                            c.run_once()
            else:
                time.sleep(1)