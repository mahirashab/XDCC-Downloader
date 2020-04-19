#!/usr/bin/python3

import scripts.client as client

class IRC_Object:

    def __init__(self):
        self.connections = []

    def add_connection(self, client):
        self.connections.append(client)

    def create_connection(self):
        cnt = client.IRC_Client()
        cnt.connect()
        self.add_connection(cnt)

    def process_all_connections(self):
        while True:
            for connection in self.connections:
                connection.run_once()



            
