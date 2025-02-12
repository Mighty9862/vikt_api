from ..base.base_repository import BaseRepository
from models import Answer
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions.exceptions import AnswerNotFoundException
from sqlalchemy import delete, select, text
from typing import List, Optional
from datetime import datetime

class AnswerRepository(BaseRepository[Answer]):
    model: Answer = Answer
    exception: AnswerNotFoundException = AnswerNotFoundException()

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=self.model, exception=self.exception)

    async def add_answer(self, question_id: int, user_id: Optional[int], answer: str) -> Answer:
        new_answer = Answer(
            question_id=question_id,
            user_id=user_id,
            answer=answer,
            answer_at=(datetime.now()).strftime("%H:%M:%S")
        )
        self.session.add(new_answer)
        await self.session.commit()
        return new_answer

    async def get_all_answers(self) -> List[Answer]:
        query = select(self.model)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        return res

    async def get_answers_by_question_id(self, question_id: int) -> List[Answer]:
        query = select(self.model).where(self.model.question_id == question_id)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        return res

    async def get_answers_by_user_id(self, user_id: int) -> List[Answer]:
        query = select(self.model).where(self.model.user_id == user_id)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        return res

    async def get_answers_by_question_and_user(self, question_id: int, user_id: int) -> List[Answer]:
        query = select(self.model).where(
            (self.model.question_id == question_id) & 
            (self.model.user_id == user_id)
        )
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        return res
    
    async def reset_table(self) -> dict:
        # Удаляем все записи из таблицы answers
        delete_query = delete(self.model)
        await self.session.execute(delete_query)

        # Сбрасываем последовательность id (для PostgreSQL)
        reset_sequence_query = text("ALTER SEQUENCE answers_id_seq RESTART WITH 1")
        await self.session.execute(reset_sequence_query)

        await self.session.commit()

        return {"message": "Таблица answers успешно обнулена"}