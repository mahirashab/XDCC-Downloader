from scripts.bot import Main_Bot
from PyInquirer import (Token, ValidationError, Validator, prompt,
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


def dcc_inquirer():

    server_name = [
        {
            'type': 'list',
            'name': 'server',
            'message': 'Select Server ::',
            'choices': Main_Bot.client_hash_table.keys()
        }
    ]

    server = prompt(server_name, style=style)
    SERVER_NAME = server['server']
   
    questions = [
        {
            'type': 'list',
            'name': 'channel',
            'message': 'Choose channel ::',
            'choices': Main_Bot.client_hash_table[SERVER_NAME].channels
        },
        {
            'type': 'input',
            'name': 'target',
            'message': 'Owner name ::',
            'validate': EmptyValidator
        },
        {
            'type': 'input',
            'name': 'file_name',
            'message': 'File name ::',
            'validate': EmptyValidator
        }
    ]

    options = prompt(questions, style=style)
    server.update(options)
    return server