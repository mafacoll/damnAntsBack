import re
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Users (admin + normal users)
users_db = {
    "admin@example.com": {
        "password": "Admin@123",
        "name": "Admin"
    },
    "user1@example.com": {
        "password": "User@1234",
        "name": "User One"
    }
}

# Transactions per user
transactions_db: Dict[str, List[dict]] = {}


# Models
class LoginRequest(BaseModel):
    username: str
    password: str


class Transaction(BaseModel):
    amount: float
    description: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str


# Helper
def get_current_user(x_user: Optional[str]):
    if not x_user or x_user not in users_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_user

def is_valid_email(email: str):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)


def is_valid_password(password: str):
    return re.match(r"^(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$", password)

# Routes

@app.post("/login")
def login(data: LoginRequest):
    user = users_db.get(data.username)

    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "username": data.username,
        "role": "admin" if data.username == "admin@example.com" else "user"
    }


@app.get("/transactions")
def get_transactions(x_user: Optional[str] = Header(None)):
    user = get_current_user(x_user)
    return transactions_db.get(user, [])


@app.post("/transactions")
def create_transaction(transaction: Transaction, x_user: Optional[str] = Header(None)):
    user = get_current_user(x_user)

    if user not in transactions_db:
        transactions_db[user] = []

    new_transaction = transaction.dict()
    new_transaction["id"] = len(transactions_db[user])

    transactions_db[user].append(new_transaction)
    return new_transaction


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, x_user: Optional[str] = Header(None)):
    user = get_current_user(x_user)

    if user not in transactions_db:
        raise HTTPException(status_code=404, detail="No transactions")

    transactions = transactions_db[user]

    if transaction_id >= len(transactions):
        raise HTTPException(status_code=404, detail="Not found")

    transactions.pop(transaction_id)
    return {"message": "Deleted"}


@app.get("/users")
def get_users(x_user: Optional[str] = Header(None)):
    if x_user != "admin@example.com":
        raise HTTPException(status_code=403, detail="Forbidden")

    return [
        {"email": email, "name": data["name"]}
        for email, data in users_db.items()
    ]


@app.post("/register")
def register(data: RegisterRequest):
    if not is_valid_email(data.username):
        raise HTTPException(status_code=400, detail="Invalid email")

    if not is_valid_password(data.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 chars, include uppercase & special char"
        )

    if data.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    users_db[data.username] = {
        "password": data.password,
        "name": data.name
    }

    return {"message": "User created"}