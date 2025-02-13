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
    
    async def get_question_by_section(self, section: str) -> list:
        return await self.repository.get_question_by_section(section=section)
    
    async def get_question_by_section_and_id(self, section: str, question_id: int) -> list:
        return await self.repository.get_question_by_section_and_id(section=section, question_id=question_id)
    
    async def get_data_by_question(self, question: str) -> list:
        return await self.repository.get_data_by_question(question=question)
    
    async def delete_question(self, question: str) -> list:
        return await self.repository.delete_question(question=question)
    
    
    async def reset_question_table(self):
        return await self.repository.reset_table()

    

