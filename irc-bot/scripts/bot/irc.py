
import time
import functools
import select
import schedule
import itertools
import logging
from scripts.api import app
from scripts.bot.client import IRC_Client
from scripts.db.models import AddedServers
from more_itertools import consume, repeatfunc



class IRC_Bot_Object:
    '''This Class is the main bot that manages all the connections.
       It keeps all the clients in the list connections.
       And used select() sysyem call to monitor incoming data in the run() function.
    '''

    main_logger = logging.getLogger("mainlogger")
    main_logger.info('Starting Irc_Bot...')
    
    def __init__(self):   
        self.client_hash_table = {}
        self.clients = []
        self.schedule_jobs()


    def schedule_jobs(self):
        # Register all the bg jobs...
        schedule.every(2).minutes.do(self.update_client_status)
        schedule.every(2).minutes.do(self.check_connection)


    def create_client(self):
        # This creates and returns client object..
        client = IRC_Client()
        self.clients.append(client)
        return client


    def remove_client(self, client):
        # This removes a client object...
        client.disconnect()
        del self.client_hash_table[client.server]
        self.clients.remove(client)


    @property
    def sockets(self):
        # Returns the readable sockets...
        return [
            client.socket 
            for client in self.clients 
            if client.connected and client.socket
        ]


    def update_client_status(self):
        # Updates the info in db AddedServers...
        # 
        for conn in self.clients:
            with app.app_context():
                AddedServers.update_info(conn.server, {
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
        # Check if the clients are connected...
        for conn in reversed(self.clients):
            if conn.reconnect_tries < conn.max_reconnect_tries:
                if not conn.connected:
                    conn.reconnect()
            else:
                with app.app_context():
                    AddedServers.delete_server(conn.server)
                self.remove_client(conn)



    def process_once(self, timeout=None):
        sockets = self.sockets # Gets connected sockets...

        if sockets:
            readable, writable, error = select.select(sockets, [], sockets, timeout)

            for sock, conn in itertools.product(readable, self.clients):
                if sock == conn.socket: # Matches socket to client and gets data...
                    conn.recv_data()
        else:
            time.sleep(1)
        # Run the bg jobs...
        schedule.run_pending()

    def process_forever(self, timeout=0.2):
        # Run the main infinite loop...
        once = functools.partial(self.process_once, timeout=timeout)
        consume(repeatfunc(once))
