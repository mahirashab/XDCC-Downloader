

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



def disconnect_inquirer():
   
    questions = [
        {
            'type': 'list',
            'name': 'server',
            'message': 'Server Name ::',
            'choices': Main_Bot.client_hash_table.keys()
        },
        {
            'type': 'confirm',
            'name': 'disconnect',
            'message': 'Do you want to disconnect ?? '
        },
    ]

    answers = prompt(questions, style=style)
    return answers