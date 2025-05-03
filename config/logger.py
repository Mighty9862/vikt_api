import logging
import colorama
from colorama import Fore, Style

# Инициализация colorama для Windows
colorama.init()

class ColoredFormatter(logging.Formatter):
    """Форматтер для цветных логов"""
    
    def format(self, record):
        if record.levelno >= logging.ERROR:
            color = Fore.RED
        elif record.levelno >= logging.WARNING:
            color = Fore.YELLOW
        elif record.levelno >= logging.INFO:
            if 'fastapi' in record.name:
                if "GET" in str(record.msg) or "POST" in str(record.msg):
                    color = Fore.MAGENTA
                else:
                    color = Fore.BLUE
            else:
                color = Fore.CYAN
        else:
            color = Fore.GREEN
            
        if 'fastapi' in record.name:
            record.msg = f"{color}[API] {record.msg}{Style.RESET_ALL}"
        else:
            record.msg = f"{color}[ИГРОВОЙ СЕРВЕР] {record.msg}{Style.RESET_ALL}"
        return super().format(record)

def setup_logging():
    logger = logging.getLogger('game_server')
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter('%(message)s'))

    console_handler.setLevel(logging.INFO)


    logger.addHandler(console_handler)

    return logger 