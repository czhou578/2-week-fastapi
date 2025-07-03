from typing import Union
from enum import Enum

from fastapi import FastAPI

class ItemType(str, Enum):
    book = "book"

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/users/{user_id}")
def read_user(user_id: int):
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

