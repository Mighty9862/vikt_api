from fastapi import APIRouter, Depends, HTTPException
from services.questions.QuestionService import QuestionService
from schemas.questions import QuestionSchema
from typing import List
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


@router.get("/get_info_question",
            summary="Получение информации по вопросу",
            description="Возвращает информацию по вопросу")
async def get_data_by_question(
    question: str,
    service: QuestionService = Depends(get_question_service),
):
    try:
        question_info = await service.get_data_by_question(question=question)
        return question_info
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{section}",
        response_model=list[QuestionSchema],
        summary="Список всех вопросов из раздела",
        description="Возвращает список всех вопросов из раздела с полными данными")
async def index(
    section: str,
    service: QuestionService = Depends(get_question_service)
    
) -> list[QuestionSchema]:
    return await service.get_question_by_section(section=section)

@router.get("/{section}/{question_id}",
            summary="Получение вопросов по разделу и ID вопроса",
            description="Возвращает вопрос из раздела по конкретному id")
async def get_question_by_section_and_id(
    section: str,
    question_id: int,
    service: QuestionService = Depends(get_question_service),
):
    try:
        question = await service.get_question_by_section_and_id(section=section, question_id=question_id)
        return question
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/reset",
             summary="Сброс таблицы вопросов",
             description="Полностью очищает таблицу вопросов и сбрасывает счетчик ID.")
async def reset_question_table(
    service: QuestionService = Depends(get_question_service)
):
    await service.reset_question_table()
    return {"message": "Question table has been reset successfully"}
