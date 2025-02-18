import time
import logging
import psutil
import os
import colorama
from colorama import Fore, Style
from config.logger import setup_logging
import asyncio

# Инициализация colorama для Windows
colorama.init()

# Настройка логирования
class ColoredFormatter(logging.Formatter):
    """Форматтер для цветных логов"""
    
    def format(self, record):
        # Добавляем цветовую маркировку для разных уровней логирования
        if record.levelno >= logging.ERROR:
            color = Fore.RED
        elif record.levelno >= logging.WARNING:
            color = Fore.YELLOW
        elif record.levelno >= logging.INFO:
            # Особая обработка для FastAPI логов
            if 'fastapi' in record.name:
                if "GET" in str(record.msg) or "POST" in str(record.msg):
                    color = Fore.MAGENTA  # Выделяем HTTP запросы магентой
                else:
                    color = Fore.BLUE     # Остальные логи FastAPI синим
            else:
                color = Fore.CYAN
        else:
            color = Fore.GREEN
            
        # Добавляем префикс в зависимости от источника лога
        if 'fastapi' in record.name:
            record.msg = f"{color}[API] {record.msg}{Style.RESET_ALL}"
        else:
            record.msg = f"{color}[ИГРОВОЙ СЕРВЕР] {record.msg}{Style.RESET_ALL}"
        return super().format(record)

async def start_monitoring_task():
    """Запуск периодического мониторинга"""
    logger = logging.getLogger("МОНИТОРИНГ")
    
    while True:
        try:
            stats = await get_system_stats()
            from presentation.websockets.WebSocketRouter import active_players, active_spectators
            
            # Проверяем, что переменные существуют и инициализированы
            player_count = len(active_players) if active_players is not None else 0
            spectator_count = len(active_spectators) if active_spectators is not None else 0
            total_connections = player_count + spectator_count
            
            logger.info(f"""
                        ============= СТАТИСТИКА СЕРВЕРА =============
Активные игроки: {player_count}
Активные зрители: {spectator_count}
Всего WebSocket подключений: {total_connections}

Системные ресурсы:
    ├── Загрузка ЦП: {stats['cpu_percent']}%
    ├── Использование памяти: {stats['memory_percent']}%
    ├── Активные потоки: {stats['active_threads']}
    └── Открытые файлы: {stats['open_files']}

Сетевые подключения:
    ├── Установленные: {stats['connections_detail']['ESTABLISHED']} (активные WebSocket и HTTP соединения)
    ├── Прослушивание: {stats['connections_detail']['LISTEN']} (открытые порты сервера)
    ├── Ожидание закрытия: {stats['connections_detail']['TIME_WAIT']} (соединения в процессе корректного закрытия)
    ├── Ожидание закрытия клиентом: {stats['connections_detail']['CLOSE_WAIT']} (соединения, ожидающие закрытия со стороны клиента)
    └── Прочие: {stats['connections_detail']['OTHER']} (соединения в других состояниях TCP)

Всего сетевых подключений: {stats['active_connections']}
=============================================""")
        except ImportError as e:
            logger.error(f"Ошибка импорта WebSocket переменных: {e}")
        except Exception as e:
            logger.error(f"Ошибка при сборе статистики: {e}")
        await asyncio.sleep(60)

def setup_monitoring(logger=None):
    if logger is None:
        logger = setup_logging()
        
    # Настраиваем форматтер для мониторинга
    formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Создаем handler для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Настраиваем логгер мониторинга
    monitoring_logger = logging.getLogger("МОНИТОРИНГ")
    monitoring_logger.setLevel(logging.INFO)
    monitoring_logger.addHandler(console_handler)
    
    # Отключаем все SQL логи полностью
    logging.getLogger("sqlalchemy").handlers = []
    logging.getLogger("sqlalchemy").propagate = False
    logging.getLogger("sqlalchemy.engine").handlers = []
    logging.getLogger("sqlalchemy.engine").propagate = False

    # Более агрессивное отключение для всех компонентов SQLAlchemy
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
    
    return logger

async def get_system_stats():
    """Функция для получения статистики системы"""
    process = psutil.Process(os.getpid())
    connections = process.connections()
    
    connections_detail = {
        'ESTABLISHED': 0,
        'LISTEN': 0,
        'TIME_WAIT': 0,
        'CLOSE_WAIT': 0,
        'OTHER': 0
    }
    
    for conn in connections:
        status = conn.status
        if status in connections_detail:
            connections_detail[status] += 1
        else:
            connections_detail['OTHER'] += 1
    
    return {
        'cpu_percent': process.cpu_percent(),
        'memory_percent': process.memory_percent(),
        'active_threads': process.num_threads(),
        'open_files': len(process.open_files()),
        'active_connections': len(connections),
        'connections_detail': connections_detail
    }

async def start_monitoring():
    """Асинхронная функция для запуска мониторинга"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 Инициализация мониторинга")  # Лог при инициализации
    asyncio.create_task(start_monitoring_task())

    

"""
Описание логирования в мониторинге:

1. Статистика подключений:
- Активные игроки - количество подключенных WebSocket игроков
- Активные зрители - количество подключенных WebSocket зрителей  
- Всего WebSocket подключений - сумма игроков и зрителей

2. Системные ресурсы:
- Загрузка ЦП - процент использования процессора текущим процессом
- Использование памяти - процент использования RAM текущим процессом
- Активные потоки - количество активных потоков в процессе
- Открытые файлы - количество открытых файловых дескрипторов

3. Сетевые подключения:
- ESTABLISHED - активные соединения (WebSocket и текущие HTTP запросы)
- LISTEN - открытые порты сервера
- TIME_WAIT - соединения в процессе закрытия (обычно завершенные HTTP запросы)
- CLOSE_WAIT - соединения, ожидающие закрытия клиентом
- OTHER - прочие состояния TCP соединений

Цветовая схема логов:
- Красный (RED) - ошибки (ERROR)
- Желтый (YELLOW) - предупреждения (WARNING) 
- Пурпурный (MAGENTA) - HTTP запросы FastAPI
- Синий (BLUE) - прочие логи FastAPI
- Голубой (CYAN) - информационные сообщения (INFO)
- Зеленый (GREEN) - отладочные сообщения (DEBUG)

Префиксы логов:
[API] - для логов FastAPI
[ИГРОВОЙ СЕРВЕР] - для остальных логов

Отключены логи:
- SQLAlchemy (все компоненты)
- FastAPI (стандартные)
- Uvicorn (access и error)
""" 