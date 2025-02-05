from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from .base import Base
from sqlalchemy import ForeignKey, DateTime
from datetime import datetime

class Answer(Base):
    __tablename__ = "answers"
    
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False, unique=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True, unique=False)
    answer: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)

    answer_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    
    #profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    #settings: Mapped["SettingsModel"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
