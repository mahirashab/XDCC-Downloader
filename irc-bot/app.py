#!./env/bin/python3

import threading
from scripts.api import app, api
from scripts.bot import Main_Bot
from scripts.logger import setup_logger
from scripts.api.resources.root import Server, Channel

setup_logger() # Sets up the logger...

# Creates the main bot thread...
IRC_Bot_thread = threading.Thread(target=Main_Bot.process_forever, daemon=True)

# Adding all the resources to routes...
api.add_resource(Server, '/server')
api.add_resource(Channel, '/channel')


if __name__ == '__main__':
    IRC_Bot_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)
