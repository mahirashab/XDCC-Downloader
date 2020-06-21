from scripts.irc import IRC
from scripts.logger import setup_logger
from scripts.prompt import download_prompt

setup_logger()

if __name__ == '__main__':
    server, channels, message, file_path = download_prompt()

    irc = IRC.from_prompt(server, channels, message, file_path)
    irc.begin_process()