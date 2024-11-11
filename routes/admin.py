from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen
from functools import wraps
from sqlalchemy.exc import IntegrityError

admin_bp = Blueprint('admin_bp', __name__)

# Helper function to create a user based on role
def create_user(data, role):
    hashed_password = generate_password_hash(data['password'], method='sha256')
    try:
        if role == "Admin":
            new_user = Admin(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Manager":
            new_user = Manager(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "SuperDistributor":
            new_user = SuperDistributor(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Distributor":
            new_user = Distributor(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Kitchen":
            new_user = Kitchen(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        else:
            return None
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except IntegrityError:
        db.session.rollback()
        return None

# Role-based access control decorator
def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'role' not in session:
                return jsonify({"error": "Unauthorized access"}), 401
            if session['role'] != required_role:
                return jsonify({"error": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# Route for displaying admin dashboard
@admin_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_dashboard():
    managers = Manager.query.all()
    super_distributors = SuperDistributor.query.all()
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    return render_template('admin/admin.html', 
                           managers=managers, 
                           super_distributors=super_distributors, 
                           distributors=distributors, 
                           kitchens=kitchens)

# Route for adding new users (Manager, SuperDistributor, Distributor, Kitchen)
VALID_ROLES = ["Admin", "Manager", "SuperDistributor", "Distributor", "Kitchen"]

@admin_bp.route('/add_user/<role>', methods=['GET', 'POST'])
@role_required('Admin')
def add_user(role):
    if role not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    if request.method == 'POST':
        data = request.form
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Password match validation
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        # Create user based on the role
        user = create_user(data, role)
        if user:
            return redirect(url_for('admin_bp.admin_dashboard'))
        else:
            return jsonify({"error": "User already exists or invalid role"}), 400

    # If GET request, render the form
    return render_template('admin/add_user.html', role=role)

# Route for displaying the signup form and handling signup
@admin_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        role = data.get('role')
        if data['password'] != data['confirm_password']:
            return jsonify({"error": "Passwords do not match"}), 400
        
        user = create_user(data, role)
        if user:
            return jsonify({"message": f"{role} created successfully"}), 201
        else:
            return jsonify({"error": "User already exists or invalid role"}), 400
    # Render signup form for GET requests
    return render_template("signup.html")

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        role = data.get('role')
        email = data['email']
        password = data['password']
        
        if role == "Admin":
            user = Admin.query.filter_by(email=email).first()
        elif role == "Manager":
            user = Manager.query.filter_by(email=email).first()
        elif role == "SuperDistributor":
            user = SuperDistributor.query.filter_by(email=email).first()
        elif role == "Distributor":
            user = Distributor.query.filter_by(email=email).first()
        elif role == "Kitchen":
            user = Kitchen.query.filter_by(email=email).first()
        else:
            return jsonify({"error": "Invalid role"}), 400

        if not user or not check_password_hash(user.password, password):
            return jsonify({"error": "Invalid email or password"}), 401

        session['user_id'] = user.id
        session['role'] = role
        #return jsonify({"message": f"{role} logged in successfully"}), 200
        return redirect(url_for('admin_bp.admin_dashboard'))

    return render_template('admin/login.html')