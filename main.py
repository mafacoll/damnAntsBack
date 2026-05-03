from fastapi import FastAPI, Depends, HTTPException, Header, Body
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User, Transaction
from schemas import UserCreate, UserLogin, TransactionCreate

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

#  que paginas permite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # mejor que "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# tablas
Base.metadata.create_all(bind=engine)

# DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# USER HELPERS
def get_current_user(user_id: int, db: Session):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")

    return user


# LOGIN
@app.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(status_code=400, detail="Usuario no existe")

    if user.password_hash != data.password:
        raise HTTPException(status_code=400, detail="Password incorrecto")

    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin
    }


@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    # comprobar email
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    # comprobar username
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username ya existe")

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=user.password,  
        birth_date=user.birth_date,
        is_admin=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "is_admin": new_user.is_admin
    }

@app.get("/users")
def get_users(
    user_id: int = Header(..., alias="user-id"),
    db: Session = Depends(get_db)
):

    admin = get_current_user(user_id, db)

    if not admin.is_admin:
        raise HTTPException(status_code=403, detail="No autorizado")

    users = db.query(User).filter(User.id != admin.id).all()

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


@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: dict = Body(...),
    current_user_id: int = Header(..., alias="user-id"),
    db: Session = Depends(get_db)
):

    admin = get_current_user(current_user_id, db)

    if not admin.is_admin:
        raise HTTPException(status_code=403, detail="No autorizado")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if "username" in data:
        user.username = data["username"]

    if "email" in data:
        user.email = data["email"]

    if "birth_date" in data:
        user.birth_date = data["birth_date"]

    if "is_admin" in data:
        user.is_admin = data["is_admin"]

    db.commit()
    db.refresh(user)

    return {"message": "Usuario actualizado"}


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user_id: int = Header(..., alias="user-id"),
    db: Session = Depends(get_db)
):

    admin = get_current_user(current_user_id, db)

    if not admin.is_admin:
        raise HTTPException(status_code=403, detail="No autorizado")

    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(user)
    db.commit()

    return {"message": "Usuario eliminado"}


# TRANSACTIONS (GET)
@app.get("/transactions")
def get_transactions(
    user_id: int = Header(..., alias="user-id"),
    db: Session = Depends(get_db)
):

    # Validar usuario
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")

    # Obtener transacciones del usuario
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .all()
    )


    # Devolver lista
    return [
        {
            "id": t.id,
            "description": t.description,
            "date": t.date,
            "amount": float(t.amount),
            "currency": t.currency,
            "is_recurring": t.is_recurring
        }
        for t in transactions
    ]
    

# TRANSACTIONS (POST)
@app.post("/transactions")
def create_transaction(
    data: TransactionCreate,
    user_id: int = Header(..., alias="user-id"),
    db: Session = Depends(get_db)
):

    # 🔐 Validar usuario
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if user.is_admin:
        raise HTTPException(status_code=403, detail="Admins no pueden crear transacciones")

    # 🧾 Crear transacción
    transaction = Transaction(
        description=data.description,
        date=data.date,
        amount=float(data.amount),  # 👈 importante
        currency=data.currency,
        is_recurring=data.is_recurring,
        user_id=user.id
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)


    return transaction

@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    data: TransactionCreate,
    user_id: int = Header(..., alias="user-id"),
    db: Session = Depends(get_db)
):
    user = get_current_user(user_id, db)

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    # 🔐 Solo el dueño puede editar
    if transaction.user_id != user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    transaction.description = data.description
    transaction.date = data.date
    transaction.amount = float(data.amount)
    transaction.currency = data.currency
    transaction.is_recurring = data.is_recurring

    db.commit()
    db.refresh(transaction)

    return {"message": "Transacción actualizada"}

@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    user_id: int = Header(..., alias="user-id"),
    db: Session = Depends(get_db)
):
    user = get_current_user(user_id, db)

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    # 🔐 Solo el dueño puede borrar
    if transaction.user_id != user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    db.delete(transaction)
    db.commit()

    return {"message": "Transacción eliminada"}