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
    name = session.get("name", None)  # Retrieve the user's name from the session
    return render_template("homepage.html", name=name)


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

            print(f"Login attempt - Email: {email}, Role: {role}")

            if not all([email, password, role]):
                return jsonify({"error": "All fields are required"}), 400

            user = mongo.db.users.find_one({"email": email})

            if user and check_password_hash(user["password"], password) and user["role"] == role:
                session["user_id"] = str(user["_id"])
                session["role"] = user["role"]
                session["name"] = user["name"]
                print(f"Successful login for user: {email}")
                
                # Redirect investors to investor dashboard after login
                # Redirect based on user role
                if role == "admin":
                    return redirect(url_for("admin_panel"))  # Redirect to the admin dashboard if the user is an admin
                elif role == "investor":
                    return redirect(url_for("investor_dashboard"))  # Investor dashboard if role is investor
                elif role == "entrepreneur":
                    return redirect(url_for("startup_dashboard"))  # Startup dashboard if role is startup

                # if role == "admin":
                #     return redirect(url_for("admin_dashboard"))
                # return redirect(url_for("homepage"))
            
            print(f"Failed login attempt for user: {email}")
            return jsonify({"error": "Invalid credentials"}), 401

        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({"error": f"Login error: {str(e)}"}), 500

    # Get the next parameter if it exists
    next_page = request.args.get('next')
    return render_template("login.html", next=next_page)

# Dashboard route for Startups
@app.route("/startup-dashboard")
def startup_dashboard():
    if "role" in session and session["role"] == "entrepreneur":
        user_id = session["user_id"]
        projects = list(mongo.db.projects.find({"startup_id": ObjectId(user_id)}))
        return render_template("startup_dashboard.html", name=session["name"], projects=projects)
    return redirect("/login")

# Dashboard route for Investors
@app.route("/investor-dashboard")
def investor_dashboard():
    if "role" in session and session["role"] == "investor":
        projects = list(mongo.db.projects.find())
        return render_template("investor_dashboard.html", name=session["name"], projects=projects)
    return redirect("/login")


# Route to create a project (Startup)
# Route to create a project (Startup)
@app.route("/create-project", methods=["GET", "POST"])
def create_project():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        funding_goal = float(request.form.get("funding_goal"))
        deadline = request.form.get("deadline")
        user_id = session["user_id"]

        # Insert project into database
        project = {
            "title": title,
            "description": description,
            "funding_goal": funding_goal,
            "current_funding": 0,
            "deadline": deadline,
            "startup_id": ObjectId(user_id)
        }
        mongo.db.projects.insert_one(project)
        return redirect("/create-project")
    return render_template("create_project.html")

# Route to invest in a project (Investor)
@app.route("/invest/<project_id>", methods=["POST"])
def invest(project_id):
    if session["role"] == "investor":
        amount = float(request.form.get("investment"))
        project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})

        if project:
            # Update project's current funding
            new_funding = project["current_funding"] + amount
            mongo.db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"current_funding": new_funding}})

            # Record the investment
            investment = {
                "investor_id": ObjectId(session["user_id"]),
                "project_id": ObjectId(project_id),
                "amount": amount,
                "date": datetime.datetime.utcnow()
            }
            mongo.db.investments.insert_one(investment)
            return redirect("/investor-dashboard")
    return redirect("/login")

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page (or homepage)
    return redirect(url_for('homepage'))  # Replace 'login' with your login route name

#####################333
#Admin Panel Route
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "role" in session and session["role"] == "admin":
        # Fetch all users and projects
        users = list(mongo.db.users.find({}, {"password": 0}))  # Exclude passwords for security
        projects = list(mongo.db.projects.find())

        if request.method == "POST":
            # Approve or Reject a project
            project_id = request.form.get("project_id")
            action = request.form.get("action")

            if action == "approve":
                mongo.db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"status": "Approved"}})
            elif action == "reject":
                mongo.db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"status": "Rejected"}})
            return redirect(url_for("admin"))

        return render_template("admin_dashboard.html", users=users, projects=projects)

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)