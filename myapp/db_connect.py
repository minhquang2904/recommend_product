import pymongo
from pymongo import MongoClient
import os
from pathlib import Path
from dotenv import load_dotenv

def get_database():
    client = MongoClient("mongodb+srv://minhquang29042001:daVCWUZcsTOOCyEY@store.goz72zm.mongodb.net/store")
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
