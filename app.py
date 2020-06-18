
from scripts.bot.user import User
from scripts.bot.pack import Pack
from scripts.logger import setup_logger
from scripts.prompt import download_prompt
from scripts.bot.xdcc_bot import XDCC_Downloader
from scripts.bot.pack import Pack
from scripts.bot.server_connection import ServerConnection

setup_logger()

if __name__ == '__main__':
    
    # server, pack = download_prompt()

    server = 'irc.abjects.net'
    channel = '#MOVIEGODS'
    message = '/msg [MG]-MISC|CA|S|BarbiCide xdcc send #213'
    file_path = './'

    pack = Pack.from_message(channel, message, file_path=file_path)


    xdcc = XDCC_Downloader(ServerConnection(server, 'utf-8', 512), User(), pack)
    xdcc.download()


# create from message func in pack
# will return packs

# 