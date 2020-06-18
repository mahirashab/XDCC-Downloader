
import os
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

    channel = answers['channel']
    if not channel.startswith('#'):
        channel = '#' + channel

    pack = Pack.from_message(channel, message, file_path=file_path)
    
    return (server, pack)
    