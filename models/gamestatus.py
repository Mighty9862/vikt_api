from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, ARRAY, Text, Boolean
from .base import Base
from datetime import datetime

class GameStatus(Base):
    __tablename__ = "gamestatus"
    
    sections: Mapped[str] = mapped_column(Text, nullable=True, unique=False, 
                                          default="Начальный этап Великой Отечественной войны.Коренной перелом в ходе Великой Отечественной войны.Завершающий этап Великой Отечественной войны")
    current_section_index: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    current_question: Mapped[str] = mapped_column(Text, nullable=True)
    answer_for_current_question: Mapped[str] = mapped_column(Text, nullable=True)
    current_question_image: Mapped[str] = mapped_column(String(1000), nullable=True, unique=False)
    current_answer_image: Mapped[str] = mapped_column(String(1000), nullable=True, unique=False)

    game_started: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    game_over: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    timer: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    show_answer: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    spectator_display_mode: Mapped[str] = mapped_column(Text, nullable=True, default="question")

    # Связь с таблицей answers
    #answers = relationship("Answer", back_populates="user", cascade="all, delete-orphan")
    
    #profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    #settings: Mapped["SettingsModel"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
