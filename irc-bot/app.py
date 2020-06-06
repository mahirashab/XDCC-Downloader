
import threading
from scripts.bot import Main_Bot
from scripts.db import init_db
from scripts.prompt import IRC_Prompt
from scripts.logger import setup_logger
    
setup_logger()
init_db()

Main_Bot_Thread = threading.Thread(target=Main_Bot.process_forever, daemon=True)


if __name__ == '__main__':
    Main_Bot_Thread.start()
    app = IRC_Prompt()
    app.cmdloop()
