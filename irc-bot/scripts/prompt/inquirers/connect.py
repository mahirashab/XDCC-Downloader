

from scripts.bot import Main_Bot
from PyInquirer import (Token, ValidationError, Validator, print_json, prompt,
                        style_from_dict)

style = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
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


class ServerValidator(Validator):
    def validate(self, value):

        input_value = value.text.replace(' ', '')

        added_servers = Main_Bot.client_hash_table.keys()
        server_exists = input_value in list(added_servers)

        length = len(input_value)
        
        if not length:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))
        elif server_exists:
            raise ValidationError(
                message="Server already exists..",
                cursor_position=len(value.text))
        else:
            return True


def connect_inquirer():
   
    questions = [
        {
            'type': 'input',
            'name': 'server',
            'message': 'Server Name ::',
            'filter': lambda val: val.replace(' ', ''),
            'validate': ServerValidator
        },
        {
            'type': 'input',
            'name': 'channels',
            'message': 'Channel Names ::',
            'filter': lambda val: val.replace(' ', ''),
            'validate': EmptyValidator
        },
        {
            'type': 'input',
            'name': 'nick',
            'message': 'Nickname ::'
        },
        {
            'type': 'input',
            'name': 'user',
            'message': 'Username ::'
        },
        {
            'type': 'input',
            'name': 'real',
            'message': 'Realname ::'
        }
    ]

    answers = prompt(questions, style=style)
    return answers