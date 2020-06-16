
from scripts.bot.user import User
from scripts.bot.pack import Pack
from scripts.logger import setup_logger
from scripts.prompt import download_prompt
from scripts.bot.xdcc_bot import XDCC_Downloader

setup_logger()

if __name__ == '__main__':
    
    server, channel, bot, package, file_path = download_prompt()

    user = User()
    pack = Pack(server, channel, bot, package)
    xdcc = XDCC_Downloader(user, pack)
    xdcc.download()
