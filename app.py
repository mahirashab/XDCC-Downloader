

import select
import threading
from scripts.logger import setup_logger
from scripts.bot.user import User
from scripts.bot.pack import Pack
from scripts.bot.xdcc_bot import XDCC_Downloader

setup_logger()

user = User('mahirr', 'rriham', 'Mahir Ashab')
pack = Pack('irc.abandoned-irc.net', '#PORN-HQ', '[PhQ]-ak-47', '#175')
xdcc = XDCC_Downloader(user, pack)
xdcc.process_forever()

# xdcc.connect()

# def start():
#     while True:
#         r, w, e = select.select([xdcc.socket], [], [], 0.2)
#         if r:
#             xdcc.recv_data()
            
# t = threading.Thread(target=start, daemon=True)
# t.start()