from fastapi import Depends
from repositories import UserRepository, QuestionRepository, AnswerRepository
from services import UserService, QuestionService, AnswerService
from config import DatabaseConnection, settings
from sqlalchemy.ext.asyncio import AsyncSession

def get_db() -> DatabaseConnection:
    return DatabaseConnection(
        db_url=settings.db.test_url,
        echo_pool=settings.db.echo_pool,
        pool_size=settings.db.pool_size,
        db_echo=settings.db.echo
    )
    
def get_user_repository(session: AsyncSession = Depends(get_db().sesion_creation)) -> UserRepository:
    return UserRepository(session=session)

def get_question_repository(session: AsyncSession = Depends(get_db().sesion_creation)) -> QuestionRepository:
    return QuestionRepository(session=session)

def get_answer_repository(session: AsyncSession = Depends(get_db().sesion_creation)) -> AnswerRepository:
    return AnswerRepository(session=session)

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

#def get_hobby_service(repository: HobbyService = Depends(get_hobby_repository)) -> HobbyService:
    return HobbyService(repository=repository)

#def get_settings_service(repository: SettingsModelService = Depends(get_settings_repository)) -> SettingsModelService:
    return SettingsModelService(repository=repository)