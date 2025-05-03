from sqlalchemy import String, Integer, Boolean, Column
from .base import Base

class GameStatus(Base):
    __tablename__ = "gamestatus"
    
    id = Column(Integer, primary_key=True, index=True)
    sections = Column(String, nullable=True, unique=False, 
                      default="Начальный этап Великой Отечественной войны.Коренной перелом в ходе Великой Отечественной войны.Завершающий этап Великой Отечественной войны")
    current_section_index = Column(Integer, nullable=True, default=0)

    current_question = Column(String, nullable=True)
    answer_for_current_question = Column(String, nullable=True)
    current_question_image = Column(String, nullable=True, unique=False)
    current_answer_image = Column(String, nullable=True, unique=False)

    game_started = Column(Boolean, nullable=True, default=False)
    game_over = Column(Boolean, nullable=True, default=False)
    timer = Column(Boolean, nullable=True, default=False)
    show_answer = Column(Boolean, nullable=True, default=False)
    spectator_display_mode = Column(String, nullable=True, default="question")

