from repositories.questions.QuestionRepository import QuestionRepository
from schemas.users import UserLoginSchema
from werkzeug.security import generate_password_hash, check_password_hash
#from .exceptions.exceptions import IncorrectPasswordException

class QuestionService:

    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def add_question(self, questions_data: list[dict]):
        return await self.repository.add_question_from_list(questions_data=questions_data)
    
    async def get_all_question(self) -> list:
        return await self.repository.get_all_question()
    
    async def get_question_by_chapter(self, chapter: str) -> list:
        return await self.repository.get_question_by_chapter(chapter=chapter)
    
    async def get_question_by_chapter_and_id(self, chapter: str, question_id: int) -> list:
        return await self.repository.get_question_by_chapter_and_id(chapter=chapter, question_id=question_id)
    
    async def reset_question_table(self):
        return await self.repository.reset_table()

    

