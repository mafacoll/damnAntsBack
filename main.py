from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User, Transaction
from schemas import UserCreate, UserLogin

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🌍 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧱 crear tablas
Base.metadata.create_all(bind=engine)

# 🔌 DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🧾 REGISTER (SIN AUTH)
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=user.password,  # 👈 SIN ENCRIPTAR
        birth_date=user.birth_date,
        is_admin=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuario creado"}


@app.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(status_code=400, detail="Usuario no existe")

    if user.password_hash != data.password:
        raise HTTPException(status_code=400, detail="Password incorrecto")

    return {
        "message": "Login correcto",
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin
    }

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "birth_date": u.birth_date,
            "is_admin": u.is_admin
        }
        for u in users
    ]

@app.post("/transactions")
def create_transaction(data: dict, db: Session = Depends(get_db)):

    tx = Transaction(
    title=data["title"],
    amount=data["amount"],
    user_id=data["user_id"],
    date=data["date"],              # 🔥 obligatorio
    recurrent=data.get("recurrent", False),
    currency=data.get("currency", "EUR")
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)

    return tx


@app.put("/transactions/{tx_id}")
def update_transaction(tx_id: int, data: dict, db: Session = Depends(get_db)):

    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()

    if not tx:
        raise HTTPException(status_code=404, detail="Not found")

    tx.title = data.get("title", tx.title)
    tx.amount = data.get("amount", tx.amount)
    tx.date = data.get("date", tx.date)
    tx.recurrent = data.get("recurrent", tx.recurrent)
    tx.currency = data.get("currency", tx.currency)

    db.commit()

    return tx


@app.get("/transactions/{user_id}")
def get_transactions(user_id: int, db: Session = Depends(get_db)):

    txs = db.query(Transaction).filter(Transaction.user_id == user_id).all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "amount": float(t.amount),   # 🔥 CLAVE
            "date": t.date,
            "recurrent": t.recurrent
        }
        for t in txs
    ]