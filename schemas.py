from pydantic import BaseModel, EmailStr, Field
from datetime import date
from decimal import Decimal

class UserCreate(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    birth_date: date

class UserLogin(BaseModel):
    username: str
    password: str

class TransactionCreate(BaseModel):
    description: str
    date: date
    amount: Decimal
    currency: str = "EUR"
    is_recurring: bool = False
