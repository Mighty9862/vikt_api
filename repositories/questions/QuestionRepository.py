from typing import List
from ..base.base_repository import BaseRepository
from models import Question
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions.exceptions import UserNotFoundException, UserNotExistsException, UserExistsException
from sqlalchemy import select, delete, text

class QuestionRepository(BaseRepository[Question]):
    model: Question = Question
    exception: UserNotFoundException = UserNotFoundException()

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=self.model, exception=self.exception)

    async def add_question_from_list(self, questions_data: list[dict]) -> Question:
        
        for question_data in questions_data:
            new_question = Question(
                question=question_data.get("question"),
                answer=question_data.get("answer"),
                section=question_data.get("section"),
                question_image=question_data.get("question_image"),
                answer_image=question_data.get("answer_image")

            )
            self.session.add(new_question)
        await self.session.commit()

        return {
            "ok": "Вопросы успешно добавлены"
        }
    
    async def get_all_question(self) -> list[Question]:
        query = select(self.model)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise "Fail"
        
        return res
    
    async def get_question_by_section(self, section: str) -> list[Question]:
        query = select(self.model).where(self.model.section == section)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise "Fail"
        
        return list(res)
    
    async def get_question_by_section_and_id(self, section: str, question_id: int) -> List[Question]:
        query = select(self.model).where(
            (self.model.section == section) & 
            (self.model.id == question_id)
        )
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        return res
    
    async def get_data_by_question(self, question: str) -> List[Question]:
        query = select(self.model).where(
            (self.model.question == question)
        )
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise self.exception
        
        return res
    
    async def reset_table(self):
        # Удаляем все записи из таблицы
        await self.session.execute(delete(self.model))
        
        # Если используется PostgreSQL, сбрасываем последовательность
        if self.session.bind.dialect.name == 'postgresql':
            await self.session.execute(text(f"ALTER SEQUENCE {self.model.__tablename__}_id_seq RESTART WITH 1"))
        
        await self.session.commit()

    async def delete_question(self, question: str) -> Question:
        # Сначала проверяем, существует ли пользователь
        query = select(self.model).where(self.model.question == question)
        stmt = await self.session.execute(query)
        question_data = stmt.scalars().first()

        if not question_data:
            raise self.exception

        # Выполняем запрос на удаление
        delete_query = delete(self.model).where(self.model.question == question)
        await self.session.execute(delete_query)
        await self.session.commit()

        return {
            "message": "Вопрос успешно удален"
        }
    
    
    