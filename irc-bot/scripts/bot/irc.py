#!./.env/bin/python3

import time
import functools
import select
import schedule
import itertools
import logging
from scripts.db import DB_Session
from scripts.bot.client import IRC_Client
from more_itertools import consume, repeatfunc
from scripts.db.models import AddedServers



class IRC_Bot_Object:
    '''This Class is the main bot that manages all the connections.
       It keeps all the clients in the list connections.
       And used select() sysyem call to monitor incoming data in the run() function.
    '''

    main_logger = logging.getLogger("mainlogger")
    main_logger.info('Starting Irc_Bot...')
    
    def __init__(self):   
        self.clients = []
        self.schedule_jobs()


    def schedule_jobs(self):
        # Register all the bg jobs...
        schedule.every(2).minutes.do(self.update_client_status)
        schedule.every(1).minute.do(self.check_connection)


    def create_connection(self):
        # This creates and returns client object..
        client = IRC_Client()
        self.clients.append(client)
        return client


    def remove_client(self, client):
        # This removes a client object...
        client.disconnect()
        self.clients.remove(client)


    @property
    def sockets(self):
        # Returns the readable sockets...
        return [
            client.socket for client in self.clients if client.connected and client.socket
        ]


    def update_client_status(self):
        '''This updates all the info in db AddedServers
        '''
        with DB_Session() as session:
            for conn in self.clients:
                session.query(AddedServers).\
                    filter(AddedServers.server == conn.server).\
                    update({
                        "real_server": conn.real_server,
                        "channels": conn.channels,
                        "status": {
                            "connected": conn.connected,
                            "user_registered": conn.user_registered,
                            "names": {
                                "user": conn.user,
                                "nick": conn.nick,
                                "real": conn.real
                            }
                        }
                    })


    def check_connection(self):
        # remove = []

        for conn in reversed(self.clients):
            if conn.reconnect_tries < conn.max_reconnect_tries:
                if not conn.connected:
                    conn.reconnect()
            else:
                with DB_Session() as session:
                    session.query(AddedServers).\
                        filter(AddedServers.server == conn.server).delete()
                self.remove_client(conn)

        # if remove:
        #     self.clients = list(set(self.clients) - set(remove))
        #     with DB_Session() as session:
        #         for conn in remove:
        #             session.query(AddedServers).\
        #                 filter(AddedServers.server == conn.server).delete()


    def process_once(self, timeout=None):
        sockets = self.sockets

        if sockets:
            readable, writable, error = select.select(
                sockets, [], sockets, timeout)

            for sock, conn in itertools.product(readable, self.clients):
                if sock == conn.socket:
                    conn.run_once()
        else:
            time.sleep(1)
        # Run the bg jobs...
        schedule.run_pending()

    def process_forever(self, timeout=0.2):
        # Run the main infinite loop...
        once = functools.partial(self.process_once, timeout=timeout)
        consume(repeatfunc(once))
