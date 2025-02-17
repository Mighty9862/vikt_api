from typing import List
from ..base.base_repository import BaseRepository
from models import GameStatus
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions.exceptions import UserNotFoundException, UserNotExistsException, UserExistsException
from sqlalchemy import select, delete, text

class GameRepository(BaseRepository[GameStatus]):
    model: GameStatus = GameStatus
    exception: UserNotFoundException = UserNotFoundException()

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=self.model, exception=self.exception)

    async def add_gamestatus(self, current_question=None, answer_for_current_question=None, current_question_image=None, current_answer_image=None) -> GameStatus:
        new_gamestatus = GameStatus(
            current_question = current_question,
            answer_for_current_question = answer_for_current_question,
            current_question_image = current_question_image,
            current_answer_image = current_answer_image
        )

        self.session.add(new_gamestatus)
        await self.session.commit()
        await self.session.close()
        return new_gamestatus

    async def get_all_status(self):
        query = select(self.model)
        stmt = await self.session.execute(query)
        status = stmt.scalars().first()

        await self.session.close()
        return status
    
    async def get_sections(self):
        query = select(self.model)
        stmt = await self.session.execute(query)
        res = stmt.scalars().first()

        sections_list = (res.sections).split('.')

        if not sections_list:
            raise "Fail"
        
        await self.session.close()
        return sections_list
    
    async def start_game(self, current_section_index: int, game_started: bool, game_over: bool):
        query = select(self.model)
        stmt = await self.session.execute(query)
        status = stmt.scalars().first()

        status.current_section_index = current_section_index
        status.game_started = game_started
        status.game_over = game_over

        await self.session.commit()
        await self.session.refresh(status)
        await self.session.close()
        return {"message": "Ok"}

    async def stop_game(self):

        stmt = await self.session.execute(select(self.model))
        status = stmt.scalars().first()
        
        if not status:
            status = self.model()
            self.session.add(status)
        else:
            status.sections = "Начальный этап Великой Отечественной Войны.Коренной перелом в ходе Великой Отечественной войны.Завершающий этап Великой Отечественной войны"
            status.current_section_index = 0
            status.current_question = None
            status.answer_for_current_question = None
            status.current_question_image = None
            status.current_answer_image = None
            status.game_started = False
            status.game_over = False
            status.timer = False
            status.show_answer=False
            status.spectator_display_mode = "question"
        
        await self.session.commit()
        await self.session.refresh(status)
        await self.session.close()
        return status

    async def switch_display_mode(self, display_mode: str):
        query = select(self.model)
        stmt = await self.session.execute(query)
        status = stmt.scalars().first()

        status.spectator_display_mode = display_mode

        self.session.add(status)
        await self.session.commit()
        await self.session.refresh(status)
        await self.session.close()

    async def update_section_index(self, section_index: int):
        query = select(self.model)
        stmt = await self.session.execute(query)
        status = stmt.scalars().first()

        status.current_section_index = section_index

        await self.session.commit()
        await self.session.refresh(status)
        await self.session.close()

    async def update_game_over(self, game_over: bool):
        query = select(self.model)
        stmt = await self.session.execute(query)
        status = stmt.scalars().first()

        status.game_over = game_over

        await self.session.commit()
        await self.session.refresh(status)
        await self.session.close()

    async def update_timer_status(self, timer: bool):
        query = select(self.model)
        stmt = await self.session.execute(query)
        status = stmt.scalars().first()

        status.timer = timer

        await self.session.commit()
        await self.session.refresh(status)
        await self.session.close()

    async def update_answer_status(self, show_answer: bool):
        query = select(self.model)
        stmt = await self.session.execute(query)
        status = stmt.scalars().first()

        status.show_answer = show_answer

        await self.session.commit()
        await self.session.refresh(status)
        await self.session.close()

    async def update_current_question(self, current_question: str, answer_for_current_question: str, current_question_image: str, current_answer_image: str, timer_status: bool, show_answer: bool):
        query = select(self.model)
        stmt = await self.session.execute(query)
        status = stmt.scalars().first()

        status.current_question = current_question
        status.answer_for_current_question = answer_for_current_question
        status.current_question_image = current_question_image
        status.current_answer_image = current_answer_image
        status.timer = timer_status
        status.show_answer = show_answer

        await self.session.commit()
        await self.session.refresh(status)
        await self.session.close()
        
    
    