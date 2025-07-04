import time
from email.header import Header
from typing import Union, Annotated
from enum import Enum
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header, Depends, Response
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db, User as DBUser
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])

logger = logging.getLogger(__name__)

class ItemType(str, Enum):
    book = "book"

class User(BaseModel):
    id: int
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str

app = FastAPI()

async def get_api_key(x_api_key: str = Header(...)):
    if x_api_key != "mysecretkey":
        raise HTTPException(status_code=400, detail="Invalid API Key")
    return x_api_key

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
def read_user(user_id: int, api_key: Annotated[str, Depends(get_api_key)]):
    if user_id < 0:
        return {"error": "User ID must be a non-negative integer"}
    elif user_id > 0 and user_id < 1000:
        return {"user_id": user_id, "status": "active", "item_type": ItemType.book}
    else:
        return {"user_id": user_id, "status": "inactive"}

@app.get("/users/{user_id}/items/{item_id}")
def get_user_item(user_id: int, item_id: str):
    return {"user_id": user_id, "item_id": item_id}

@app.get("/items/")
def get_items(q: str = None, skip: int | None = 0):
    return {"q": q, "skip": skip}

@app.post("/users/")
def create_user(user: User) -> UserResponse:
    db: Session = next(get_db())
    db_user = DBUser(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
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





