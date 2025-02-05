from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_answer_service, get_db
from schemas.answers import AnswerSchema  # Создайте схему для ответов
from services.answers.AnswerService import AnswerService

router = APIRouter(prefix="/answers", tags=["Answers"])

@router.post("/",
             summary="Добавление нового ответа",
             description="Добавляет новый ответ на вопрос и возвращает его")
async def add_answer(
    question_id: int,
    user_id: Optional[int] = None,
    answer: str = None,
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        new_answer = await service.add_answer(question_id=question_id, user_id=user_id, answer=answer)
        return new_answer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/",
            summary="Получение всех ответов",
            description="Возвращает список всех ответов")
async def get_all_answers(
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        answers = await service.get_all_answers()
        return answers
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/question/{question_id}",
            summary="Получение ответов по ID вопроса",
            description="Возвращает список ответов на конкретный вопрос")
async def get_answers_by_question_id(
    question_id: int,
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        answers = await service.get_answers_by_question_id(question_id=question_id)
        return answers
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/user/{user_id}",
            summary="Получение ответов по ID пользователя",
            description="Возвращает список ответов конкретного пользователя")
async def get_answers_by_user_id(
    user_id: int,
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        answers = await service.get_answers_by_user_id(user_id=user_id)
        return answers
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/question/{question_id}/user/{user_id}",
            summary="Получение ответов по ID вопроса и ID пользователя",
            description="Возвращает список ответов на конкретный вопрос от конкретного пользователя")
async def get_answers_by_question_and_user(
    question_id: int,
    user_id: int,
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        answers = await service.get_answers_by_question_and_user(question_id=question_id, user_id=user_id)
        return answers
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))