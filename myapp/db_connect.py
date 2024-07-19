import os
import pymongo
from pymongo import MongoClient
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env.local'

load_dotenv(dotenv_path=env_path)


def get_database():
    print(os.getenv('MONGO_URL'))
    client = MongoClient(os.getenv('MONGO_URL'))
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
