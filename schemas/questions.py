from pydantic import BaseModel, Field
from datetime import datetime


class QuestionSchema(BaseModel):
    id: int
    question: str
    answer: str
    chapter: str

class QuestionReadSchema(BaseModel):
    question: str
    answer: str
    chapter: str
