# food_delivery_app/app/routes/order.py

from flask import Blueprint, request, jsonify, session, redirect, render_template, url_for, flash
# from models import Order, OrderItem, MenuItem, User
from models import Order, FoodItem, OrderItem
from models.order import db
from werkzeug.exceptions import NotFound
from decimal import Decimal
from models import Customer, FoodItem, Order
from base64 import b64encode

order_bp = Blueprint('order', __name__)

# Method to place new order

@order_bp.route('/place-order/<int:item_id>', methods=['GET','POST'])
def place_order(item_id):
    try:

        data = request.form

        item = FoodItem.query.filter_by(id=item_id).first()
        if item.image:
            item.image_base64 = f"data:image/jpeg;base64,{b64encode(item.image).decode('utf-8')}"
        else:
            item.image_base64 = None

        user_id = session.get('user_id')

        if request.method == 'POST':
        
            # Get current user id from the JWT token
            # user_id = get_jwt_identity()

            # user = User.query.get(user_id)
            # if not user:
            #     raise ValueError("User does not exist.")

            total_amount = 0  # Initialize total amount to 0

            # Create the new order with a default total_amount
            new_order = Order(
                user_id=user_id,
                kitchen_id=data['kitchen_id'],
                total_amount=total_amount,  # This will be updated after calculating
                # address=user.address
                order_status='Pending'  # Set initial status to 'Pending'
            )
            db.session.add(new_order)
            db.session.commit()

            order_items_details = []

            # if 'order_items' in data:
            #     for item in data:
                    
            menu_item = FoodItem.query.get(item_id)
            if not menu_item:
                raise ValueError(f"FoodItem with id {item_id} does not exist.")

            original_price = item.price   # Store the original price

            item_total_price = original_price * int(data['quantity'])  # Calculate total price for this order item base on quantity.
            
            # Create the order item
            order_item = OrderItem(
                order_id=new_order.order_id,
                item_id=item_id,
                quantity=data['quantity'],
                price=item_total_price,  # Save the original price
            )
            db.session.add(order_item)

            # Append the order item details to the list
            order_items_details.append({
                'item_id': item_id,
                'quantity': data['quantity'],
                'item_price': original_price,
                'total_price': item_total_price
            })

            # Add the item's total price to the total amount for the order
            total_amount += item_total_price

            # Calculate GST (18%) for the order price
            # gst = total_amount * Decimal('0.18')

            # Add delivery charge (50 rupees)
            # delivery_charge = Decimal('50.00')

            # Update the total amount with GST and delivery charge
            total_amount_with_gst_and_delivery = total_amount# + gst + delivery_charge

            # Update the total amount of the order
            new_order.total_amount = total_amount_with_gst_and_delivery
            
            db.session.commit()

            # return jsonify({
            #     'message': 'Order created successfully!',
            #     'order_id': new_order.order_id,
            #     'delivery_charge':delivery_charge,
            #     'gst': gst,
            #     'total_amount': total_amount,
            #     'address': user.address,
            #     'order_items': order_items_details

            # }), 201 
            # return redirect(url_for('payment.make_payment', order_id=new_order.order_id))
            # return redirect(url_for('https://cosmofeed.com/vp/670e326be4c91d00131ada48'))
            flash('Order Successful!')
            return redirect(url_for('customer.customer_dashboard'))
    
        return render_template('order/place_order.html', item=item)

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Method to get Order Details by order_id.
@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = Order.query.get_or_404(order_id) # Fetch the order 
        # Fetch Order details.
        order_data = {
            'order_id': order.order_id,
            'restaurant_id': order.restaurant_id,
            'user_id': order.user_id,
            'total_amount': order.total_amount,
            'status': order.order_status,
            # Fetch oredr item details.
            'items': [                              
                {'item_id': item.item_id, 'quantity': item.quantity}
                for item in order.order_items
            ]
        }
        
        return jsonify(order_data), 200
    
    except NotFound:
        # If order not found.
        return jsonify({'message': 'Order not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Method to get Order Details by user_id.
@order_bp.route('/user/<int:user_id>', methods=['GET'])
def get_orders_by_user_id(user_id):
    try:
        orders = Order.query.filter_by(user_id=user_id).all()
        
        if not orders:
            return jsonify({'message': 'No orders yet'}), 200
        
        orders_data = [
            {
                'order_id': order.order_id,
                'restaurant_id': order.restaurant_id,
                'total_amount': order.total_amount,
                'status': order.order_status,
                'created_at': order.created_at,
                'updated_at': order.updated_at
            }
            for order in orders
        ]
        
        return jsonify(orders_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Method to get orders of login user
@order_bp.route('/my-orders', methods=['GET'])
def get_orders_login_user():
    try:
        user_id = session.get('user_id')

        orders = Order.query.filter_by(user_id=user_id).all()

        if not orders:
            flash('No orders yet')
            return redirect(url_for('customer.customer_dashboard'))

        # Prepare the orders data with order items to return
        orders_data = [
            {
                'order_id': order.order_id,
                'kitchen_id': order.kitchen_id,
                'total_amount': order.total_amount,
                'status': order.order_status,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': [
                    {
                        'item_id': item.item_id,
                        'quantity': item.quantity,
                        'price': item.price,
                        'total_price': item.price * item.quantity
                    }
                    for item in order.order_items
                ]
            }
            for order in orders
        ]

        return render_template('order/my_orders.html', orders_data=orders_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Method to Delete the Order along with Order items
@order_bp.route('/delete/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        # Fetch the order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"message": "Order not found."}), 404  

        # Check if the order status is "Pending" or "Processing"
        if order.order_status not in ['Pending', 'Processing']:
            return jsonify({"message": "Only orders with status 'Pending' or 'Processing' can be deleted."}), 400

        # Delete all related OrderItems
        Order.query.filter_by(order_id=order_id).delete()

        # Delete the order itself
        db.session.delete(order)
        db.session.commit()

        return jsonify({"message": "Order deleted successfully!"}), 200  

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400  


@order_bp.route('/cart', methods=['POST'])
def order_cart():
    data =request.json
    try:
        # Get current user id from the JWT token
        user_id = session.get('user_id')
        restaurant_id = data.get('restaurant_id', 1)
        # Retrieve the cart for the logged-in user from the session
        cart_key = f'cart_{user_id}'
        cart_items = session.get(cart_key, [])

        if not cart_items:
            raise ValueError("Cart is empty.")

        user = Customer.query.get(user_id)
        if not user:
            raise ValueError("User does not exist.")

        total_amount = 0  # Initialize total amount to 0

        # Create the new order with a default total_amount
        new_order = Order(
            user_id=user_id,
            restaurant_id=restaurant_id, 
            total_amount=total_amount,
            order_status='Pending'  # Set initial status to 'Pending'
        )
        db.session.add(new_order)
        db.session.commit()

        order_items_details = []

        for item in cart_items:
            menu_item = FoodItem.query.get(item['item_id'])
            if not menu_item:
                raise ValueError(f"MenuItem with id {item['item_id']} does not exist.")

            original_price = menu_item.price   # Store the original price
            item_total_price = original_price * item['quantity']  # Calculate total price for this order item

            # Create the order item
            order_item = Order(
                order_id=new_order.order_id,
                item_id=item['item_id'],
                quantity=item['quantity'],
                price=item_total_price,  # Save the total price
            )
            db.session.add(order_item)

            # Append the order item details to the list
            order_items_details.append({
                'item_id': item['item_id'],
                'quantity': item['quantity'],
                'item_price': original_price,
                'total_price': item_total_price
            })

            # Add the item's total price to the total amount for the order
            total_amount += item_total_price

        # Update the total amount of the order
        new_order.total_amount = total_amount
        db.session.commit()

        # Clear the cart from the session
        session.pop(cart_key, None)

        return jsonify({
            'message': 'Order created successfully!',
            'order_id': new_order.order_id,
            'total_amount': total_amount,
            'address': user.address,
            'order_items': order_items_details
        }), 201 

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400