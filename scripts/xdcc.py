import sys
import json
import os.path
from pathlib import Path
from scripts.bot.pack import Pack
from scripts.bot.user import User
from scripts.bot.xdcc_bot import XDCC_Downloader
from scripts.bot.server_connection import ServerConnection


def from_prompt(server, channel, message, file_path):
    '''
    Downloads packs using ctcp message.
    :param server: Server address.
    :param channel: Channels to be joined to communicate with bot.
    :param message: ctcp message to bot.
    :param file_path: Location where the files are stored.
    :return: None
    '''
    packs = Pack.from_message(channel, message, file_path=file_path)
    xdcc_bots = [XDCC_Downloader(ServerConnection(server, 'utf-8', 512), pack, User())
                for pack in packs]  

    for xdcc_bot in xdcc_bots:
        xdcc_bot.download() 

    
def from_file(json_file_path):
    '''
    Downloads all the packs in a json file.
    :param json_file_path: Path of the json file.
    :return: None
    '''
    if not os.path.exists(json_file_path):
        print("No such file..")
        sys.exit(0)

    if not Path(json_file_path).suffix == '.json':
        print("Not a json file..")
        sys.exit(0)

    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)
        if type(data) != list:
            print("Not list..")
            sys.exit(0)

    for download_task_data in data:
        if download_task_data.get("pass", False):
            continue

        server, channel, msg, f_path = (download_task_data["server"], 
                                        download_task_data["channel"], download_task_data["message"], download_task_data["file_path"])

        packs = Pack.from_message(channel, msg, file_path=f_path)
        xdcc_bots = [XDCC_Downloader(ServerConnection(server, 'utf-8', 512), pack, User())
                    for pack in packs]
        
        for xdcc_bot in xdcc_bots:
            xdcc_bot.download()
        