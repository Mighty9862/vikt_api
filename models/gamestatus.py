from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, ARRAY, Text, Boolean, Column
from .base import Base
from datetime import datetime

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
    timer_seconds = Column(Integer, nullable=True)  # Добавляем новое поле

    show_answer = Column(Boolean, nullable=True, default=False)

    spectator_display_mode = Column(String, nullable=True, default="question")

    # Связь с таблицей answers
    #answers = relationship("Answer", back_populates="user", cascade="all, delete-orphan")
    
    #profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    #settings: Mapped["SettingsModel"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
