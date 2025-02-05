from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AnswerSchema(BaseModel):
    id: int = Field(description="Уникальный идентификатор ответа")
    question_id: int = Field(description="ID вопроса, на который дан ответ")
    user_id: Optional[int] = Field(default=None, description="ID пользователя, который оставил ответ (если есть)")
    answer: str = Field(description="Текст ответа")
    answer_at: datetime = Field(description="Дата и время создания ответа")

    class Config:
        from_attributes = True  # Ранее называлось `orm_mode = True` в Pydantic v1
        json_schema_extra = {
            "example": {
                "id": 1,
                "question_id": 10,
                "user_id": 5,
                "answer": "Это пример ответа на вопрос.",
                "answer_at": "2023-10-01T12:00:00"
            }
        }