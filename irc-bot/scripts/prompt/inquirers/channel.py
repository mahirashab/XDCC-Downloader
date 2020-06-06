
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


def getContentType(answer, content, match_value):
    return answer.get(content).lower() == match_value.lower()


class EmptyValidator(Validator):
    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


def channel_inquirer():

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
            'name': 'action',
            'message': 'Choose action ::',
            'choices': ['add', 'remove']
        },
        {
            'type': 'input',
            'name': 'channels',
            'message': 'Channel Name(s) ::',
            'when': lambda answers: getContentType(answers, 'action', "add"),
            'filter': lambda val: val.replace(' ', ''),
            'validate': EmptyValidator
        },
        {
            'type': 'list',
            'name': 'channels',
            'message': 'Choose channel names ::',
            'when': lambda answers: getContentType(answers, 'action', "remove"),
            'choices': Main_Bot.client_hash_table[SERVER_NAME].channels
        },
    ]

    options = prompt(questions, style=style)
    server.update(options)
    return server