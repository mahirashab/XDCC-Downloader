

from colorama import Fore, Back, Style

def colored_print(text, *styles):
    style = ''.join(styles)
    print(style + text + Style.RESET_ALL)
