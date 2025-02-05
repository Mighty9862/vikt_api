from ..base.base_repository import BaseRepository
from models import Question
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions.exceptions import UserNotFoundException, UserNotExistsException, UserExistsException
from sqlalchemy import select, delete

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
                chapter=question_data.get("chapter")
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
    
    async def get_question_by_chapter(self, chapter: str) -> list[Question]:
        query = select(self.model).where(self.model.chapter == chapter)
        stmt = await self.session.execute(query)
        res = stmt.scalars().all()

        if not res:
            raise "Fail"
        
        return list(res)
    
    
    