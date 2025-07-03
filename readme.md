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