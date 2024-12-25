from flask_pymongo import PyMongo
from bson.objectid import ObjectId

class User:
    def __init__(self, db):
        self.collection = db["users"]

    def create_user(self, name, email, password, phone, age, role):
        user_data = {
            "name": name,
            "email": email,
            "password": password,  # Note: Hash passwords in production
            "phone": phone,
            "age": age,
            "role": role
        }
        return self.collection.insert_one(user_data).inserted_id

    def find_by_email(self, email):
        return self.collection.find_one({"email": email})

    def find_by_id(self, user_id):
        return self.collection.find_one({"_id": ObjectId(user_id)})

class Project:
    def __init__(self, db):
        self.collection = db["projects"]

    def create_project(self, title, description, funding_goal, deadline, startup_id):
        project_data = {
            "title": title,
            "description": description,
            "funding_goal": funding_goal,
            "current_funding": 0,
            "deadline": deadline,
            "startup_id": ObjectId(startup_id),
            "approved": False  # Default state is not approved
        }
        return self.collection.insert_one(project_data).inserted_id

    def find_all_approved_projects(self):
        return list(self.collection.find({"approved": True}))

    def find_by_id(self, project_id):
        return self.collection.find_one({"_id": ObjectId(project_id)})

    def approve_project(self, project_id):
        return self.collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"approved": True}}
        )

class Investor:
    def __init__(self, db):
        self.collection = db["investors"]

    def invest_in_project(self, project_id, amount):
        project = self.collection.find_one({"_id": ObjectId(project_id)})
        if project:
            new_funding = project.get("current_funding", 0) + amount
            return self.collection.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {"current_funding": new_funding}}
            )
        return None
