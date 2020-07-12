import os
import sys
import json
import os.path
import colorama
from pathlib import Path
from xdcc_downloader.bot.user import User
from xdcc_downloader.bot.pack import Pack
from xdcc_downloader.logger import setup_logger
from PyInquirer import Validator, ValidationError
from PyInquirer import style_from_dict, Token, prompt
from xdcc_downloader.bot.xdcc_bot import XDCC_Downloader
from xdcc_downloader.bot.server_connection import ServerConnection


style = style_from_dict({
    Token.QuestionMark: '#E91E63 bold',
    Token.Selected: '#673AB7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#2196f3 bold',
    Token.Question: '#34d1b2 bold',
})


class EmptyValidator(Validator):
    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


class FileValidator(Validator):
    def validate(self, value):
        file_name = value.text
        file_path = os.path.expanduser(os.path.abspath(file_name))

        if os.path.exists(file_path):
            return True
        else:
            raise ValidationError(
                message="No Such File Found.",
                cursor_position=len(value.text))
            


def options_prompt():
    questions = [
        {
            'type': 'list',
            'name': 'choosen',
            'message': 'Choose input method ::',
            'choices': ['From Prompt (from single bot)', 'From Json file (from multiple bots)']
        }
    ]

    answers = prompt(questions, style=style)
    if answers['choosen'] == 'From Prompt (from single bot)':
        return 'from_prompt'
    else:
        return 'from_file'


def json_file_prompt():
    questions = [
        {
            'type': 'input',
            'name': 'file_name',
            'message': 'Input json file path ??',
            'default': './',
            'validate': FileValidator
        }
    ]

    answers = prompt(questions, style=style)
    return answers['file_name']



def download_prompt():
    questions = [
        {
            'type': 'input',
            'name': 'server',
            'message': 'Input server name ??',
            'validate': EmptyValidator
        },
        {
            'type': 'input',
            'name': 'channel',
            'message': 'Input channel name ??',
            'validate': EmptyValidator
        },
        {
            'type': 'input',
            'name': 'message',
            'message': 'Input message to bot ??',
            'validate': EmptyValidator
        },
        {
            'type': 'input',
            'name': 'file_path',
            'message': 'File output folder?',
            'default': os.getcwd()
        }
    ]

    answers = prompt(questions, style=style)

    server = answers['server']
    message = answers['message']
    file_path = answers['file_path']

    channels = answers['channel'].replace(' ', ',')
    channels = list(filter(None, channels.split(',')))

    channels = ['#'+channel 
                if not channel.startswith('#') 
                else channel
                for channel in channels] 
    
    return (server, channels, message, file_path)



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
    


def print_intro():
    logo = '''
 ██╗  ██╗██████╗  ██████╗ ██████╗  ██████╗  ██████╗ ████████╗
 ╚██╗██╔╝██╔══██╗██╔════╝██╔════╝ ██╔══██╗██╔═══██ ╚══██╔══╝
  ╚███╔╝ ██║  ██║██║     ██║         ██████╔╝██║   ██║   ██║   
  ██╔██╗ ██║  ██║██║     ██║         ██╔══██╗██║   ██║   ██║   
 ██╔╝ ██╗██████╔╝╚██████╗╚██████╗  ██████╔╝╚██████╔╝  ██║   
 ╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝  ╚═════╝    ╚═╝   
                                                               
    '''

    print(colorama.Fore.GREEN, logo, colorama.Style.RESET_ALL)

    