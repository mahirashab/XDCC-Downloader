#!/usr/bin/python3

import select
import time
import scripts.client as client

class IRC_Object:

    def __init__(self):
        self.connections = []
        
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