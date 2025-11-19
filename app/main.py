import datetime

import sqlalchemy
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DB_NAME = "entrance_data.db"
DB_PATH = f"database/{DB_NAME}"

# SQLAlchemy setup
engine = sqlalchemy.create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Define the User model
class User(Base):
    __tablename__ = "users"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    phone = sqlalchemy.Column(sqlalchemy.String, unique=True)
    birthday = sqlalchemy.Column(sqlalchemy.String)
    date_added = sqlalchemy.Column(
        sqlalchemy.String, default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


# Create the table
Base.metadata.create_all(bind=engine)


# Pydantic schemas for data validation
class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    birthday: str


class UserResponse(UserCreate):
    id: int
    date_added: datetime.datetime

    model_config = {"from_attributes": True}


class Embedding(Base):
    __tablename__ = "embeddings"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    embedding_vector = sqlalchemy.Column(sqlalchemy.BLOB())


class EmbeddingCreate(BaseModel):
    user_id: int
    embedding_vector: list[float]


class EmbeddingResponse(EmbeddingCreate):
    id: int

    model_config = {"from_attributes": True}


app = FastAPI()


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/embeddings/", response_model=EmbeddingResponse)
def create_embedding(
    embedding: EmbeddingCreate,
    db: Session = Depends(get_db),
):
    db_embedding = Embedding(**embedding.model_dump())
    db.add(db_embedding)
    db.commit()
    db.refresh(db_embedding)
    return db_embedding


@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/embeddings/{embedding_id}", response_model=EmbeddingResponse)
def read_embedding(embedding_id: int, db: Session = Depends(get_db)):
    db_embedding = db.query(Embedding).filter(Embedding.id == embedding_id).first()
    if db_embedding is None:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return db_embedding


@app.get("/users/", response_model=list[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@app.get("/embeddings/", response_model=list[EmbeddingResponse])
def read_embeddings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    embeddings = db.query(Embedding).offset(skip).limit(limit).all()
    return embeddings


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserCreate,
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for var, value in vars(user).items():
        setattr(db_user, var, value) if value else None
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put("/embeddings/{embedding_id}", response_model=EmbeddingResponse)
def update_embedding(
    embedding_id: int,
    embedding: EmbeddingCreate,
    db: Session = Depends(get_db),
):
    db_embedding = db.query(Embedding).filter(Embedding.id == embedding_id).first()
    if db_embedding is None:
        raise HTTPException(status_code=404, detail="Embedding not found")
    for var, value in vars(embedding).items():
        setattr(db_embedding, var, value) if value else None
    db.commit()
    db.refresh(db_embedding)
    return db_embedding


@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user


@app.delete("/embeddings/{embedding_id}", response_model=EmbeddingResponse)
def delete_embedding(embedding_id: int, db: Session = Depends(get_db)):
    db_embedding = db.query(Embedding).filter(Embedding.id == embedding_id).first()
    if db_embedding is None:
        raise HTTPException(status_code=404, detail="Embedding not found")
    db.delete(db_embedding)
    db.commit()
    return db_embedding


@app.get("/")
def read_root():
    return {"message": "Welcome to the DeepFace DB API"}
