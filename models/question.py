from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from .base import Base

class Question(Base):
    __tablename__ = "questions"
    
    question: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)
    answer: Mapped[str] = mapped_column(String(1000), nullable=True, unique=False)
    section: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)

    question_image: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)
    answer_image: Mapped[str] = mapped_column(String(1000), nullable=False, unique=False)
