import json
import random
import time
import asyncio

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.questions import QuestionSchema, QuestionReadSchema
from dependencies import get_game_service, get_user_service, get_question_service, get_answer_service, get_db, get_redis
from services.users.UserService import UserService
from services.games.GameService import GameService
from services.answers.AnswerService import AnswerService
from services.questions.QuestionService import QuestionService

from config.logger import setup_logging
from config.monitoring import start_monitoring_task

# Настройка единого логгера
logger = setup_logging()

router = APIRouter(prefix="/websocket", tags=["WebSocket"])

# Изменяем структуру хранения данных
active_players = {}  # {username: {'ws': WebSocket, 'connection_id': str}}
active_spectators = {}  # {id: WebSocket}
spectator_last_activity = {}  # {id: datetime}
answered_users = set()  # Теперь храним имена пользователей вместо ID

# Константы
INACTIVE_TIMEOUT = 10  # секунд
CLEANUP_INTERVAL = 5  # секунд

# Кэширование состояния игры
_game_status_cache = None
_game_status_cache_time = 0
CACHE_TIMEOUT = 1  # секунды

async def get_cached_game_status(service_game: GameService, force_update: bool = False):
    global _game_status_cache, _game_status_cache_time
    current_time = time.time()

    if force_update or _game_status_cache is None or (current_time - _game_status_cache_time) > CACHE_TIMEOUT:
        _game_status_cache = await service_game.get_all_status()
        _game_status_cache_time = current_time

    return _game_status_cache

async def invalidate_game_status_cache():
    global _game_status_cache
    _game_status_cache = None

async def is_connection_active(websocket: WebSocket) -> bool:
    try:
        # Проверяем соединение через отправку пустого текстового сообщения
        await websocket.send_text("")
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки соединения: {str(e)}")
        return False

# Admin endpoints
@router.post("/")
async def add_gamestatus(
    service: AnswerService = Depends(get_game_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        new_gamestatus = await service.add_gamestatus()
        return new_gamestatus
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/add_point/{player_name}")
async def add_point(player_name: str, service: UserService = Depends(get_user_service)):
    await service.add_score_to_user(username=player_name, points=1)
    return {"message": "OK"}

@router.post("/admin/remove_point/{player_name}")
async def remove_point(player_name: str, service: UserService = Depends(get_user_service)):
    await service.add_score_to_user(username=player_name, points=-1)
    return {"message": "OK"}

@router.post("/get_all_status")
async def get_all_status(service: AnswerService = Depends(get_game_service)):
    status = await service.get_all_status()
    return {"status": status}

@router.get("/admin/sections")
async def get_all_sections(service: GameService = Depends(get_game_service)):
    sections = await service.get_sections()
    return {"sections": sections}

@router.post("/admin/update_sections")
async def update_sections(
    sections: List[str],
    service: GameService = Depends(get_game_service)
):
    try:
        # Преобразуем список секций в строку, разделенную точками
        sections_string = ".".join(sections)
        await service.update_sections(sections_string)
        return {"message": "Разделы успешно обновлены", "sections": sections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении разделов: {str(e)}")

@router.post("/admin/start")
async def start_game(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service),
    service_question: QuestionService = Depends(get_question_service)
):
    try:
        global answered_users
        answered_users = set()

        sections = await service_game.get_sections()
        if not sections:
            raise HTTPException(status_code=400, detail="Нет доступных разделов")

        for section in sections:
            if not await service_question.has_questions(section):
                await service_question.load_questions_to_redis(section)

        await service_game.start_game(0, True, False)
        await _broadcast("Игра начата! Ожидайте первый вопрос.", service_game, service_user, service_answer)
        return {"message": "Игра начата"}

    except Exception as e:
        logger.error(f"Ошибка при запуске игры: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при запуске игры: {str(e)}")


@router.post("/admin/stop")
async def stop_game(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await service_game.stop_game()
    await broadcast_message(
        message_type="question",
        content="clear_storage",
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer
    )
    await broadcast_message(
        message_type="question",
        content="Игра завершена администратором.",
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer
    )
    return {"message": "Игра остановлена"}

@router.post("/admin/show_rating")
async def show_rating(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await service_game.switch_display_mode("rating")
    await broadcast_message(
        message_type="rating",
        content=None,  # контент будет получен внутри функции
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer,
        force_update=True
    )
    return {"message": "Рейтинг показан"}

@router.post("/admin/show_question")
async def show_question(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await service_game.switch_display_mode("question")
    await service_game.update_answer_status(False)
    
    status = await get_cached_game_status(service_game, force_update=True)
    await broadcast_message(
        message_type="question",
        content=status.current_question or "Ожидайте вопрос",
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer,
        force_update=True
    )
    return {"message": "Вопрос показан"}

@router.post("/admin/show_answer")
async def update_answer_status(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await service_game.update_answer_status(True)
    # Получаем обновленный статус через кэш
    status = await get_cached_game_status(service_game, force_update=True)
    await broadcast_message(
        message_type="question",
        content=status.current_question or "Ожидайте вопрос",
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer
    )
    return {"message": "Правильный ответ показан"}

@router.post("/admin/start_timer")
async def update_timer(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await service_game.update_timer_status(True)
    # Получаем обновленный статус через кэш
    status = await get_cached_game_status(service_game, force_update=True)
    await broadcast_message(
        message_type="question",
        content=status.current_question or "Ожидайте вопрос",
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer
    )
    return {"message": "Таймер запущен"}

@router.get("/admin/answers")
async def get_answers(service_answer: AnswerService = Depends(get_answer_service)):
    answers = await service_answer.get_all_answers()
    return {"answers": answers}

@router.post("/admin/reload-questions")
async def reload_questions(
    section: str,
    service_question: QuestionService = Depends(get_question_service)
):
    await service_question.load_questions_to_redis(section)
    return {"status": f"Questions for {section} reloaded"}

@router.post("/admin/next")
async def next_question(
    service_question: QuestionService = Depends(get_question_service),
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    logger.info("Starting next question procedure")
    start_time = datetime.now()

    global answered_users
    answered_users = set()  # Очищаем список ответивших

    status = await get_cached_game_status(service_game)
    if not status.game_started or status.game_over:
        return {"message": "Игра не активна"}

    sections = await service_game.get_sections()
    current_section_index = status.current_section_index

    if not sections:
        raise HTTPException(status_code=400, detail="Нет доступных разделов")

    if current_section_index >= len(sections):
        await service_game.update_game_over(True)
        await invalidate_game_status_cache()
        await broadcast_message(
            message_type="question",
            content="Игра завершена!",
            service_game=service_game,
            service_user=service_user,
            service_answer=service_answer
        )
        return {"message": "Все разделы пройдены"}

    current_section = sections[current_section_index]
    question = await service_question.get_random_question(current_section)

    if question:
        game_update = {
            "current_question": question.question,
            "answer_for_current_question": question.answer,
            "current_question_image": question.question_image,
            "current_answer_image": question.answer_image,
            "timer_status": False,
            "show_answer": False
        }
        await service_game.update_current_question(**game_update)
        await invalidate_game_status_cache()

        await broadcast_message(
            message_type="question",
            content=question.question,
            service_game=service_game,
            service_user=service_user,
            service_answer=service_answer
        )
        execution_time = datetime.now() - start_time
        logger.info(f"Question changed successfully in {execution_time.total_seconds()} seconds")
        return {"message": "OK"}
    else:
        current_section_index += 1
        if current_section_index >= len(sections):
            await service_game.update_game_over(True)
            await broadcast_message(
                message_type="question",
                content="Игра завершена!",
                service_game=service_game,
                service_user=service_user,
                service_answer=service_answer
            )
            return {"message": "Все разделы пройдены"}

        await service_game.update_section_index(current_section_index)
        new_section = sections[current_section_index]
        if not await service_question.has_questions(new_section):
            await service_question.load_questions_to_redis(new_section)
        return await next_question(service_question, service_game, service_user, service_answer)

@router.post("/admin/next-section")
async def next_section(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service),
    service_question: QuestionService = Depends(get_question_service)
):
    try:
        status = await get_cached_game_status(service_game)
        sections = await service_game.get_sections()
        current_section_index = status.current_section_index
        
        # Очищаем вопросы всех предыдущих секций и текущей секции из Redis
        redis = await anext(get_redis())
        for i in range(current_section_index + 1):
            section = sections[i]
            # Удаляем вопросы секции
            await redis.delete(f"questions:{section}")
            # Удаляем все ключи, связанные с этой секцией
            pattern = f"*{section}*"
            keys = await redis.keys(pattern)
            if keys:
                await redis.delete(*keys)
        
        # Переходим к следующей секции
        next_section_index = current_section_index + 1
        
        if next_section_index >= len(sections):
            # Если секции закончились
            await service_game.update_game_over(True)
            await broadcast_message(
                message_type="question",
                content="Игра завершена! Все разделы пройдены.",
                service_game=service_game,
                service_user=service_user,
                service_answer=service_answer
            )
            return {"message": "Все разделы пройдены"}
        
        # Обновляем индекс секции
        await service_game.update_section_index(next_section_index)
        new_section = sections[next_section_index]
        
        # Загружаем вопросы для новой секции
        if not await service_question.has_questions(new_section):
            await service_question.load_questions_to_redis(new_section)
        
        # Очищаем текущий вопрос
        await service_game.update_current_question(
            current_question=None,
            answer_for_current_question=None,
            current_question_image=None,
            current_answer_image=None,
            timer_status=False,
            show_answer=False
        )
        
        await broadcast_message(
            message_type="question",
            content=f"Переход к разделу: {new_section}",
            service_game=service_game,
            service_user=service_user,
            service_answer=service_answer
        )
        return {"message": f"Переход к разделу: {new_section}"}
        
    except Exception as e:
        logger.error(f"Ошибка при переключении секции: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Добавляем новую функцию для обработки отключений
async def handle_disconnect(connection_type: str, identifier: str | int, websocket: WebSocket):
    """
    Универсальная функция для обработки отключений websocket соединений
    
    Args:
        connection_type: тип соединения ("player" или "spectator")
        identifier: идентификатор соединения (имя игрока или ID зрителя)
        websocket: объект WebSocket
    """
    try:
        if connection_type == "player":
            if identifier in active_players:
                del active_players[identifier]
                logger.info(f"🔴 Игрок {identifier} отключился. Осталось игроков: {len(active_players)}")
        elif connection_type == "spectator":
            if identifier in active_spectators:
                del active_spectators[identifier]
            if identifier in spectator_last_activity:
                del spectator_last_activity[identifier]
            logger.info(f"🔴 Зритель {identifier} отключился. Осталось зрителей: {len(active_spectators)}")
        
        try:
            await websocket.close()
        except Exception:
            pass  # Игнорируем ошибки при закрытии сокета
            
    except Exception as e:
        logger.error(f"Ошибка при обработке отключения {connection_type} {identifier}: {str(e)}")

# Обновляем обработчик игрока
@router.websocket("/ws/player")
async def websocket_player(
    websocket: WebSocket,
    service_game: GameService = Depends(get_game_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await websocket.accept()
    connection_id = id(websocket)
    player_name = None

    logger.info(f"🟢 Новое подключение игрока. ID подключения: {connection_id}")

    try:
        data = await websocket.receive_text()
        msg = json.loads(data)
        player_name = msg["name"]
        reconnect = msg.get("reconnect", False)

        if player_name in active_players:
            if reconnect:
                # Используем новую функцию для закрытия старого соединения
                await handle_disconnect("player", player_name, active_players[player_name]['ws'])
                logger.info(f"🔄 Игрок {player_name} переподключился")
            else:
                await websocket.close()
                logger.warning(f"❌ Попытка дублирования игрока {player_name}")
                return

        active_players[player_name] = {'ws': websocket, 'connection_id': connection_id}
        logger.info(f"👤 Игрок {player_name} присоединился к игре. Всего игроков: {len(active_players)}")

        # Используем кэшированный статус вместо прямого запроса
        status = await get_cached_game_status(service_game)
        initial_message = {
            "type": "question",
            "content": status.current_question or "Ожидайте вопрос",
            "timer": status.timer,
            "show_answer": status.show_answer
        }
        await websocket.send_json(initial_message)

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if player_name not in answered_users:
                logger.info(f"Получен ответ от игрока {player_name}")
                # Получаем свежий статус для ответа
                status = await get_cached_game_status(service_game, force_update=True)
                await service_answer.add_answer(
                    question=status.current_question,
                    username=player_name,
                    answer=msg['answer']
                )
                answered_users.add(player_name)

    except WebSocketDisconnect:
        if player_name:
            await handle_disconnect("player", player_name, websocket)
    except Exception as e:
        logger.error(f"Ошибка в websocket_player: {str(e)}")
        if player_name:
            await handle_disconnect("player", player_name, websocket)

# Обновляем обработчик зрителя
@router.websocket("/ws/spectator")
async def websocket_spectator(
    websocket: WebSocket,
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await websocket.accept()
    spectator_id = id(websocket)

    try:
        active_spectators[spectator_id] = websocket
        spectator_last_activity[spectator_id] = datetime.now()

        logger.info(f"🟢 Новое подключение зрителя: ID: {spectator_id}, Всего зрителей: {len(active_spectators)}")

        # Сразу отправляем текущее состояние
        status = await get_cached_game_status(service_game)
        await _broadcast_spectators(service_game, service_user, service_answer, status)

        while True:
            try:
                # Ждем сообщения от клиента для поддержания соединения
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
                spectator_last_activity[spectator_id] = datetime.now()
            except asyncio.TimeoutError:
                # Проверяем соединение
                if not await is_connection_active(websocket):
                    logger.warning(f"🔴 Зритель {spectator_id} неактивен, закрываем соединение")
                    raise WebSocketDisconnect()
                continue

    except WebSocketDisconnect:
        await handle_disconnect("spectator", spectator_id, websocket)
    except Exception as e:
        logger.error(f"Ошибка в websocket_spectator: {str(e)}")
        await handle_disconnect("spectator", spectator_id, websocket)

async def _broadcast(message: str, service_game, service_user, service_answer):
    start_time = datetime.now()
    logger.info(f"""
    🔄 Начало рассылки сообщения:
    - Активных игроков: {len(active_players)}
    - Активных зрителей: {len(active_spectators)}
    - Время начала: {start_time.strftime('%H:%M:%S.%f')}
    """)

    try:
        status = await get_cached_game_status(service_game)
        sections = await service_game.get_sections()
        current_section = sections[status.current_section_index]

        # Унифицированный формат сообщений для всех клиентов
        common_message = {
            "type": "question",  # Добавляем тип для всех сообщений
            "content": message,   # Используем content вместо text
            "section": current_section,
            "answer": status.answer_for_current_question,
            "question_image": status.current_question_image,
            "answer_image": status.current_answer_image,
            "timer": status.timer,
            "show_answer": status.show_answer
        }

        broadcast_tasks = []

        # Отправка игрокам (теперь тот же формат)
        for player_name, player_data in active_players.items():
            broadcast_tasks.append(
                asyncio.create_task(player_data['ws'].send_json(common_message))
            )
            logger.debug(f"➡️ Добавлена задача отправки для игрока: {player_name}")

        # Отправка зрителям (используем тот же объект сообщения)
        broadcast_tasks.append(
            asyncio.create_task(
                _broadcast_spectators(service_game, service_user, service_answer, status, common_message)
            )
        )

        if broadcast_tasks:
            await asyncio.gather(*broadcast_tasks, return_exceptions=True)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        logger.info(f"""
        ✅ Рассылка завершена:
        - Время окончания: {end_time.strftime('%H:%M:%S.%f')}
        - Длительность: {execution_time:.3f} секунд
        - Отправлено сообщений: {len(broadcast_tasks)}
        """)

    except Exception as e:
        logger.error(f"""
        ❌ Ошибка при рассылке:
        - Время: {datetime.now().strftime('%H:%M:%S.%f')}
        - Ошибка: {str(e)}
        """, exc_info=True)
        raise

async def _broadcast_spectators(service_game, service_user, service_answer, status=None, common_message=None):
    if status is None:
        status = await get_cached_game_status(service_game)

    sections = await service_game.get_sections()
    current_section = sections[status.current_section_index]

    if status.spectator_display_mode == "rating":
        players = await service_user.get_all_user()
        message = {
            "type": "rating",
            "content": players,
            "section": current_section
        }
    else:
        message = common_message or {
            "type": "question",
            "content": status.current_question or "Ожидайте следующий вопрос...",
            "section": current_section,
            "answer": status.answer_for_current_question,
            "question_image": status.current_question_image,
            "answer_image": status.current_answer_image,
            "timer": status.timer,
            "show_answer": status.show_answer
        }

    broadcast_tasks = []
    for spectator_id, spectator in list(active_spectators.items()):
        try:
            broadcast_tasks.append(
                asyncio.create_task(spectator.send_json(message))
            )
            logger.debug(f"➡️ Добавлена задача отправки для зрителя ID: {spectator_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке зрителю {spectator_id}: {str(e)}")
            await handle_disconnect("spectator", spectator_id, spectator)

    if broadcast_tasks:
        await asyncio.gather(*broadcast_tasks, return_exceptions=True)


@router.post("/admin/clear-redis")
async def clear_redis(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    redis = await anext(get_redis())
    
    # Очищаем весь Redis
    await redis.flushall()
    
    # Останавливаем игру
    await service_game.stop_game()
    
    # Оповещаем всех подключенных клиентов
    await broadcast_message(
        message_type="question",
        content="Игра сброшена",
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer
    )
    
    return {"message": "Redis очищен, игра сброшена"}

# Добавляем новую функцию для унифицированной рассылки
async def broadcast_message(
    message_type: str,  # "question" или "rating"
    content: any,
    service_game: GameService,
    service_user: UserService,
    service_answer: AnswerService,
    force_update: bool = False
):
    """
    Универсальная функция для рассылки сообщений всем клиентам
    
    Args:
        message_type: тип сообщения ("question" или "rating")
        content: содержимое сообщения
        service_game: сервис игры
        service_user: сервис пользователей
        service_answer: сервис ответов
        force_update: принудительное обновление кэша
    """
    start_time = datetime.now()
    logger.info(f"""
    🔄 Начало рассылки сообщения:
    - Тип: {message_type}
    - Активных игроков: {len(active_players)}
    - Активных зрителей: {len(active_spectators)}
    - Время начала: {start_time.strftime('%H:%M:%S.%f')}
    """)

    try:
        status = await get_cached_game_status(service_game, force_update)
        sections = await service_game.get_sections()
        current_section = sections[status.current_section_index]

        broadcast_tasks = []

        if message_type == "question":
            # Формируем сообщение для вопроса
            message = {
                "type": "question",
                "content": content,
                "section": current_section,
                "answer": status.answer_for_current_question,
                "question_image": status.current_question_image,
                "answer_image": status.current_answer_image,
                "timer": status.timer,
                "show_answer": status.show_answer
            }

            # Отправляем всем игрокам
            for player_name, player_data in active_players.items():
                broadcast_tasks.append(
                    asyncio.create_task(player_data['ws'].send_json(message))
                )
                logger.debug(f"➡️ Добавлена задача отправки для игрока: {player_name}")

        elif message_type == "rating":
            # Для рейтинга получаем список игроков
            players = await service_user.get_all_user()
            message = {
                "type": "rating",
                "content": players,
                "section": current_section
            }

        # Отправляем зрителям
        for spectator_id, spectator in list(active_spectators.items()):
            try:
                broadcast_tasks.append(
                    asyncio.create_task(spectator.send_json(message))
                )
                logger.debug(f"➡️ Добавлена задача отправки для зрителя ID: {spectator_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке зрителю {spectator_id}: {str(e)}")
                await handle_disconnect("spectator", spectator_id, spectator)

        if broadcast_tasks:
            await asyncio.gather(*broadcast_tasks, return_exceptions=True)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        logger.info(f"""
        ✅ Рассылка завершена:
        - Время окончания: {end_time.strftime('%H:%M:%S.%f')}
        - Длительность: {execution_time:.3f} секунд
        - Отправлено сообщений: {len(broadcast_tasks)}
        """)

    except Exception as e:
        logger.error(f"""
        ❌ Ошибка при рассылке:
        - Время: {datetime.now().strftime('%H:%M:%S.%f')}
        - Ошибка: {str(e)}
        """, exc_info=True)
        raise