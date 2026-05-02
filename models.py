from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    is_admin = Column(Boolean, default=False)
    

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="EUR")
    is_recurring = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User")
