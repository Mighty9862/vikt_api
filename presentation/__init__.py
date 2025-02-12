from fastapi import APIRouter
from .users.UserRouter import router as UserRouter
from .questions.QuestionRouter import router as QuestionRouter
from .answers.AnswerRouter import router as AnswerRouter
from .websockets.WebSocketRouter import router as WebSocketRouter


router = APIRouter(prefix="/api/v2")
router.include_router(router=UserRouter)
router.include_router(router=QuestionRouter)
router.include_router(router=AnswerRouter)
router.include_router(router=WebSocketRouter)

