# models.py
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

class User:
    def __init__(self, db):
        self.collection = db["users"]

    def create_user(name, email, password, phone, age, role):
        user_data = {
            "name": name,
            "email": email,
            "password": password,
            "phone": phone,
            "age": age,
            "role": role
        }
        return mongo.db.users.insert_one(user_data).inserted_id

    def find_by_email(email):
        return mongo.db.users.find_one({"email": email})

    def find_by_id(user_id):
        return mongo.db.users.find_one({"_id": ObjectId(user_id)})
