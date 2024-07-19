import pymongo
from pymongo import MongoClient
import os

def get_database():
    mongo_url = os.getenv('MONGO_URL')
    client = MongoClient(mongo_url)
    return client['store']

def get_products_collection():
    db = get_database()
    return db['products']

def get_history_orders_collection():
    db = get_database()
    return db['historyorders']

def get_cart_collection():
    db = get_database()
    return db['carts']
