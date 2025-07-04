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

Query parameters and Request bodies are different because Request bodies are generating a schema based upon the request body
that is being sent up with the api request. 

Dependency Injection:

It is just a function that can take all the same parameters that a path operation function can take:

Dependency injection is beneficial because it is able to modularize logic. Avoid code duplication

Async Await in Python:

Concurrency: computer can do something else while an operation is proceeding, and come back to check on it later. once it finishes, then it grabs off the first finished task and keeps going

Parallelism: having multiple processes be running at the same time.

When you declare a path operation function with normal def instead of async def, it is run in an external threadpool that is then awaited, instead of being called directly (as it would block the server).

But all this functionality of using asynchronous code with async and await is many times summarized as using "coroutines". 

## 5 common HTTP status codes

404 - Not Found - path may be wrong
204 - Empty Content
500 - Internal server error
200 - REST Operation success!
405 - Method not allowed

Raise exception in utility function being called in path function will right away send error to client

## Extra Details that may be useful later

- Can override default exception handlers 

```python

@app_exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)        
```

Error handling benefits from better printouts of errors and also allows custom error handling



