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

```python
@router.get("/good-ping")
def good_ping():
    time.sleep(10) # I/O blocking operation for 10 seconds, but in a separate thread for the whole `good_ping` route

    return {"pong": True}

@router.get("/perfect-ping")
async def perfect_ping():
    await asyncio.sleep(10) # non-blocking I/O operation

    return {"pong": True}

```

**Important**:
FastAPI first converts that pydantic object to dict with its jsonable_encoder, then validates data with your response_model, and only then serializes your object to JSON.

Threads require more resources than coroutines, so they are not as cheap as async I/O operations.
Thread pool has a limited number of threads, i.e. you might run out of threads and your app will become slow. Read more (external link)


Query parameters and Request bodies are different because Request bodies are generating a schema based upon the request body
that is being sent up with the api request. 

Dependency Injection:

It is just a function that can take all the same parameters that a path operation function can take:

Dependency injection is beneficial because it is able to modularize logic. Avoid code duplication. Dependencies are also cached!

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

Multiple Middleware Stacking:

```python

app.add_middleware(MiddlewareA)
app.add_middleware(MiddlewareB)

```

MB -> MA -> Route
Route -> MA -> MB

Background Tasks are helpful when scheduling tasks to be run after returning a response. 

Start Redis Server manually:

```
redis-server --daemonize yes
```

How does dependency injection work?

- You define a function that is supposed to run, could be async, collect the results, and you inject that as a parameter into the api route. You use this to inject database logic or some common configuration. Dependencies can be functions or classes and support teardown using yield


How to handle authentication?

- You can use JWT tokens. Simply send the token to the server for a request, and if it matches what is on the server, then you are an authenticated user.

Path parameters vs Query parmaeters in FastAPI?

- Path parameters are variables that are embedded in the path of the URL, that you can extract from the url that could be variable. Query parameters are parameters defined after the question mark in the URL.

How does FastAPI handle asynchronous requests, and when should you use async def vs def?

- FastAPI spins up worker threads to execute the async request and it returns a coroutine, which is the result of an async op that you have to await. You should use it if you are doing some file reading, or I/O operation that doesn't require the main process to wait a long time. 

How do you handle background tasks, WebSockets, or long-running operations in FastAPI?

- You can use backgroundtasks, which is a module in fastAPI for such operations, and also @app.websockets to do this.

How does FastAPI internally distinguish between path parameters, query parameters, and request bodies, and how does it infer their locations using Python type hints and default values?

- Declared with Pydantic models are treated as request bodies. Parameters with default values of None or 0 and not part of url are treated as query params. 

What are the differences between Depends, Header, Cookie, and Body in FastAPI, and how do they contribute to dependency injection or request parsing?

- Depends: Used for dependency injection. Can inject logic, DB sessions, auth tokens, etc. Header: Extracts data from request headers. Cookie: Extracts data from cookies.
Body: Forces interpretation of a primitive or dict parameter as part of the request body.

What are some common patterns or anti-patterns for using async/await in FastAPI applications? How does blocking I/O affect FastAPI performance, and how should it be mitigated?

- Basically not mixing async and sync code together due to performance issues.

In a real-world deployment, how would you configure FastAPI to handle CORS, rate limiting, and secure HTTPS endpoints? Mention relevant middleware and deployment considerations.

- Cors config, rate limit using api gateways, and use HTTPS middleware like cloudflare.

How can you integrate FastAPI with SQLAlchemy (sync or async), and what are best practices for managing database sessions in a high-concurrency environment?

- use connection pools
- reuse db sessions
- use try catch blocks for commits.

How would you implement role-based access control (RBAC) in a FastAPI application, and what are the trade-offs between doing it at the route level vs the service layer?

- for simple checks, use the route level but for complex business logic, use the app level.



