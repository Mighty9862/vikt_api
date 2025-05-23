from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_answer_service, get_db
from services.answers.AnswerService import AnswerService

router = APIRouter(prefix="/answers", tags=["Answers"])

@router.post("/",
             summary="Добавление нового ответа",
             description="Добавляет новый ответ на вопрос и возвращает его")
async def add_answer(
    question: str,
    username: str,
    answer: str = None,
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        new_answer = await service.add_answer(question=question, username=username, answer=answer)
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

@router.get("/question/{question}",
            summary="Получение ответов по ID вопроса",
            description="Возвращает список ответов на конкретный вопрос")
async def get_answers_by_question_id(
    question: str,
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        answers = await service.get_answers_by_question_id(question=question)
        return answers
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/user/{username}",
            summary="Получение ответов по ID пользователя",
            description="Возвращает список ответов конкретного пользователя")
async def get_answers_by_user_id(
    username: str,
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        answers = await service.get_answers_by_user_id(username=username)
        return answers
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/question/{question}/user/{username}",
            summary="Получение ответов по ID вопроса и ID пользователя",
            description="Возвращает список ответов на конкретный вопрос от конкретного пользователя")
async def get_answers_by_question_and_user(
    question: str,
    username: str,
    service: AnswerService = Depends(get_answer_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        answers = await service.get_answers_by_question_and_user(question=question, username=username)
        return answers
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.post("/reset",
             summary="Обнуление таблицы answers",
             description="Удаляет все данные из таблицы answers и сбрасывает счетчик id")
async def reset_answers_table(
    service: AnswerService = Depends(get_answer_service)
) -> dict:
    try:
        result = await service.reset_answers_table()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))