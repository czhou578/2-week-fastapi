# FastAPI Path Parameters

In FastAPI, path parameters are parts of the URL path that are captured as function parameters: Path Urls are executed in order of definition!!!

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

Path parameters:
- Are defined in curly braces `{}`
- Can be typed (int, str, etc.)
- FastAPI automatically validates and converts types
- Required by default
- Can have path parameter validation with Pydantic

Multiple path parameters can be used in a single endpoint.

# Pydantic Role in Route Validation

In FastAPI, pydantic plays

a crucial role in data validation:

- Acts as the foundation for all data validation in FastAPI
- Validates request and response data against predefined models
- Converts incoming JSON to Python objects and vice versa
- Provides automatic documentation for your API
- Handles type annotations and enforces type checking
- Enables complex validation rules through field constraints

Example usage:

```python
from fastapi import FastAPI, Path
from pydantic import BaseModel, Field

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    
@app.get("/items/{item_id}")
def read_item(item_id: int = Path(..., ge=1), q: str = None):
    return {"item_id": item_id, "q": q}
```

With Pydantic, FastAPI handles validation errors automatically, returning appropriate HTTP status codes and error messages.