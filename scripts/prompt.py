import os
import colorama
from scripts.bot.pack import Pack
from PyInquirer import Validator, ValidationError
from PyInquirer import style_from_dict, Token, prompt


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


def print_intro():
    logo = '''
██╗  ██╗██████╗  ██████╗ ██████╗    ██████╗  ██████╗ ████████╗
╚██╗██╔╝██╔══██╗██╔════╝██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝
 ╚███╔╝ ██║  ██║██║     ██║         ██████╔╝██║   ██║   ██║   
 ██╔██╗ ██║  ██║██║     ██║         ██╔══██╗██║   ██║   ██║   
██╔╝ ██╗██████╔╝╚██████╗╚██████╗    ██████╔╝╚██████╔╝   ██║   
╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═════╝    ╚═════╝  ╚═════╝    ╚═╝   
                                                               
    '''

    print(colorama.Fore.GREEN, logo, colorama.Style.RESET_ALL)

    