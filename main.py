from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# GET - retrieves information
# POST - sends the data
# PUT - update whole model
# DELETE - delete data

class User(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    address: str

@app.get('/')
def print_hello():
    message = "Hello FastAPI learners"
    return f"Message: {message}"

