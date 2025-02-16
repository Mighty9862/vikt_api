import json
from typing import List, Optional
from ..base.base_repository import BaseRepository
from models import Question
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions.exceptions import UserNotFoundException, UserNotExistsException, UserExistsException
from sqlalchemy import select, delete, text
from schemas.questions import QuestionSchema

from redis.asyncio import Redis

class QuestionRepository(BaseRepository[Question]):
    model: Question = Question
    exception: UserNotFoundException = UserNotFoundException()

    def __init__(self, session: AsyncSession, redis: Redis):
        self.redis = redis
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
            return False
        
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
    
    async def load_questions_to_redis(self, section: str):
        # Удаляем старые вопросы перед загрузкой новых
        await self.redis.delete(section)
        
        # Получаем вопросы из базы данных
        query = select(self.model).where(self.model.section == section)
        result = await self.session.execute(query)
        questions = result.scalars().all()
        
        # Сериализуем и загружаем в Redis
        for question in questions:
            question_data = QuestionSchema.from_orm(question).dict()
            # Сохраняем данные в Redis
            await self.redis.sadd(section, json.dumps(question_data, ensure_ascii=False))

    # Пример получения данных из Redis
    async def get_random_question(self, section: str) -> Optional[QuestionSchema]:
        question_json = await self.redis.spop(section)
        if question_json:
            # Декодируем данные из байтового формата
            return QuestionSchema(**json.loads(question_json.decode('utf-8')))
        return None

    async def has_questions(self, section: str) -> bool:
        return await self.redis.scard(section) > 0 
    
    async def clear_questions(self, section: str):
        await self.redis.delete(f"questions:{section}")

    async def clear_redis(self):
        try:
            await self.redis.flushall()
            return {"message": "Redis успешно очищен"}
        except Exception as e:
            return {"error": f"Ошибка при очистке Redis: {str(e)}"}
        
    