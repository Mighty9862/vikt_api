import json
import random
import time
import asyncio

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.questions import QuestionSchema, QuestionReadSchema
from dependencies import get_game_service, get_user_service, get_question_service, get_answer_service, get_db
from services.users.UserService import UserService
from services.games.GameService import GameService
from services.answers.AnswerService import AnswerService
from services.questions.QuestionService import QuestionService

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

async def is_connection_active(websocket: WebSocket) -> bool:
    try:
        # Проверяем соединение через отправку пустого текстового сообщения
        await websocket.send_text("")
        return True
    except Exception as e:
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
        raise HTTPException(status_code=500, detail=f"Ошибка при запуске игры: {str(e)}")


@router.post("/admin/stop")
async def stop_game(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await service_game.stop_game()
    await _broadcast("clear_storage", service_game, service_user, service_answer)
    await _broadcast("Игра завершена администратором.", service_game, service_user, service_answer)
    return {"message": "Игра остановлена"}

@router.post("/admin/show_rating")
async def show_rating(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    # Сначала переключаем режим отображения
    await service_game.switch_display_mode("rating")
    # Сбрасываем кэш
    await invalidate_game_status_cache()
    # Отправляем обновление всем зрителям
    await _broadcast_spectators(service_game, service_user, service_answer)
    return {"message": "Рейтинг показан"}

@router.post("/admin/show_question")
async def show_question(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    # Сначала переключаем режим отображения
    await service_game.switch_display_mode("question")
    # Получаем текущий статус
    status = await service_game.get_all_status()
    # Сбрасываем кэш
    await invalidate_game_status_cache()
    # Отправляем обновление всем зрителям
    await _broadcast(
        status.current_question or "Ожидайте вопрос",
        service_game,
        service_user,
        service_answer
    )
    return {"message": "Вопрос показан"}

@router.post("/admin/show_answer")
async def update_answer_status(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    status = await service_game.get_all_status()
    await service_game.update_answer_status(True)
    await _broadcast(status.current_question or "Ожидайте вопрос", service_game, service_user, service_answer)
    return {"message": "Правильный ответ показан"}

@router.post("/admin/start_timer")
async def update_timer(
    service_game: GameService = Depends(get_game_service),
    service_user: UserService = Depends(get_user_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
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
        await _broadcast("Игра завершена!", service_game, service_user, service_answer)
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

        await _broadcast(question.question, service_game, service_user, service_answer)
        return {"message": "OK"}
    else:
        current_section_index += 1
        if current_section_index >= len(sections):
            await service_game.update_game_over(True)
            await _broadcast("Игра завершена!", service_game, service_user, service_answer)
            return {"message": "Все разделы пройдены"}

        await service_game.update_section_index(current_section_index)
        new_section = sections[current_section_index]
        if not await service_question.has_questions(new_section):
            await service_question.load_questions_to_redis(new_section)
        return await next_question(service_question, service_game, service_user, service_answer)

@router.websocket("/ws/player")
async def websocket_player(
    websocket: WebSocket,
    service_game: GameService = Depends(get_game_service),
    service_answer: AnswerService = Depends(get_answer_service)
):
    await websocket.accept()
    connection_id = id(websocket)
    player_name = None

    try:
        data = await websocket.receive_text()
        msg = json.loads(data)
        player_name = msg["name"]
        reconnect = msg.get("reconnect", False)

        if player_name in active_players:
            if reconnect:
                try:
                    old_ws = active_players[player_name]['ws']
                    await old_ws.close()
                except:
                    pass
            else:
                await websocket.close()
                return

        active_players[player_name] = {'ws': websocket, 'connection_id': connection_id}

        status = await service_game.get_all_status()
        initial_message = {
            "text": status.current_question or "Ожидайте вопрос",
            "timer": status.timer,
            "show_answer": status.show_answer
        }
        await websocket.send_json(initial_message)

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg['type'] == 'answer' and player_name not in answered_users:
                await service_answer.add_answer(
                    question=status.current_question,
                    username=player_name,
                    answer=msg['answer']
                )
                answered_users.add(player_name)

    except WebSocketDisconnect:
        if player_name and player_name in active_players:
            del active_players[player_name]
    except Exception as e:
        if player_name and player_name in active_players:
            del active_players[player_name]

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

        status = await get_cached_game_status(service_game)
        await _broadcast_spectators(service_game, service_user, service_answer, status)

        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
                spectator_last_activity[spectator_id] = datetime.now()
            except asyncio.TimeoutError:
                if not await is_connection_active(websocket):
                    raise WebSocketDisconnect()
                continue

    except WebSocketDisconnect:
        pass
    finally:
        if spectator_id in active_spectators:
            del active_spectators[spectator_id]
        if spectator_id in spectator_last_activity:
            del spectator_last_activity[spectator_id]

async def _broadcast(message: str, service_game, service_user, service_answer):
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

        broadcast_tasks = []

        for player_name, player_data in active_players.items():
            broadcast_tasks.append(
                asyncio.create_task(player_data['ws'].send_json(data_player))
            )

        broadcast_tasks.append(
            asyncio.create_task(
                _broadcast_spectators(service_game, service_user, service_answer, status)
            )
        )

        if broadcast_tasks:
            await asyncio.gather(*broadcast_tasks, return_exceptions=True)

    except Exception as e:
        raise

async def _broadcast_spectators(service_game, service_user, service_answer, status=None):
    if status is None:
        status = await get_cached_game_status(service_game)

    sections = await service_game.get_sections()
    current_section = sections[status.current_section_index]

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
                asyncio.create_task(spectator.send_text(json.dumps(message)))
            )
        except Exception as e:
            if spectator_id in active_spectators:
                del active_spectators[spectator_id]
            if spectator_id in spectator_last_activity:
                del spectator_last_activity[spectator_id]

    if broadcast_tasks:
        await asyncio.gather(*broadcast_tasks, return_exceptions=True)