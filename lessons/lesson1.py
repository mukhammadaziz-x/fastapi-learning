# 1-lesson
# Path parameters
from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def index():
    return {'message': 'Hello World!'}