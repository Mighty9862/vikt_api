from pydantic import BaseModel


class QuestionSchema(BaseModel):
    id: int
    question: str
    answer: str
    section: str
    question_image: str
    answer_image: str

    class Config:
        from_attributes = True

class QuestionReadSchema(BaseModel):
    question: str
    answer: str
    section: str
    question_image: str
    answer_image: str
