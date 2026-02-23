# 1-lesson
# Path parameters
from fastapi import FastAPI
from enum import Enum

app = FastAPI()

class UserType(str, Enum):
    admin = 'admin'
    superuser = 'superuser'
    regular = 'regular'

# @app.get('/')
# async def index():
#     return {'message': 'Hello World!'}

@app.get('/user/{user_id}')
async def get_user(user_id: int):
    return {'id': user_id}

@app.get('/roles/{user_type}')
async def get_user(user_type: UserType):
    if user_type == UserType.admin:
        return {'text': 'Hello, you have limited access!'}
    elif user_type is UserType.superuser:
        return {'text': 'Hello, master!'}
    else:
        return {'text': 'Who are you?'}