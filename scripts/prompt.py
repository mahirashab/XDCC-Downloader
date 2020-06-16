
import os
import sys
import os.path as path
from PyInquirer import style_from_dict, Token, prompt
from PyInquirer import Validator, ValidationError


style = style_from_dict({
    Token.QuestionMark: '#E91E63 bold',
    Token.Selected: '#673AB7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#2196f3 bold',
    Token.Question: '',
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
            'default': './'
        }
    ]

    answers = prompt(questions, style=style)

    server = answers['server']

    channel = answers['channel']
    if not channel.startswith('#'):
        channel = '#' + channel

    message_parts = answers['message'].split()
    if len(message_parts) == 5:
        bot = message_parts[1]
        package = message_parts[4]
    else:
        print('Invalid message..')
        sys.exit()

    file_path = answers['file_path']
    if file_path:
        if not path.isabs(file_path):
            file_path = path.abspath(file_path)

        file_path = path.expanduser(file_path)
        if not path.exists(file_path):
            os.makedirs(file_path)

    
    return (server, channel, bot, package, file_path)
    