from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AnswerSchema(BaseModel):
    id: int = Field(description="Уникальный идентификатор ответа")
    question: str = Field(description="вопрос, на который дан ответ")
    username: str = Field(description="username пользователя, который оставил ответ (если есть)")
    answer: str = Field(description="Текст ответа")
    answer_at: str = Field(description="Дата и время создания ответа")

    class Config:
        from_attributes = True  # Ранее называлось `orm_mode = True` в Pydantic v1
        json_schema_extra = {
            "example": {
                "id": 1,
                "question": "Вопрос",
                "username": "Username",
                "answer": "Это пример ответа на вопрос.",
                "answer_at": "12:00:00"
            }
        }