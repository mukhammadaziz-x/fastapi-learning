from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# GET - retrieves information
# POST - sends the data
# PUT - update whole model
# DELETE - delete data

# fake_db = []

# class User(BaseModel):
#     id: int
#     name: str
#     age: int
#     gender: str
#     address: str

# @app.get('/')
# def print_hello():
#     message = "Hello FastAPI learners"
#     return f"Message: {message}"
#
# @app.post('/save_to_db')
# def save_to_db(user:User):
#     fake_db.append(user)
#     return fake_db

#----------------------------------------------------------------------------------------------------------------------#
# Task
# CRUD app for a little store
# It should be able to:
    # 1. Add products
    # 2. Read products
    # 3. Update products
    # 4. Delete products

# products_db = []
#
# class Product(BaseModel):
#     id: int
#     product_name: str
#     price: float
#     quantity: int
#
# @app.post('/add_product')
# def add_product(product:Product):
#     products_db.append(product)
#     return products_db
#
# @app.get('/all_products')
# def get_products():
#     return products_db
#
# @app.put('/update_product/{id}')
# def update_product(id:int, updated_product:Product):
#     for product in products_db:
#         if product.id == id:
#             product.product_name = updated_product.product_name
#             product.price = updated_product.price
#             product.quantity = updated_product.quantity
#             return product
#     return f"Message: Product not found"
#
# @app.delete('/delete_product/{id}')
# def delete_product(id:int):
#     for product in products_db:
#          if product.id == id:
#              products_db.remove(product)
#              return f"Message: Product deleted"
#     return f"Product not found"

#----------------------------------------------------------------------------------------------------------------------#
# Assignment: Mini Task Manager API (FastAPI, No Database)
# 1. Assignment

