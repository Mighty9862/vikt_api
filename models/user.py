from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from .base import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    score: Mapped[int] = mapped_column(nullable=True, default=0)
    
    #profile: Mapped["Profile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    #settings: Mapped["SettingsModel"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
