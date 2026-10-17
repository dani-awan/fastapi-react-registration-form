import os
import re
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pwdlib import PasswordHash
from sqlalchemy import DateTime, String, create_engine, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

load_dotenv()
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise RuntimeError('Set DATABASE_URL in backend/.env first.')
engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
password_hasher = PasswordHash.recommended()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(11))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Registration(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr = Field(max_length=254)
    phone: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator('name', 'email', 'phone', mode='before')
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        return str(value).lower()

    @field_validator('name')
    @classmethod
    def validate_name(cls, value):
        if not any(char.isalpha() for char in value):
            raise ValueError('Name must contain letters.')
        return value

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value):
        if not re.fullmatch(r'03[0-9]{9}', value):
            raise ValueError('Use a Pakistan mobile number such as 03001234567.')
        return value

    @field_validator('password')
    @classmethod
    def validate_password(cls, value):
        if not re.search(r'[A-Za-z]', value) or not re.search(r'[0-9]', value):
            raise ValueError('Password must contain a letter and a number.')
        return value


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    phone: str
    created_at: datetime


@asynccontextmanager
async def lifespan(app):
    # Convenient initial table creation for this local learning project.
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


app = FastAPI(title='Registration Form API', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('FRONTEND_ORIGINS', 'http://localhost:5173').split(','),
    allow_methods=['POST'],
    allow_headers=['Content-Type'],
)


def get_db():
    with SessionLocal() as session:
        yield session


@app.post('/api/register', response_model=UserPublic, status_code=201)
def register(data: Registration, db: Session = Depends(get_db)):
    user = User(name=data.name, email=str(data.email), phone=data.phone,
                password_hash=password_hasher.hash(data.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='This email is already registered.')
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail='Database unavailable. Please try again.')
    return user
