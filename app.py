from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
from bson.objectid import ObjectId
import datetime

app = Flask(__name__)

# Configuration
app.config["MONGO_URI"] = "mongodb+srv://amogh5533:2AehyekZzcrEIV9m@cluster0.kc2as.mongodb.net/angelfundr?retryWrites=true&w=majority&appName=Cluster0"
app.secret_key = "your_secret_key_here"  # Replace with a strong secret key

# Initialize MongoDB connection with error handling
try:
    mongo = PyMongo(app)
    # Test the connection
    mongo.db.command('ping')
    print("Connected successfully to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    mongo = None

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            # Check if MongoDB connection is available
            if not mongo:
                print("MongoDB connection is not available")
                return jsonify({"error": "Database connection error"}), 500

            # Get form data with debug logging
            name = request.form.get("name")
            email = request.form.get("email")
            phone = request.form.get("phone")
            password = request.form.get("password")
            confirm_password = request.form.get("confirmPassword")
            age = request.form.get("age")
            role = request.form.get("role")

            print(f"Received registration data - Email: {email}, Role: {role}")  # Debug log

            # Basic validation with detailed error messages
            if not all([name, email, phone, password, confirm_password, age, role]):
                missing_fields = [field for field, value in {
                    'name': name, 'email': email, 'phone': phone,
                    'password': password, 'confirmPassword': confirm_password,
                    'age': age, 'role': role
                }.items() if not value]
                print(f"Missing fields: {missing_fields}")  # Debug log
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

            if password != confirm_password:
                return jsonify({"error": "Passwords do not match"}), 400

            try:
                age = int(age)
                if age <= 0:
                    return jsonify({"error": "Age must be a positive number"}), 400
            except ValueError:
                return jsonify({"error": "Age must be a valid number"}), 400

            # Check if user already exists
            existing_user = mongo.db.users.find_one({"email": email})
            if existing_user:
                return jsonify({"error": "Email already registered"}), 400

            # Hash password
            hashed_password = generate_password_hash(password)

            # Create user document
            user_data = {
                "name": name,
                "email": email,
                "password": hashed_password,
                "phone": phone,
                "age": age,
                "role": role,
                "created_at": datetime.datetime.utcnow()
            }

            # Insert user with debug logging
            print("Attempting to insert user document...")  # Debug log
            result = mongo.db.users.insert_one(user_data)
            
            if result.inserted_id:
                print(f"User registered successfully with ID: {result.inserted_id}")  # Debug log
                return redirect(url_for("login"))
            else:
                print("User insertion failed - no inserted_id returned")  # Debug log
                return jsonify({"error": "Registration failed - database error"}), 500

        except Exception as e:
            print(f"Detailed registration error: {str(e)}")  # Debug log
            return jsonify({"error": f"Registration error: {str(e)}"}), 500

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            if not mongo:
                return jsonify({"error": "Database connection error"}), 500

            email = request.form.get("email")
            password = request.form.get("password")
            role = request.form.get("role")

            print(f"Login attempt - Email: {email}, Role: {role}")  # Debug log

            if not all([email, password, role]):
                return jsonify({"error": "All fields are required"}), 400

            user = mongo.db.users.find_one({"email": email})

            if user and check_password_hash(user["password"], password) and user["role"] == role:
                session["user_id"] = str(user["_id"])
                session["role"] = user["role"]
                session["name"] = user["name"]
                print(f"Successful login for user: {email}")  # Debug log
                return redirect(url_for("homepage"))
            
            print(f"Failed login attempt for user: {email}")  # Debug log
            return jsonify({"error": "Invalid credentials"}), 401

        except Exception as e:
            print(f"Login error: {str(e)}")  # Debug log
            return jsonify({"error": f"Login error: {str(e)}"}), 500

    return render_template("login.html")

# ... (rest of the routes remain the same)

if __name__ == "__main__":
    app.run(debug=True)