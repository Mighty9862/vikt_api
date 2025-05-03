from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    id: int
    username: str


class UserLoginSchema(BaseModel):
    username: str
    password: str = Field(min_length=6, max_length=20)
    
class UserByName(BaseModel):
    username: str
    score: int
