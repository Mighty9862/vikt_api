from repositories.games.GameRepository import GameRepository

class GameService:

    def __init__(self, repository: GameRepository):
        self.repository = repository
    
    async def add_gamestatus(self):
        return await self.repository.add_gamestatus()
    
    async def get_sections(self):
        return await self.repository.get_sections()
    
    async def start_game(self, current_section_index: int, game_started: bool, game_over: bool):
        return await self.repository.start_game(current_section_index=current_section_index, game_started=game_started, game_over=game_over)
    
    async def stop_game(self):
        return await self.repository.stop_game()
    
    async def switch_display_mode(self, display_mode: str):
        return await self.repository.switch_display_mode(display_mode=display_mode)
    
    async def get_all_status(self):
        return await self.repository.get_all_status()
    
    async def update_section_index(self, section_index: int):
        return await self.repository.update_section_index(section_index=section_index)
    
    async def update_game_over(self, game_over: bool):
        return await self.repository.update_game_over(game_over=game_over)
    
    async def update_timer_status(self, timer: bool):
        return await self.repository.update_timer_status(timer=timer)
    
    async def update_answer_status(self, show_answer: bool):
        return await self.repository.update_answer_status(show_answer=show_answer)
    
    async def update_current_question(self, current_question: str, answer_for_current_question: str, current_question_image: str, current_answer_image: str, timer_status: bool, show_answer: bool):
        return await self.repository.update_current_question(current_question=current_question, answer_for_current_question=answer_for_current_question, current_question_image=current_question_image, current_answer_image=current_answer_image, timer_status=timer_status, show_answer=show_answer)
    
    async def update_sections(self, sections: str):
        return await self.repository.update_sections(sections=sections)
    
    
    

    

    

