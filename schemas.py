from pydantic import BaseModel, EmailStr, Field
from datetime import date

class UserCreate(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    birth_date: date

class UserLogin(BaseModel):
    username: str
    password: str