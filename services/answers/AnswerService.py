from typing import Optional
from repositories.answers.AnswerRepository import AnswerRepository
from schemas.users import UserLoginSchema
from werkzeug.security import generate_password_hash, check_password_hash
#from .exceptions.exceptions import IncorrectPasswordException

class AnswerService:

    def __init__(self, repository: AnswerRepository):
        self.repository = repository

    async def add_answer(self, question_id: int, user_id: Optional[int], answer: str):
        return await self.repository.add_answer(question_id=question_id, user_id=user_id, answer=answer)
    
    async def get_all_answers(self) -> list:
        return await self.repository.get_all_answers()
    
    async def get_answers_by_question_id(self, question_id: int) -> list:
        return await self.repository.get_answers_by_question_id(question_id=question_id)
    
    async def get_answers_by_user_id(self, user_id: int) -> list:
        return await self.repository.get_answers_by_user_id(user_id=user_id)
    
    async def get_answers_by_question_and_user(self, question_id: int, user_id: int) -> list:
        return await self.repository.get_answers_by_question_and_user(question_id=question_id, user_id=user_id)
    
    async def reset_answers_table(self) -> dict:
        return await self.repository.reset_table()

    

