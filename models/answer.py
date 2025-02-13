from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text
from .base import Base
from sqlalchemy import ForeignKey, DateTime
from datetime import datetime

class Answer(Base):
    __tablename__ = "answers"
    
    question: Mapped[str] = mapped_column(Text, nullable=False, unique=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True, unique=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False, unique=False)

    answer_at: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)

    # Связь с таблицей users
    #user = relationship("User", back_populates="answers")
    # Связь с таблицей questions
    #question = relationship("Question", back_populates="answers")
    
    #profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    #settings: Mapped["SettingsModel"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
