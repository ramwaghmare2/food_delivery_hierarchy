from flask import Blueprint, redirect, render_template, url_for, request, flash, session, current_app
from models.kitchen import Kitchen
from models.distributor import Distributor
from models import db, SuperDistributor  ,Order ,OrderItem ,Sales
import bcrypt
import json
from utils.services import get_model_counts, allowed_file ,get_image
from base64 import b64encode
from sqlalchemy import func

distributor_bp = Blueprint('distributor', __name__, template_folder='../templates/distributor', static_folder='../static')

################################## Route for distributor dashboard ##################################

import json
import logging

from datetime import datetime, timedelta

@distributor_bp.route('/', methods=['GET', 'POST'])
def distributor_home():
    try:
        # Logging session data for debugging
        logging.debug(f"Session user_id: {session.get('user_id')}")

        # Get the logged-in distributor's ID from the session
        distributor_id = session.get('user_id')
        if not distributor_id:
            flash({'error': 'Unauthorized access'})
            logging.debug("Redirecting due to missing user_id in session")
            return redirect(url_for('distributor.distributor_home'))

        # Get the filter type (if any)
        filter_type = request.args.get('filter', 'all')

        # Get the current date and calculate other date ranges for the filters
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        start_of_month = today.replace(day=1)
        start_of_year = today.replace(month=1, day=1)

        # Define the filter date ranges
        if filter_type == 'today':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif filter_type == 'yesterday':
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif filter_type == 'monthly':
            start_date = start_of_month
            end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif filter_type == 'yearly':
            start_date = start_of_year
            end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            start_date = None
            end_date = None

        # Fetch all active kitchens under this distributor
        kitchens = Kitchen.query.filter_by(distributor_id=distributor_id, status="activated").all()

        # Fetch orders based on the selected filter
        kitchen_ids = [kitchen.id for kitchen in kitchens]
        query = Order.query.filter(Order.kitchen_id.in_(kitchen_ids))

        if start_date and end_date:
            query = query.filter(Order.created_at >= start_date, Order.created_at <= end_date)

        orders = query.all()

        # Prepare data for the table
        kitchen_sales = {kitchen.name: 0 for kitchen in kitchens}
        for order in orders:
            kitchen = next(k for k in kitchens if k.id == order.kitchen_id)
            kitchen_sales[kitchen.name] += float(order.total_amount)  # Sum up the sales for each kitchen

        # Count of active kitchens for the logged-in distributor
        kitchen_count = len(kitchens)

        # Fetch orders for these active kitchens
        kitchen_ids = [kitchen.id for kitchen in kitchens]
        orders = Order.query.filter(Order.kitchen_id.in_(kitchen_ids)).all()

        # Count of orders related to the active kitchens
        order_count = len(orders)

        # Total price of all orders related to the active kitchens
        total_price = db.session.query(func.sum(Order.total_amount))\
        .filter(Order.kitchen_id.in_(kitchen_ids))\
        .filter(Order.order_status == 'Completed')\
        .scalar()
        total_price = float(total_price) if total_price else 0  # Convert to float

        # Prepare data for bar chart
        kitchen_order_count = {kitchen.name: 0 for kitchen in kitchens}
        kitchen_sales = {kitchen.name: 0 for kitchen in kitchens}

        for order in orders:
            kitchen = next(k for k in kitchens if k.id == order.kitchen_id)
            kitchen_order_count[kitchen.name] += 1
            kitchen_sales[kitchen.name] += float(order.total_amount)  # Convert to float

        # Prepare data for pie chart: Total sales amount for each kitchen
        kitchen_sales_total = {kitchen.name: 0 for kitchen in kitchens}
        
        # Calculate the total sales amount for each kitchen based on orders
        for order in orders:
            if order.order_status == 'Completed':
                kitchen = next(k for k in kitchens if k.id == order.kitchen_id)
                kitchen_sales_total[kitchen.name] += float(order.total_amount)  # Sum up the total sales amount

        # Get user data (name, role, etc.)
        user_name = session.get('user_name', 'User')
        role = session.get('role')
        image_data = get_image(role, distributor_id)

        # Render the distributor home page with table and chart data
        return render_template(
            'd_index.html', 
            user_name=user_name,
            role=role, 
            encoded_image=image_data,
            kitchen_count=kitchen_count,
            order_count=order_count,
            total_price=total_price,
            kitchen_names=json.dumps(list(kitchen_order_count.keys())),
            order_counts=json.dumps(list(kitchen_order_count.values())),
            sales_data=json.dumps(list(kitchen_sales.values())),
            pie_chart_labels=json.dumps(list(kitchen_sales_total.keys())),
            pie_chart_data=json.dumps(list(kitchen_sales_total.values())),
            kitchens=kitchens,
            kitchen_sales=kitchen_sales,
            filter_type=filter_type
        )
    except Exception as e:
        flash({'error': str(e)})
        logging.error(f"Error occurred: {str(e)}")
        return redirect(url_for('distributor.distributor_home'))


################################## Route for display all distributor ##################################
@distributor_bp.route('/all-distributor', methods=['GET'])
def all_distributor():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    if role == 'Admin':
        # Admin sees all distributors
        all_distributors = Distributor.query.all()
    elif role == 'SuperDistributor':
        all_distributors = Distributor.query.filter_by(super_distributor=user_id).all()
    else:
        # Non-admin sees distributors linked to their super distributors
        super_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
        super_distributor_ids = [sd.id for sd in super_distributors]
        print("Super Distributor IDs:", super_distributor_ids)
        all_distributors = Distributor.query.filter(Distributor.super_distributor.in_(super_distributor_ids)).all()
    # Convert images to Base64 format
    for distributors in all_distributors:
            if distributors.image:
                distributors.image_base64 = f"data:image/jpeg;base64,{b64encode(distributors.image).decode('utf-8')}"
            else:
                distributors.image_base64 = None
    return render_template('d_all_distributor.html', all_distributors=all_distributors,role=role,user_name=user_name, encoded_image=image_data)


################################## Route to display all kitchens ##################################
@distributor_bp.route('/all-kitchens', methods=['GET'])
def distrubutor_all_kitchens():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id)  # Assuming 'user_id' is stored in the session
    counts = get_model_counts()
    if role == 'Admin':
            # Admin sees all kitchens
            all_kitchens = Kitchen.query.all()   
    elif role == 'SuperDistributor':
            distributors = Distributor.query.filter_by(super_distributor=user_id).all()
            distributor_ids = [dist.id for dist in distributors]
            all_kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
    elif role == 'Distributor':
            all_kitchens = Kitchen.query.filter_by(distributor_id=user_id).all()
    else:
            # Non-admin sees kitchens linked to their distributors
            super_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
            super_distributor_ids = [sd.id for sd in super_distributors]
            distributors = Distributor.query.filter(Distributor.super_distributor.in_(super_distributor_ids)).all()
            distributor_ids = [dist.id for dist in distributors]
            all_kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
    return render_template('kitchen/all_kitchens.html', all_kitchens=all_kitchens , role=role , user_name=user_name, **counts , encoded_image=image_data)

################################## Route to delete kitchen ##################################
@distributor_bp.route('/delete-kitchen/<int:kitchen_id>', methods=['GET','POST'])
def delete_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)
    db.session.delete(kitchen)
    db.session.commit()
    flash('Kitchen deleted successfully!')
    return redirect(url_for('distributor.distrubutor_all_kitchens'))

################################## Route for delete the distributor ##################################
@distributor_bp.route('/delete/<int:distributor_id>', methods=['GET', 'POST'])
def delete_distributor(distributor_id):
    
    distributor = Distributor.query.get_or_404(distributor_id)

    try:
        distributor.status = 'deactivated'
        # db.session.delete(distributor)
        db.session.commit()
        flash("Distributor deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('distributor.all_distributor'))

################################## Function for image storage ##################################
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

################################## Route for edit the distributor ##################################
@distributor_bp.route('/edit/<int:distributor_id>', methods=['GET', 'POST'])
def edit_distributor(distributor_id):
    distributor = Distributor.query.get_or_404(distributor_id)

    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']
        image = request.files.get('image')  # Get the image from the form if it exists

        # Validate if email already exists (excluding the current distributor)
        existing_distributor_email = Distributor.query.filter(Distributor.email == email, Distributor.id != Distributor.id).first()
        if existing_distributor_email:
            flash("The email is already in use by another Distributor.", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role)

        # Validate if contact already exists (excluding the current distributor)
        existing_distributor_contact = Distributor.query.filter(Distributor.contact == contact, Distributor.id != Distributor.id).first()
        if existing_distributor_contact:
            flash("The contact number is already in use by another Distributor.", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role)

        # Update distributor details
        distributor.name = name
        distributor.email = email
        distributor.contact = contact

        # If password is provided, hash and update it
        if password:
            distributor.password = bcrypt.generate_password_hash(password).decode('utf-8')

        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            distributor.image = image_binary

        try:
            db.session.commit()
            flash("Distributor updated successfully!", "success")
            return redirect(url_for('distributor.all_distributor'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Distributor: {str(e)}", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role , encoded_image = image_data)

    return render_template('edit_distributor.html', distributor=distributor, role=role , encoded_image = image_data)

################################## Route for Display orders related to distributor ##################################
from datetime import datetime, timedelta

@distributor_bp.route('/distributor-orders', methods=['GET'])
def distributor_orders():
    try:
        # Get the logged-in distributor's ID from the session
        distributor_id = session.get('user_id')
        role = session.get('role')
        image_data= get_image(role, distributor_id) 
        if not distributor_id:
            flash({'error': 'Unauthorized access'})
            return redirect(url_for('distributor.distributor_home'))

        # Fetch all kitchens under this distributor
        kitchens = Kitchen.query.filter_by(distributor_id=distributor_id).all()
        kitchen_ids = [kitchen.id for kitchen in kitchens]

        # Get filter values from the query parameters
        selected_kitchen_id = request.args.get('kitchen_id')
        order_status = request.args.get('status', 'All')
        date_filter = request.args.get('date', 'All')

        # Start building the query
        query = Order.query.filter(Order.kitchen_id.in_(kitchen_ids))

        # Filter by selected kitchen
        if selected_kitchen_id and selected_kitchen_id != "All":
            query = query.filter(Order.kitchen_id == int(selected_kitchen_id))

        # Filter by order status
        if order_status and order_status != "All":
            query = query.filter(Order.order_status == order_status)

        # Filter by date range
        if date_filter != "All":
            today = datetime.now()
            if date_filter == "Today":
                start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date)
            elif date_filter == "Yesterday":
                start_date = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date, Order.created_at < end_date)
            elif date_filter == "Weekly":
                start_date = today - timedelta(days=today.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date)
            elif date_filter == "Monthly":
                start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date)
            elif date_filter == "Yearly":
                start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= start_date)

        orders = query.all()

        # Prepare order data for rendering
        orders_data = [
            {
                'order_id': order.order_id,
                'user_id': order.user_id,
                'kitchen_id': order.kitchen_id,
                'total_amount': order.total_amount,
                'status': order.order_status,
                'kitchen_name': order.kitchen.name,
                'customer_name': f"{order.customer.name}",
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': [
                    {
                        'item_id': item.item_id,
                        'item_name':item.food_items.item_name,
                        'quantity': item.quantity,
                        'price': item.price,
                        'total_price': item.price * item.quantity
                    }
                    for item in order.order_items
                ]
            }
            for order in orders
        ]

        # Render the distributor's order page
        return render_template(
            'distributor/d_orders.html',
            distributor_id=distributor_id,
            kitchens=kitchens,
            orders_data=orders_data,
            selected_kitchen_id=selected_kitchen_id,
            order_status=order_status,
            date_filter=date_filter,
            encoded_image=image_data
        )
    
    except Exception as e:
        flash({'error': str(e)})
        return redirect(url_for('distributor.distributor_home'))
