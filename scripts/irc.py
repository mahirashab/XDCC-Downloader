import sys
from scripts.bot.pack import Pack
from scripts.bot.user import User
from scripts.bot.xdcc_bot import XDCC_Downloader
from scripts.bot.server_connection import ServerConnection

class IRC:

    def __init__(self, xdcc_bots):
        self.xdcc_bots = xdcc_bots

    
    def begin_process(self):
        for xdcc_bot in self.xdcc_bots:
            xdcc_bot.download()


    @classmethod
    def from_prompt(cls, server, channel, message, file_path):
        packs = Pack.from_message(channel, message, file_path=file_path)
        xdcc_bots = [XDCC_Downloader(ServerConnection(server, 'utf-8', 512), pack, User())
                    for pack in packs]   

        return cls(xdcc_bots)