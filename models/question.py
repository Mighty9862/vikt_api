from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from .base import Base
from datetime import datetime

class Question(Base):
    __tablename__ = "questions"
    
    question: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)
    answer: Mapped[str] = mapped_column(String(1000), nullable=True, unique=False)
    chapter: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)

    question_image: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)
    answer_image: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)

    # Связь с таблицей answers
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    
    #profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    #settings: Mapped["SettingsModel"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
