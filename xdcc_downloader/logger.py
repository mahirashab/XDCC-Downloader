
import os
import logging.config

parent_dir = os.getcwd()
log_folder = os.path.join(parent_dir, "logs/")

# Creates the logs folder if not found...
if not os.path.exists(log_folder):
    os.mkdir(log_folder)


# DictConfig of all loggers...
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '-- [%(levelname)s] - [%(module)s] - ||| %(message)s'
        },
        'message': {
            'format': '--| %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'main_handler': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.getcwd(), "logs/", "main.log"),
            'mode': 'w'
        },
        'message_handler': {
            'level': 'INFO',
            'formatter': 'message',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.getcwd(), "logs/", "messages.log"),
            'mode': 'w'
        }
    },
    'loggers': {
        'root': {  # root logger
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        'mainlogger': {  # main logger
            'handlers': ['main_handler'],
            'level': 'DEBUG',
            'qualname': 'mainlogger',
            'propagate': False
        },
        'messagelogger': {  # message logger
            'handlers': ['message_handler'],
            'level': 'INFO',
            'qualname': 'messagelogger',
            'propagate': False
        }
    }
}


def setup_logger():
    # Sets up the logger...
    logging.config.dictConfig(LOGGING_CONFIG)
    log = logging.getLogger('mainlogger')
    log.info('Setup of logger is complete')
