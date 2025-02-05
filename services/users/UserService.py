from repositories.users.UserRepository import UserRepository
from schemas.users import UserLoginSchema
from werkzeug.security import generate_password_hash, check_password_hash
from .exceptions.exceptions import IncorrectPasswordException

class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository


    async def registration(self, user_in: UserLoginSchema):
        hash_password: str = generate_password_hash(password=user_in.password)

        return await self.repository.registration(hash_password, user_in.username)
    

    async def login(self, user_in: UserLoginSchema):
        user = await self.repository.login(username=user_in.username)

        is_valid_password: bool = check_password_hash(
            pwhash=user.password,
            password=user_in.password
        )

        if not is_valid_password:
            raise IncorrectPasswordException()

        return {
            "message": "Пользователь успешно авторизован"
        }
    
    async def get_all_user(self) -> list:
        return await self.repository.get_all_user()
    
    async def get_user_by_username(self, username: str):
        return await self.repository.get_user_by_username(username=username)
    
    async def add_score_to_user(self, username: str, points: int):
        return await self.repository.add_score_to_user(username=username, points=points)
    
    async def delete_user_by_username(self, username: str) -> dict:
        return await self.repository.delete_user_by_username(username=username)


