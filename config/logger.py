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
    # Отключаем все SQL логи
    for logger_name in [
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.base.Engine",
        "sqlalchemy.dialects",
        "sqlalchemy.pool",
        "sqlalchemy.orm",
        "sqlalchemy.engine.Engine"
    ]:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = False
        logger.disabled = True
        logger.setLevel(logging.CRITICAL)

    # Отключаем стандартные логи FastAPI и uvicorn
    for logger_name in [
        "fastapi",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error"
    ]:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = False
        logger.disabled = True
        logger.setLevel(logging.CRITICAL)

    # Настройка логирования
    logger = logging.getLogger('game_server')
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Файловый обработчик
    file_handler = logging.FileHandler('game_server.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - [ИГРОВОЙ СЕРВЕР] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter('%(message)s'))

    file_handler.setLevel(logging.INFO)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 