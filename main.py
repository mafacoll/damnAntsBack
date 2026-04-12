import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

class Transaction(BaseModel):
    description: str

class Transactions(BaseModel):
    transactions: list[Transaction]


app = FastAPI()

#origins that can access the aplication
origins = [
    "http://localhost:3000"
]

#middleare prohibits unauthorized to interact
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

memory_db = {"transactions": []}

@app.get("/transactions", response_model=Transactions)
def get_transactions():
    return Transactions(transactions=memory_db["transactions"])

@app.post("/transactions")
def add_transaction(transaction: Transaction):
    memory_db["transactions"].append(transaction)
    return transaction

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)