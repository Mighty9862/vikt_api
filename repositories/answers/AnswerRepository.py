from ..base.base_repository import BaseRepository
from models import Answer
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions.exceptions import AnswerNotFoundException
from sqlalchemy import delete, select, text
from typing import List, Optional
from datetime import datetime
import pytz

class AnswerRepository(BaseRepository[Answer]):
    model: Answer = Answer
    exception: AnswerNotFoundException = AnswerNotFoundException()

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=self.model, exception=self.exception)

    async def add_answer(self, question: str, username: str, answer: str) -> Answer:
        moscow_tz = pytz.timezone('Europe/Moscow')
        moscow_time = datetime.now(moscow_tz)

        new_answer = Answer(
            question=question,
            username=username,
            answer=answer,
            answer_at=moscow_time.strftime("%H:%M:%S")
        )
        self.session.add(new_answer)
        await self.session.commit()
        await self.session.close()
        return new_answer

    async def get_all_answers(self) -> List[Answer]:
        query = select(self.model)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        await self.session.close()
        return res

    async def get_answers_by_question_id(self, question: str) -> List[Answer]:
        query = select(self.model).where(self.model.question == question)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()
        
        await self.session.close()
        return res

    async def get_answers_by_user_id(self, username: str) -> List[Answer]:
        query = select(self.model).where(self.model.username == username)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        await self.session.close()
        return res

    async def get_answers_by_question_and_user(self, question: str, username: str) -> List[Answer]:
        query = select(self.model).where(
            (self.model.question == question) & 
            (self.model.username == username)
        )
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        await self.session.close()
        return res
    
    async def reset_table(self) -> dict:
        # Удаляем все записи из таблицы answers
        delete_query = delete(self.model)
        await self.session.execute(delete_query)

        # Сбрасываем последовательность id (для PostgreSQL)
        reset_sequence_query = text("ALTER SEQUENCE answers_id_seq RESTART WITH 1")
        await self.session.execute(reset_sequence_query)

        await self.session.commit()
        await self.session.close()
        
        return {"message": "Таблица answers успешно обнулена"}