import time
from email.header import Header
from typing import Union, Annotated
from enum import Enum
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header, Depends, Response, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db, User as DBUser
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

import redis
import json

REDIS_URL = "redis://localhost:6379"
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

SECRET_KEY = "your-secret-key-here"  # Change this to a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security scheme
security = HTTPBearer()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])

logger = logging.getLogger(__name__)

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str = None

class ItemType(str, Enum):
    book = "book"

class User(BaseModel):
    id: int
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

app = FastAPI()

async def get_api_key(x_api_key: str = Header(...)):
    if x_api_key != "mysecretkey":
        raise HTTPException(status_code=400, detail="Invalid API Key")
    return x_api_key

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# JWT utilities
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(email=email)
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(DBUser).filter(DBUser.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content=jsonable_encoder({"detail": exc.detail, "body": "Not Found"}),
    )

@app.middleware("http")
async def logging_middleware(request, call_next):
    
    logging.info(f"Request: {request.method} {request.url}")
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    logging.info(f"Response: {response.status_code} in {duration:.2f} seconds")
    return response

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/users/")
def read_users(skip: int = 0, limit: int = 10):
    db: Session = next(get_db())
    users = db.query(DBUser).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}")
async def read_user(user_id: int, api_key: Annotated[str, Depends(get_api_key)]):
    # Create cache key
    cache_key = f"user:{user_id}"
    
    # Try to get from cache first
    cached_user = await get_cache(cache_key)
    if cached_user:
        logger.info(f"Cache hit for user {user_id}")
        return cached_user
    
    # Cache miss - get from database
    logger.info(f"Cache miss for user {user_id}")
    db: Session = next(get_db())
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare response data
    user_data = {
        "user_id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "status": "active" if user_id < 1000 else "inactive",
        "item_type": ItemType.book
    }
    
    # Cache the result for 5 minutes
    await set_cache(cache_key, user_data, 300)
    
    return user_data

@app.get("/users/{user_id}/items/{item_id}")
def get_user_item(user_id: int, item_id: str):
    return {"user_id": user_id, "item_id": item_id}

@app.get("/items/")
def get_items(q: str = None, skip: int | None = 0):
    return {"q": q, "skip": skip}

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, background_tasks: BackgroundTasks):
    db: Session = next(get_db())
    
    # Check if user already exists
    db_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create user with hashed password
    db_user = DBUser(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    background_tasks.add_task(write_notification, user.email, message="User created successfully")
    return {"id": db_user.id, "name": db_user.name}


@app.delete("/users/{users_id}")
def delete_user(users_id: int):
    db: Session = next(get_db())
    user = db.query(DBUser).filter(DBUser.id == users_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return Response(status_code=204)

def write_notification(email: str, message=""):
    with open("log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)


@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="Some notification")
    return Response(status_code=200, content=f"Notification sent to {email}")


@app.post("/login", response_model=Token)
def login(user_login: UserLogin):
    db: Session = next(get_db())
    user = db.query(DBUser).filter(DBUser.email == user_login.email).first()
    if not user or not verify_password(user_login.password, user.password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/protected")
async def protected_route(token: Annotated[TokenData, Depends(verify_token)]):
    return {"message": "This is a protected route", "user": token.email}

@app.get("/health/redis")
async def redis_health():
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}

# Cache utility functions
async def get_cache(key: str):
    """Get data from Redis cache"""
    try:
        cached_data = redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None

async def set_cache(key: str, value: dict, expire_time: int = 300):
    """Set data in Redis cache with expiration (default 5 minutes)"""
    try:
        redis_client.setex(key, expire_time, json.dumps(value))
    except Exception as e:
        logger.error(f"Cache set error: {e}")

async def delete_cache(key: str):
    """Delete data from Redis cache"""
    try:
        redis_client.delete(key)
    except Exception as e:
        logger.error(f"Cache delete error: {e}")

'''
curl -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d '{"name": "John Doe", "email": "john@example.com", "password": "secret123"}'

curl -X POST "http://localhost:8000/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "john@example.com", "password": "secret123"}'

curl -X GET "http://localhost:8000/protected" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

'''


