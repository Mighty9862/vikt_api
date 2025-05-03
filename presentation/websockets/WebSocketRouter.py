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

logger = setup_logging()

router = APIRouter(prefix="/websocket", tags=["WebSocket"])

active_players = {}  # {username: {'ws': WebSocket, 'connection_id': str}}
active_spectators = {}  # {id: WebSocket}
spectator_last_activity = {}  # {id: datetime}
answered_users = set()  

INACTIVE_TIMEOUT = 10
CLEANUP_INTERVAL = 5

_game_status_cache = None
_game_status_cache_time = 0
CACHE_TIMEOUT = 1

_sections_cache = None
_sections_cache_time = 0
SECTIONS_CACHE_TIMEOUT = 60

_rating_cache = None
_rating_cache_time = 0
RATING_CACHE_TIMEOUT = 5

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
        await websocket.send_text("")
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки соединения: {str(e)}")
        return False

async def get_cached_sections(service_game: GameService, force_update: bool = False):
    global _sections_cache, _sections_cache_time
    current_time = time.time()
    
    if force_update or _sections_cache is None or (current_time - _sections_cache_time) > SECTIONS_CACHE_TIMEOUT:
        _sections_cache = await service_game.get_sections()
        _sections_cache_time = current_time
        
    return _sections_cache

async def get_cached_rating(service_user: UserService, force_update: bool = False):
    global _rating_cache, _rating_cache_time
    current_time = time.time()
    
    if force_update or _rating_cache is None or (current_time - _rating_cache_time) > RATING_CACHE_TIMEOUT:
        _rating_cache = await service_user.get_all_user()
        _rating_cache_time = current_time
        
    return _rating_cache

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
    
        first_section = sections[0]
        section_message = f"Раунд 1: {first_section}"
        
        await broadcast_message(
            message_type="question",
            content=section_message,
            service_game=service_game,
            service_user=service_user,
            service_answer=service_answer
        )
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
        content=None,
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
async def start_timer(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    """Запускает таймер на 40 секунд"""
    await service_game.update_timer_status(True)
    status = await get_cached_game_status(service_game, force_update=True)
    await broadcast_message(
        message_type="question",
        content=status.current_question or "Ожидайте вопрос",
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer
    )
    return {"message": "Таймер запущен на 40 секунд"}


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
    answered_users = set()

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
    if status.current_question is None:
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
            logger.info(f"First question of section shown in {execution_time.total_seconds()} seconds")
            return {"message": "Первый вопрос раздела показан"}
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

            await service_game.update_current_question(
                current_question=None,
                answer_for_current_question=None,
                current_question_image="None",
                current_answer_image="None",
                timer_status=False,
                show_answer=False
            )

            await service_game.update_timer_status(False)

            section_message = f"Раунд {current_section_index + 1}: {new_section}"
            await broadcast_message(
                message_type="question",
                content=section_message,
                service_game=service_game,
                service_user=service_user,
                service_answer=service_answer
            )
            
            return {"message": f"Переход к разделу: {new_section}"}
    else:
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
                
            await service_game.update_current_question(
                current_question=None,
                answer_for_current_question=None,
                current_question_image="None",
                current_answer_image="None",
                timer_status=False,
                show_answer=False
            )
            
            await service_game.update_timer_status(False)
            
            section_message = f"Раунд {current_section_index + 1}: {new_section}"
            await broadcast_message(
                message_type="question",
                content=section_message,
                service_game=service_game,
                service_user=service_user,
                service_answer=service_answer
            )
            
            return {"message": f"Переход к разделу: {new_section}"}

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
        
        redis = await anext(get_redis())
        for i in range(current_section_index + 1):
            section = sections[i]
            await redis.delete(f"questions:{section}")
            pattern = f"*{section}*"
            keys = await redis.keys(pattern)
            if keys:
                await redis.delete(*keys)
        
        next_section_index = current_section_index + 1
        
        if next_section_index >= len(sections):
            await service_game.update_game_over(True)
            await broadcast_message(
                message_type="question",
                content="Игра завершена! Все разделы пройдены.",
                service_game=service_game,
                service_user=service_user,
                service_answer=service_answer
            )
            return {"message": "Все разделы пройдены"}
        
        await service_game.update_section_index(next_section_index)
        new_section = sections[next_section_index]
        
        if not await service_question.has_questions(new_section):
            await service_question.load_questions_to_redis(new_section)
        
        await service_game.update_current_question(
            current_question=None,
            answer_for_current_question=None,
            current_question_image="None",
            current_answer_image="None",
            timer_status=False,
            show_answer=False
        )
        
        await service_game.update_timer_status(False)
        
        section_message = f"Раунд {next_section_index + 1}: {new_section}"
        
        await broadcast_message(
            message_type="question",
            content=section_message,
            service_game=service_game,
            service_user=service_user,
            service_answer=service_answer
        )
        return {"message": f"Переход к разделу: {new_section}"}
        
    except Exception as e:
        logger.error(f"Ошибка при переключении секции: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_disconnect(connection_type: str, identifier: str | int, websocket: WebSocket):
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
            pass
            
    except Exception as e:
        logger.error(f"Ошибка при обработке отключения {connection_type} {identifier}: {str(e)}")

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
                await handle_disconnect("player", player_name, active_players[player_name]['ws'])
                logger.info(f"🔄 Игрок {player_name} переподключился")
            else:
                await websocket.close()
                logger.warning(f"❌ Попытка дублирования игрока {player_name}")
                return

        active_players[player_name] = {'ws': websocket, 'connection_id': connection_id}
        logger.info(f"👤 Игрок {player_name} присоединился к игре. Всего игроков: {len(active_players)}")

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
        status = await get_cached_game_status(service_game)
        
        message_type = "rating" if status.spectator_display_mode == "rating" else "question"
        content = None if message_type == "rating" else (status.current_question or "Ожидайте следующий вопрос...")
        
        temp_spectators = {spectator_id: websocket}
        original_spectators = active_spectators.copy()
        
        try:
            active_spectators.clear()
            active_spectators.update(temp_spectators)

            await broadcast_message(
                message_type=message_type,
                content=content,
                service_game=service_game,
                service_user=service_user,
                service_answer=service_answer,
                force_update=False
            )
        finally:
            active_spectators.clear()
            active_spectators.update(original_spectators)

        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
                spectator_last_activity[spectator_id] = datetime.now()
            except asyncio.TimeoutError:
                if not await is_connection_active(websocket):
                    logger.warning(f"🔴 Зритель {spectator_id} неактивен, закрываем соединение")
                    raise WebSocketDisconnect()
                continue

    except WebSocketDisconnect:
        await handle_disconnect("spectator", spectator_id, websocket)
    except Exception as e:
        logger.error(f"Ошибка в websocket_spectator: {str(e)}")
        await handle_disconnect("spectator", spectator_id, websocket)
        
async def broadcast_message(
    message_type: str,  # "question" или "rating"
    content: any,
    service_game: GameService,
    service_user: UserService,
    service_answer: AnswerService,
    force_update: bool = False
):
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
        sections = await get_cached_sections(service_game, force_update)
        current_section = sections[status.current_section_index]

        broadcast_tasks = []

        if message_type == "question":
            is_section_header = isinstance(content, str) and content.startswith("Раунд ")
            is_waiting_message = content in ["Ожидайте вопрос", "Ожидайте следующий вопрос...", "Игра завершена!", "Игра сброшена"]
            
            message = {
                "type": "question",
                "content": content,
                "section": current_section,
                "answer": status.answer_for_current_question,
                "question_image": status.current_question_image,
                "answer_image": status.current_answer_image,
                "timer": False if (is_section_header or is_waiting_message) else status.timer,
                "show_answer": status.show_answer
            }

            for player_name, player_data in active_players.items():
                broadcast_tasks.append(
                    asyncio.create_task(player_data['ws'].send_json(message))
                )
                logger.debug(f"➡️ Добавлена задача отправки для игрока: {player_name}")

        elif message_type == "rating":
            players = await get_cached_rating(service_user, force_update)
            message = {
                "type": "rating",
                "content": players,
                "section": current_section
            }

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

@router.post("/admin/clear-redis")
async def clear_redis(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    redis = await anext(get_redis())
    
    await redis.flushall()
    await service_game.stop_game()
    
    await broadcast_message(
        message_type="question",
        content="Игра сброшена",
        service_game=service_game,
        service_user=service_user,
        service_answer=service_answer
    )
    
    return {"message": "Redis очищен, игра сброшена"}