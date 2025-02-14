from fastapi import Depends
from repositories import UserRepository, QuestionRepository, AnswerRepository, GameRepository
from services import UserService, QuestionService, AnswerService, GameService
from config import DatabaseConnection, settings
from sqlalchemy.ext.asyncio import AsyncSession

from redis.asyncio import Redis

def get_db() -> DatabaseConnection:
    return DatabaseConnection(
        db_url=settings.db.test_url,
        echo_pool=settings.db.echo_pool,
        pool_size=settings.db.pool_size,
        db_echo=settings.db.echo
    )
    
async def get_redis():
    redis = Redis(
        host=settings.redis.url, 
        port=settings.redis.port, 
        db=0)
    try:
        yield redis
    finally:
        await redis.close()
    
def get_user_repository(session: AsyncSession = Depends(get_db().sesion_creation)) -> UserRepository:
    return UserRepository(session=session)

def get_question_repository(session: AsyncSession = Depends(get_db().sesion_creation), redis: Redis = Depends(get_redis)) -> QuestionRepository:
    return QuestionRepository(session=session, redis=redis)

def get_answer_repository(session: AsyncSession = Depends(get_db().sesion_creation)) -> AnswerRepository:
    return AnswerRepository(session=session)

def get_game_repository(session: AsyncSession = Depends(get_db().sesion_creation)) -> GameRepository:
    return GameRepository(session=session)

#def get_hobby_repository(session: AsyncSession = Depends(get_db().sesion_creation)) -> HobbyRepository:
    return HobbyRepository(session=session)

#def get_settings_repository(session: AsyncSession = Depends(get_db().sesion_creation)) -> SettingsModelRepository:
    return SettingsModelRepository(session=session)

#==================================================================

def get_user_service(repository: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repository=repository)

def get_question_service(repository: QuestionRepository = Depends(get_question_repository)) -> QuestionService:
    return QuestionService(repository=repository)

def get_answer_service(repository: AnswerRepository = Depends(get_answer_repository)) -> AnswerService:
    return AnswerService(repository=repository)

def get_game_service(repository: GameService = Depends(get_game_repository)) -> GameService:
    return GameService(repository=repository)

#def get_hobby_service(repository: HobbyService = Depends(get_hobby_repository)) -> HobbyService:
    return HobbyService(repository=repository)

#def get_settings_service(repository: SettingsModelService = Depends(get_settings_repository)) -> SettingsModelService:
    return SettingsModelService(repository=repository)