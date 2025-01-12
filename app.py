from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
from bson.objectid import ObjectId
import datetime
from models import Investor
from flask import Flask, jsonify, request, session, redirect, url_for, render_template, flash
from datetime import datetime
from bson import ObjectId

import stripe
stripe.api_key = "sk_test_51QgOg4Kjkoqs3fx5f4CvkSHpYZazFpaNxOhWSj9oOU4yJ5lxMcAXdZQ0klppdvjzWSGDt4pL1fbBni3S4vFuGCrf00gcrqu6qU" 


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
                    # return redirect(url_for("investor_dashboard"))  # Investor dashboard if role is investor
                    return render_template("homepage.html")
                elif role == "entrepreneur":
                    # return redirect(url_for("startup_dashboard"))  # Startup dashboard if role is startup
                    return render_template("homepage.html")
            
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
        
        # Aggregation pipeline to get projects with investor details
        pipeline = [
            {
                "$match": {"startup_id": ObjectId(user_id)}
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "investments.investor_id",
                    "foreignField": "_id",
                    "as": "investor_details"
                }
            }
        ]
        
        try:
            projects = list(mongo.db.projects.aggregate(pipeline))
            
            # Process each project to add investor names
            for project in projects:
                # Create a map of investor IDs to names
                investor_map = {str(investor['_id']): investor['name'] 
                              for investor in project.get('investor_details', [])}
                
                # Add investor names to investments
                if 'investments' in project:
                    for investment in project['investments']:
                        investor_id = str(investment['investor_id'])
                        investment['investor_name'] = investor_map.get(investor_id, 'Unknown Investor')
                        # Format amount to 2 decimal places
                        investment['amount'] = float(investment['amount'])
            
            return render_template("startup_dashboard.html", name=session["name"], projects=projects)
            
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return render_template("startup_dashboard.html", name=session["name"], projects=[])
            
    return redirect("/login")



# Route to create a project (Startup)
# Route to create a project (Startup)
# Update the create_project route
@app.route("/create-project", methods=["GET", "POST"])
def create_project():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        funding_goal = float(request.form.get("funding_goal"))
        deadline = request.form.get("deadline")
        total_equity = float(request.form.get("total_equity", 0))  # New field
        user_id = session["user_id"]

        # Insert project into database
        project = {
            "title": title,
            "description": description,
            "funding_goal": funding_goal,
            "current_funding": 0,
            "deadline": deadline,
            "startup_id": ObjectId(user_id),
            "total_equity": total_equity,            # Total equity being offered
            "remaining_equity": total_equity,        # Initially same as total equity
            "status": "active",                     # Project status
            "investments": []                       # List to track investments
        }
        mongo.db.projects.insert_one(project)
        return redirect("/startup-dashboard")
    return render_template("create_project.html")


@app.route("/investor-dashboard")
def investor_dashboard():
    if "role" in session and session["role"] == "investor":
        user_id = session["user_id"]
        
        # Fetch projects the user has invested in
        user_investments = []
        investments = mongo.db.projects.find({"investments.investor_id": ObjectId(user_id)})
        
        total_invested = 0
        for project in investments:
            for investment in project["investments"]:
                if str(investment["investor_id"]) == user_id:
                    # Add investment date and transaction ID
                    user_investments.append({
                        "project_title": project["title"],
                        "project_description": project["description"],
                        "amount": investment["amount"],
                        "equity_percentage": investment["equity_percentage"],
                        "status": project["status"],
                        "deadline": project["deadline"],
                        "investment_date": investment.get("date"),
                        "transaction_id": investment.get("transaction_id"),
                        "project_id": str(project["_id"])  # Add project ID for tracking
                    })
                    total_invested += investment["amount"]
        
        # Fetch only approved and not fully funded projects
        projects = list(mongo.db.projects.find({
            "status": "Approved",
            "$expr": {
                "$lt": ["$current_funding", "$funding_goal"]
            }
        }).sort("deadline", 1))  # Sort by deadline ascending
        
        for project in projects:
            try:
                # Calculate current funding if not already set
                if "current_funding" not in project:
                    current_funding = sum(inv["amount"] for inv in project.get("investments", []))
                    # Update the project document with current funding
                    mongo.db.projects.update_one(
                        {"_id": project["_id"]},
                        {"$set": {"current_funding": current_funding}}
                    )
                    project["current_funding"] = current_funding
                
                # Calculate remaining funding
                project["remaining_funding"] = project["funding_goal"] - project["current_funding"]
                
                # Calculate remaining equity
                total_equity_taken = sum(inv["equity_percentage"] for inv in project.get("investments", []))
                project["remaining_equity"] = project.get("total_equity", 0) - total_equity_taken
                
                # Calculate funding progress percentage
                project["funding_progress"] = (project["current_funding"] / project["funding_goal"]) * 100
                
                # Add time remaining calculation
                if isinstance(project["deadline"], str):
                    deadline = datetime.strptime(project["deadline"], "%Y-%m-%d")
                else:
                    deadline = project["deadline"]
                project["days_remaining"] = (deadline - datetime.now()).days
                
                # Remove projects that are fully funded or have no remaining equity
                if project["remaining_funding"] <= 0 or project["remaining_equity"] <= 0:
                    projects.remove(project)
                    
            except Exception as e:
                app.logger.error(f"Error processing project {project.get('_id')}: {str(e)}")
                continue
        
        return render_template(
            "investor_dashboard.html",
            name=session["name"],
            projects=projects,
            user_investments=user_investments,
            total_invested=total_invested
        )
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

            if project_id:
                if action == "approve":
                    mongo.db.projects.update_one(
                        {"_id": ObjectId(project_id)},
                        {"$set": {"status": "Approved"}}
                    )
                elif action == "reject":
                    mongo.db.projects.delete_one({"_id": ObjectId(project_id)})

            # Redirect to the admin page after the action
            return redirect(url_for("admin_panel"))

        return render_template("admin_dashboard.html", users=users, projects=projects)

    return redirect("/login")




from datetime import datetime

# Backend route (app.py)
@app.route("/invest/<project_id>", methods=["POST"])
def invest(project_id):
    if "role" not in session or session["role"] != "investor":
        return jsonify({"error": "Please login as an investor"}), 401
        
    try:
        # Get the investment amount from the form
        amount = float(request.form.get("investment"))
        
        # Fetch project details
        project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
        if not project:
            return jsonify({"error": "Project not found"}), 404
            
        # Validate project status
        if project.get("status") != "Approved":
            return jsonify({"error": "Project is not approved for investments"}), 400
            
        # Calculate equity percentage
        total_equity = project.get("total_equity", 0)
        funding_goal = project.get("funding_goal", 1)
        equity_percentage = (amount / funding_goal) * total_equity
        
        # Validate remaining equity
        current_equity_taken = sum(inv.get("equity_percentage", 0) for inv in project.get("investments", []))
        remaining_equity = total_equity - current_equity_taken
        
        if equity_percentage > remaining_equity:
            return jsonify({"error": f"Not enough equity available. Maximum available equity is {remaining_equity}%"}), 400
            
        # Store investment details in session
        session['pending_investment'] = {
            'amount': amount,
            'equity_percentage': equity_percentage,
            'project_id': str(project["_id"])
        }
            
        # Return success response with redirect URL
        return jsonify({
            "success": True,
            "redirect": url_for('payment', 
                              project_id=project_id, 
                              amount=amount, 
                              equity_percentage=equity_percentage)
        })
        
    except ValueError:
        return jsonify({"error": "Invalid investment amount"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/payment/<project_id>')
def payment(project_id):
    if "role" not in session or session["role"] != "investor":
        return redirect(url_for("login"))
        
    try:
        # Get pending investment from session
        pending_investment = session.get('pending_investment')
        if not pending_investment or pending_investment['project_id'] != project_id:
            return redirect(url_for('investor_dashboard'))
            
        # Fetch project details from database
        project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
        if not project:
            return redirect(url_for('investor_dashboard'))
            
        return render_template(
            "payment.html",
            project=project,
            amount=pending_investment['amount'],
            equity_percentage=pending_investment['equity_percentage'],
            name=session.get("name")
        )
        
    except Exception as e:
        print(f"Error in payment route: {str(e)}")
        return redirect(url_for('investor_dashboard'))
    




@app.route("/create-payment-intent/<project_id>", methods=["POST"])
def create_payment_intent(project_id):
    if "role" not in session or session["role"] != "investor":
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        # Get investment details from session
        pending_investment = session.get('pending_investment')
        if not pending_investment or pending_investment['project_id'] != project_id:
            return jsonify({"error": "Invalid investment session - please try investing again"}), 400
            
        amount = pending_investment['amount']
        equity_percentage = pending_investment['equity_percentage']
        
        print(f"Creating payment intent for project {project_id}, amount: {amount}, equity: {equity_percentage}")  # Debug log
        
        # Create Stripe PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            automatic_payment_methods={
                "enabled": True
            },
            metadata={
                "project_id": project_id,
                "investor_id": session["user_id"],
                "equity_percentage": equity_percentage
            }
        )
        
        print(f"Payment intent created successfully: {intent.id}")  # Debug log
        
        return jsonify({
            "clientSecret": intent.client_secret
        })
        
    except Exception as e:
        print(f"Error creating payment intent: {str(e)}")  # Debug log
        return jsonify({"error": f"Payment initialization failed: {str(e)}"}), 400



@app.route("/confirm-investment/<project_id>")
def confirm_investment(project_id):
    if "role" not in session or session["role"] != "investor":
        return redirect(url_for('login'))
        
    try:
        payment_intent_id = request.args.get('payment_intent')
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status == "succeeded":
            # Get investment details from pending investment in session
            pending_investment = session.get('pending_investment')
            if not pending_investment or pending_investment['project_id'] != project_id:
                flash("Invalid investment session", "error")
                return redirect(url_for('investor_dashboard'))
            
            amount = pending_investment['amount']
            equity_percentage = pending_investment['equity_percentage']
            
            # Update project with new investment
            now = datetime.utcnow()
            investment_data = {
                "investor_id": ObjectId(session["user_id"]),
                "amount": amount,
                "equity_percentage": equity_percentage,
                "date": now,
                "transaction_id": payment_intent_id
            }
            
            # Update project document
            result = mongo.db.projects.update_one(
                {
                    "_id": ObjectId(project_id),
                    "remaining_equity": {"$gte": equity_percentage}
                },
                {
                    "$push": {"investments": investment_data},
                    "$inc": {
                        "current_funding": amount,
                        "remaining_equity": -equity_percentage
                    }
                }
            )
            
            if result.modified_count == 1:
                session.pop('pending_investment', None)
                flash("Investment successful!", "success")
            else:
                # If investment fails, initiate refund
                stripe.Refund.create(payment_intent=payment_intent_id)
                flash("Investment failed, payment refunded", "error")
                
        else:
            flash("Payment failed or was cancelled", "error")
            
        return redirect(url_for('investor_dashboard'))
            
    except Exception as e:
        print(f"Error in confirm_investment: {str(e)}")  # Add logging
        flash(f"An error occurred during payment processing", "error")
        return redirect(url_for('investor_dashboard'))



# @app.route("/confirm-investment/<project_id>")
# def confirm_investment(project_id):
#     if "role" not in session or session["role"] != "investor":
#         return redirect(url_for('login'))
        
#     try:
#         payment_intent_id = request.args.get('payment_intent')
#         payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
#         if payment_intent.status == "succeeded":
#             # Get investment details from pending investment in session
#             pending_investment = session.get('pending_investment')
#             if not pending_investment or pending_investment['project_id'] != project_id:
#                 flash("Invalid investment session", "error")
#                 return redirect(url_for('investor_dashboard'))
            
#             amount = pending_investment['amount']
#             equity_percentage = pending_investment['equity_percentage']
            
#             # Update project with new investment
#             now = datetime.utcnow()
#             investment_data = {
#                 "investor_id": ObjectId(session["user_id"]),
#                 "amount": amount,
#                 "equity_percentage": equity_percentage,
#                 "date": now,
#                 "transaction_id": payment_intent_id
#             }
            
#             # Update project document
#             result = mongo.db.projects.update_one(
#                 {
#                     "_id": ObjectId(project_id),
#                     "remaining_equity": {"$gte": equity_percentage}
#                 },
#                 {
#                     "$push": {"investments": investment_data},
#                     "$inc": {
#                         "current_funding": amount,
#                         "remaining_equity": -equity_percentage
#                     }
#                 }
#             )
            
#             if result.modified_count == 1:
#                 session.pop('pending_investment', None)
#                 flash("Investment successful!", "success")
#             else:
#                 # If investment fails, initiate refund
#                 stripe.Refund.create(payment_intent=payment_intent_id)
#                 flash("Investment failed, payment refunded", "error")
                
#         else:
#             flash("Payment failed or was cancelled", "error")
            
#         return redirect(url_for('investor_dashboard'))
            
#     except Exception as e:
#         flash(f"An error occurred: {str(e)}", "error")
#         return redirect(url_for('investor_dashboard'))



if __name__ == "__main__":
    app.run(debug=True)