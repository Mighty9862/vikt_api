import json
import random
import time
import asyncio

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from config.logger import setup_logging
from config.monitoring import start_monitoring_task
from schemas.questions import QuestionSchema, QuestionReadSchema
from dependencies import get_game_service, get_user_service, get_question_service, get_answer_service, get_db
from services.users.UserService import UserService
from services.games.GameService import GameService
from services.answers.AnswerService import AnswerService 
from services.questions.QuestionService import QuestionService

#TODO: Слить ветку в мейн


# Настройка единого логгера
logger = setup_logging()

router = APIRouter(prefix="/websocket", tags=["WebSocket"])

answered_users = set()
active_players = {}       # {id: {'ws': WebSocket, 'name': str}}
active_spectators = {}    # {id: WebSocket}

# Добавим кэширование состояния игры
_game_status_cache = None
_game_status_cache_time = 0
CACHE_TIMEOUT = 1  # секунды

async def get_cached_game_status(service_game: GameService):
    global _game_status_cache, _game_status_cache_time
    current_time = time.time()
    
    if _game_status_cache is None or (current_time - _game_status_cache_time) > CACHE_TIMEOUT:
        _game_status_cache = await service_game.get_all_status()
        _game_status_cache_time = current_time
    
    return _game_status_cache

async def invalidate_game_status_cache():
    global _game_status_cache
    _game_status_cache = None

# Добавляем новую функцию для проверки активности соединения
async def is_connection_active(websocket: WebSocket) -> bool:
    try:
        # Добавляем таймаут в 5 секунд для ping-операции
        await asyncio.wait_for(websocket.ping(), timeout=5.0)
        return True
    except asyncio.TimeoutError:
        logger.warning("Таймаут WebSocket ping-запроса")
        return False
    except WebSocketDisconnect:
        logger.warning("WebSocket отключен во время ping-запроса")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка во время ping-запроса: {str(e)}")
        return False

@router.post("/",
             summary="Добавление нового ответа",
             description="Добавляет новый ответ на вопрос и возвращает его")
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

@router.post("/get_all_status",
             summary="Вывод текущего состояния",
             description="Добавляет новый ответ на вопрос и возвращает его")
async def get_all_status(service: AnswerService = Depends(get_game_service)):
    status = await service.get_all_status()
    return {"status": status}

@router.get("/admin/sections")
async def get_all_sections(service: GameService = Depends(get_game_service)):
    sections = await service.get_sections()
    return {"sections": sections}

@router.post("/admin/start")
async def start_game(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service),
    service_question: QuestionService = Depends(get_question_service)
):
    global answered_users
    answered_users = set()
    
    sections = await service_game.get_sections()
    for section in sections:
        if not await service_question.has_questions(section):
            await service_question.load_questions_to_redis(section)
    
    await service_game.start_game(0, True, False)
    await _broadcast("Игра начата! Ожидайте первый вопрос.", service_game, service_user, service_answer)
    return {"message": "Игра начата"}

@router.post("/admin/stop")
async def stop_game(service_game: GameService = Depends(get_game_service),
                      service_user: UserService = Depends(get_user_service),
                      service_answer: AnswerService = Depends(get_answer_service)):
    await service_game.stop_game()
    await _broadcast("clear_storage", service_game, service_user, service_answer)
    await _broadcast("Игра завершена администратором.", service_game, service_user, service_answer)
    return {"message": "Игра остановлена"}

@router.post("/admin/show_rating")
async def show_rating(service_game: GameService = Depends(get_game_service),
                      service_user: UserService = Depends(get_user_service),
                      service_answer: AnswerService = Depends(get_answer_service)):
    await service_game.switch_display_mode("rating")
    await _broadcast_spectators(service_game, service_user, service_answer)
    return {"message": "Рейтинг показан"}

@router.post("/admin/show_question")
async def show_question(service_game: GameService = Depends(get_game_service),
                        service_user: UserService = Depends(get_user_service),
                        service_answer: AnswerService = Depends(get_answer_service)):
    await service_game.switch_display_mode("question")
    await _broadcast_spectators(service_game, service_user, service_answer)
    return {"message": "Вопрос показан"}

@router.post("/admin/show_answer")
async def update_answer_status(service_game: GameService = Depends(get_game_service),
                        service_user: UserService = Depends(get_user_service),
                        service_answer: AnswerService = Depends(get_answer_service)):
    status = await service_game.get_all_status()

    await service_game.update_answer_status(True)
    await _broadcast(status.current_question or "Ожидайте вопрос", service_game, service_user, service_answer)
    return {"message": "Правильный ответ показан"}

@router.post("/admin/start_timer")
async def update_timer(service_game: GameService = Depends(get_game_service),
                        service_user: UserService = Depends(get_user_service),
                        service_answer: AnswerService = Depends(get_answer_service)):
    status = await service_game.get_all_status()

    await service_game.update_timer_status(True)
    await _broadcast(status.current_question or "Ожидайте вопрос", service_game, service_user, service_answer)
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

    async with AsyncSession() as session:
        async with session.begin():
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
                await _broadcast("Игра завершена!", service_game, service_user, service_answer)
                return {"message": "Все разделы пройдены"}

            current_section = sections[current_section_index]
            question = await service_question.get_random_question(current_section)
            
            if question:
                # Обновляем все данные за один запрос
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
                
                answered_users = set()
                await _broadcast(question.question, service_game, service_user, service_answer)
                execution_time = datetime.now() - start_time
                logger.info(f"""
                Question changed successfully:
                - Execution time: {execution_time.total_seconds()} seconds
                - Active players: {len(active_players)}
                - Section: {current_section}
                - Cache status: {'Hit' if _game_status_cache else 'Miss'}
                """)
                return {"message": "OK"}
            else:
                current_section_index += 1
                if current_section_index > 2:
                    return {"message": "Все вопросы пройдены. Игра завершена!"}
                await service_game.update_section_index(current_section_index)
                
                new_section = sections[current_section_index]
                if not await service_question.has_questions(new_section):
                    await service_question.load_questions_to_redis(new_section)

@router.post("/admin/next_section")
async def next_section(
    service_game: GameService = Depends(get_game_service),
    service_question: QuestionService = Depends(get_question_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):

    status = await service_game.get_all_status()
    if not status.game_started or status.game_over:
        raise HTTPException(status_code=400, detail="Игра не активна")

    sections = await service_game.get_sections()
    current_section_index = status.current_section_index

    current_section = sections[current_section_index]
    await service_question.clear_questions(current_section) 

    new_section_index = current_section_index + 1

    if new_section_index >= len(sections):
        await service_game.update_game_over(True)
        await _broadcast("Игра завершена!", service_game, service_user, service_answer)
        return {"message": "Все разделы пройдены"}

    await service_game.update_section_index(new_section_index)
    
    new_section = sections[new_section_index]

    if not await service_question.has_questions(new_section):
        await service_question.load_questions_to_redis(new_section)

    question = await service_question.get_random_question(new_section)
    if not question:
        raise HTTPException(status_code=404, detail="Нет вопросов в разделе")

    await service_game.update_current_question(
        current_question=question.question,
        answer_for_current_question=question.answer,
        current_question_image=question.question_image,
        current_answer_image=question.answer_image,
        timer_status=False,
        show_answer=False
    )

    global answered_users
    answered_users = set()

    await _broadcast(question.question, service_game, service_user, service_answer)
    return {"message": "Переход к разделу выполнен"}

@router.post("/admin/clear-redis")
async def clear_redis(
    service_question: QuestionService = Depends(get_question_service)
):
    result = await service_question.clear_redis()
    return result

async def _broadcast_spectators(service_game, service_user, service_answer, status):
    sections = await service_game.get_sections()
    current_section = sections[status.current_section_index]

    answer_for_current_question = status.answer_for_current_question
    current_question_image = status.current_question_image
    current_answer_image = status.current_answer_image
    timer = status.timer
    show_answer = status.show_answer

    if status.spectator_display_mode == "rating":
        players = await service_user.get_all_user()
        message = {
            "type": "rating",
            "players": players,
            "section": current_section
        }
        
    else:
        message = {
            "type": "question",
            "content": status.current_question or "Ожидайте следующий вопрос...",
            "section": current_section,
            "answer": answer_for_current_question,
            "question_image": current_question_image,
            "answer_image": current_answer_image,
            "timer": timer,
            "show_answer": show_answer
        }
    
    print(f"Display mode: {status.spectator_display_mode}")
    print(f"Message being sent: {message}")

    for spectator in active_spectators.values():
        try:
            await spectator.send_text(json.dumps(message))
        except:
            continue

async def _broadcast(message: str, service_game, service_user, service_answer):
    start_time = datetime.now()
    logger.info(f"Starting broadcast to {len(active_players)} players and {len(active_spectators)} spectators")
    
    try:
        status = await get_cached_game_status(service_game)
        sections = await service_game.get_sections()
        current_section = sections[status.current_section_index]

        data_player = {
            "text": message,
            "section": current_section,
            "answer": status.answer_for_current_question,
            "question_image": status.current_question_image,
            "answer_image": status.current_answer_image,
            "timer": status.timer,
            "show_answer": status.show_answer
        }

        # Отправляем сообщения всем игрокам асинхронно
        broadcast_tasks = []
        for player in active_players.values():
            broadcast_tasks.append(
                asyncio.create_task(
                    player['ws'].send_json(data_player)
                )
            )
        
        # Добавляем задачу для spectators
        broadcast_tasks.append(
            asyncio.create_task(
                _broadcast_spectators(service_game, service_user, service_answer, status=status)
            )
        )
        
        # Ждем завершения всех отправок
        await asyncio.gather(*broadcast_tasks, return_exceptions=True)
        
        broadcast_time = datetime.now() - start_time
        logger.info(f"""
        Broadcast completed:
        - Time taken: {broadcast_time.total_seconds()} seconds
        - Messages sent: {len(broadcast_tasks)}
        - Failed deliveries: {sum(1 for task in broadcast_tasks if task.exception() is not None)}
        """)
    except Exception as e:
        logger.error(f"Error in broadcast: {str(e)}", exc_info=True)
        raise

# Добавим функцию периодической очистки неактивных соединений
async def cleanup_inactive_connections():
    while True:
        for user_id, player in list(active_players.items()):
            if not await is_connection_active(player['ws']):
                del active_players[user_id]
                logger.info(f"🔴 Неактивный игрок удален. Осталось игроков: {len(active_players)}")
        
        for spectator_id, spectator in list(active_spectators.items()):
            if not await is_connection_active(spectator):
                del active_spectators[spectator_id]
                logger.info(f"🔴 Неактивный зритель удален")
        
        await asyncio.sleep(600)  # Проверка каждые 10 минут

# Модифицируем существующие WebSocket обработчики
@router.websocket("/ws/player")
async def websocket_player(websocket: WebSocket, service_game: GameService = Depends(get_game_service),
                           service_answer: AnswerService = Depends(get_answer_service)):
    cleanup_task = asyncio.create_task(cleanup_inactive_connections())
    start_time = datetime.now()
    await websocket.accept()
    user_id = id(websocket)
    
    logger.info(f"🟢 Новое подключение игрока. ID подключения: {user_id}")

    status = await service_game.get_all_status()
    sections = await service_game.get_sections()
    current_section = sections[status.current_section_index]
    try:
        data = await websocket.receive_text()
        name = json.loads(data)["name"]
        active_players[user_id] = {'ws': websocket, 'name': name}
        logger.info(f"👤 Игрок {name} присоединился к игре. Всего игроков: {len(active_players)}")

        initial_message = {
            "text": "Игра завершена" if status.game_over else \
                   "Ждите начала игры" if not status.game_started else \
                   status.current_question or "Ожидайте вопрос",
            "section": current_section,
            "answer": status.answer_for_current_question,
            "question_image": status.current_question_image,
            "answer_image": status.current_answer_image,
            "timer": status.timer,
            "show_answer": status.show_answer
        }
        await websocket.send_json(initial_message)

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg['type'] == 'answer' and user_id not in answered_users:
                logger.info(f"Player {name} submitted answer for question: {status.current_question}")
                response_time = datetime.now() - start_time
                logger.info(f"Response time for player {name}: {response_time.total_seconds()} seconds")
                
                await service_answer.add_answer(question=status.current_question, username=name, answer=msg['answer'])
                answered_users.add(user_id)

    except WebSocketDisconnect:
        if user_id in active_players:
            disconnected_player = active_players[user_id]['name']
            del active_players[user_id]
            logger.info(f"🔴 Игрок {disconnected_player} отключился. Осталось игроков: {len(active_players)}")
    finally:
        cleanup_task.cancel()


@router.websocket("/ws/spectator")
async def websocket_spectator(websocket: WebSocket, service_game: GameService = Depends(get_game_service),
                           service_user: UserService = Depends(get_user_service), service_answer: AnswerService = Depends(get_answer_service)):
    await websocket.accept()
    spectator_id = id(websocket)
    active_spectators[spectator_id] = websocket
    try:
        await _broadcast_spectators(service_game, service_user, service_answer, status=await service_game.get_all_status())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if spectator_id in active_spectators:
            del active_spectators[spectator_id]



    
