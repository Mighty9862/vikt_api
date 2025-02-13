from pydantic import BaseModel, Field
from datetime import datetime


class QuestionSchema(BaseModel):
    id: int
    question: str
    answer: str
    section: str
    question_image: str
    answer_image: str

class QuestionReadSchema(BaseModel):
    question: str
    answer: str
    section: str
    question_image: str
    answer_image: str
