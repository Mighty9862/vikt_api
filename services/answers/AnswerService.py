from repositories.answers.AnswerRepository import AnswerRepository


class AnswerService:

    def __init__(self, repository: AnswerRepository):
        self.repository = repository

    async def add_answer(self, question: str, username: str, answer: str):
        return await self.repository.add_answer(question=question, username=username, answer=answer)
    
    async def get_all_answers(self) -> list:
        return await self.repository.get_all_answers()
    
    async def get_answers_by_question_id(self, question: str) -> list:
        return await self.repository.get_answers_by_question_id(question=question)
    
    async def get_answers_by_user_id(self, username: str) -> list:
        return await self.repository.get_answers_by_user_id(username=username)
    
    async def get_answers_by_question_and_user(self, question: str, username: str) -> list:
        return await self.repository.get_answers_by_question_and_user(question=question, username=username)
    
    async def reset_answers_table(self) -> dict:
        return await self.repository.reset_table()

    

