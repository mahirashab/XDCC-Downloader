#!/usr/bin/python3

import client
import selectors

class IRC_Object:

    def __init__(self):
        self.selector = selectors.DefaultSelector()
        self.connections = []

    def add_connection(self, client):
        self.connections.append(client)
        self.selector.register(client.connection, selectors.EVENT_READ, data=client)

    def create_connection(self):
        cnt = client.IRC_Client()
        cnt.connect()
        self.add_connection(cnt)

    def process_all_connections(self):
        while True:
            for key, mask in self.selector.select(timeout=1.0):
                sock = key.fileobj
                cnt = key.data

                if mask & selectors.EVENT_READ:
                    response = sock.recv(512).decode("utf-8")
                    cnt.replies_handler.process_replies(response)




            
