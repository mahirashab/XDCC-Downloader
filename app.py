from scripts.irc import IRC
from scripts.logger import setup_logger
from scripts.prompt import download_prompt

setup_logger()

if __name__ == '__main__':
    # server, channels, message, file_path = download_prompt()

    irc = IRC.from_prompt('irc.scenep2p.net', ['#THE.SOURCE'], '/msg TS-HD|US|P|14620 xdcc send #44', './files')

    # irc = IRC.from_prompt('irc.abjects.net', ['#mahirbot'], '/msg mahir xdcc send #44', './files')

    # irc = IRC.from_prompt('irc.rizon.net', ['#BATCAVE'], '/msg [FutureBot]-[SC39] xdcc send #46', './')

    # irc = IRC.from_prompt('irc.abjects.net', ['#MOVIEGODS'], '/msg [MG]-MISC|EU|S|CRTDMT xdcc send #52', './files')

    irc.begin_process()

