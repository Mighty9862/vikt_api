from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from .base import Base
from datetime import datetime

class Question(Base):
    __tablename__ = "questions"
    
    question: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
    answer: Mapped[str] = mapped_column(String(255), nullable=True, unique=False)
    chapter: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
    
    #profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    #settings: Mapped["SettingsModel"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
