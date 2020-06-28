import sys
import signal
import scripts.prompt as prompt
from scripts.logger import setup_logger
from scripts.xdcc import from_file, from_prompt

def process_terminator(signalNumber, frame):
    sys.exit(0)

if __name__ == '__main__':
    setup_logger()
    prompt.print_intro()
    signal.signal(signal.SIGQUIT, process_terminator)

    choosen = prompt.options_prompt()
    if choosen == 'from_prompt':
        server, channels, message, file_path = prompt.download_prompt()
        from_prompt(server, channels, message, file_path)
    else:
        file_path = prompt.json_file_prompt()
        from_file(file_path)
