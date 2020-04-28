#!./env/bin/python3

import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter

class Interpreter:
    def __init__(self, irc_bot):
        self.irc_bot = irc_bot
        self.level = "BASE"
        self.setup_config()
        self.session = PromptSession()
        

    
    def setup_config(self):

        self.config = {
            'BASE': {
                'connections': self.connections,
                'disconnect' : self.disconnect,
                'completer': WordCompleter(['connections', 'disconnect'])
            }
        }

        self.prompt_style = Style.from_dict({
            # User input (default text).
            '':          '#ff0066',

            # Prompt.
            'prompt': '#00ffff',
            'dash':       '#00aa00',
            'tail':    '#00aa00',
        })


    def run_prompt(self):
        prompt = [
            ('class:prompt', 'IRC-Bot'),
            ('class:dash',       '-'),
            ('class:tail',    '~> '),
        ]
        completer = self.config[self.level]['completer']

        while True:
            command = self.session.prompt(prompt, style=self.prompt_style, completer=completer, complete_while_typing=True)
            self.process_command(command)

    
    def process_command(self, command):
        words = command.split(' ')
        words = list(map(lambda x: x.rstrip(), words))
        main_command = words[0]
        args = words[1:]

        level_commands = self.config[self.level].keys()

        if main_command in level_commands:
            self.config[self.level][main_command](args=args)
        else:
            print("Invalid command fot this level...")

    
    def connections(self, args=None):
        if not self.irc_bot.connections: print('\n No Connections. \n')

        for index, conn in enumerate(self.irc_bot.connections):
            print(f'\n  Connection {index}')
            print(f'Server addr ({conn.server}) Real name ({conn.real_server})\n')


    def disconnect(self, args=None):
        try:
            index = args[0]
            if index.isdigit() and int(index) <= len(self.irc_bot.connections) - 1:
                self.irc_bot.remove_connection(self.irc_bot.connections[int(index)])
                print(f'\n Disconnected conn {index}. \n')
            else:
                print('\n Invalid command argument')
                print('disconnect <index of connection>\n')
        except IndexError:
            print('\n No argument given \n')
        
        

    
    
        