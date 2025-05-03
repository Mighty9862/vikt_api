from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, LargeBinary, Integer
from .base import Base

class User(Base):
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
