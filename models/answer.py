from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text
from .base import Base



class Answer(Base):
    __tablename__ = "answers"
    
    question: Mapped[str] = mapped_column(Text, nullable=False, unique=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True, unique=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False, unique=False)

    answer_at: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
