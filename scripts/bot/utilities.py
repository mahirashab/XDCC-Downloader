

import re
import time
import logging
import datetime
from functools import wraps
from typing import Any, Callable
from colorama import Fore, Back, Style

def colored_print(text, styles):
    style = ''.join(styles)
    print(style + text + Style.RESET_ALL)



def timeit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Times a function, usually used as decorator"""
    logger = logging.getLogger("mainlogger")
    @wraps(func)
    def timed_func(*args: Any, **kwargs: Any) -> Any:
        """Returns the timed function"""
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = datetime.timedelta(seconds=(time.time() - start_time))
        logger.debug("time spent on %s: %s", func.__name__, elapsed_time)
        return result

    return timed_func


class Buffer:
    def __init__(self):
        self.buffer = ''
        self.stored = []
        self.seperator = '\r\n'
    
    def feed(self, data):
        splitted = data.split(self.seperator)
        splitted[0] = self.buffer + splitted[0]
        self.buffer = splitted[-1]

        self.stored += splitted[:-1]   

    def __iter__(self):
        lines, self.stored = self.stored, []
        return iter(lines)


class Source(str):      
    @property
    def sender(self):
        return self.split('!')[0]
    
    def __repr__(self):
        return "< Source sender:%s >" % (self.sender)

    def __str__(self):
        return "< Source sender:%s >" % (self.sender)


class Argument(str):
    @property
    def receiver(self):
        temp = self.split(':')[0].split(' ')
        temp = filter(lambda x: x, temp)
        return list(temp)[0]     
    
    @property
    def message(self):
        return self.split(':')[1]
    
    @property
    def channels(self):
        channels = re.findall(r'(?P<channel>#[^ ]+)', self)
        return [channel.lower() for channel in channels]
    
    def __repr__(self):
        return "< Argument receiver:%s channels:%s message:%s>" % (self.receiver, self.channels, self.message)

    def __str__(self):
        return "< Argument receiver:%s channels:%s message:%s>" % (self.receiver, self.channels, self.message)


class Event:
    def __init__(self, type, source, argument):
        self.type = type
        self.source = source
        self.argument = argument
