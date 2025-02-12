from json import JSONDecodeError
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from services.questions.QuestionService import QuestionService
from schemas.questions import QuestionSchema, QuestionReadSchema
from typing import List
#from config.utils.auth import utils
from dependencies import get_question_service


router = APIRouter(prefix="/websocket", tags=["WebSocket"])


active_users: dict[str, WebSocket] = {}

@router.websocket("/ws")
async def ws(
    websocket: WebSocket,
    service: QuestionService = Depends(get_question_service)
):
    await websocket.accept()
    username = await websocket.receive_text()
    active_users[username] = websocket
    
    for name, user_id in active_users.items():
        print(name)
    print(active_users.get(username))

    print(active_users.keys())

    
