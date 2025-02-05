from fastapi import APIRouter, Depends, HTTPException
from services.questions.QuestionService import QuestionService
from schemas.questions import QuestionSchema, QuestionReadSchema
from typing import List
#from config.utils.auth import utils
from dependencies import get_question_service


router = APIRouter(prefix="/question", tags=["Question"])


@router.post("/add",
             summary="Добавление вопросов",
             description="Заполняет базу данных вопросами из списка.")
async def add_questions(
    questions: List[dict],
    service: QuestionService = Depends(get_question_service)
):
    await service.add_question(questions)
    return {"message": "Questions added successfully"}


@router.get("/",
        summary="Список всех вопросов",
        description="Возвращает список всех вопросов с полными данными")
async def index(
    service: QuestionService = Depends(get_question_service)
    
):
    return await service.get_all_question()

@router.get("/{chapter}",
        response_model=list[QuestionSchema],
        summary="Список всех вопросов из раздела",
        description="Возвращает список всех вопросов из раздела с полными данными")
async def index(
    chapter: str,
    service: QuestionService = Depends(get_question_service)
    
) -> list[QuestionSchema]:
    return await service.get_question_by_chapter(chapter=chapter)

@router.get("/{chapter}/{question_id}",
            summary="Получение вопросов по разделу и ID вопроса",
            description="Возвращает вопрос из раздела по конкретному id")
async def get_question_by_chapter_and_id(
    chapter: str,
    question_id: int,
    service: QuestionService = Depends(get_question_service),
):
    try:
        question = await service.get_question_by_chapter_and_id(chapter=chapter, question_id=question_id)
        return question
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

