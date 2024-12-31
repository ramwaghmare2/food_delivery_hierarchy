import os
from datetime import datetime ,timezone
from flask import Flask, session, current_app ,render_template, flash,redirect, url_for
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from models import db
from utils.services import today_sale
from models.royalty import RoyaltyWallet

# Declare global variables
socketio = SocketIO(cors_allowed_origins="*", ping_interval=25, ping_timeout=10)
bcrypt = Bcrypt()
shared_session_store = {}

def create_app():
    app = Flask(__name__, static_url_path='/static', static_folder='static')
    app.config.from_object('config.Config')
    app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")

    # Initialize extensions
    socketio.init_app(app)
    app.socketio = socketio
    bcrypt.init_app(app)
    db.init_app(app)
    Migrate(app, db)

    # Initialize scheduler within create_app
    scheduler = BackgroundScheduler()

    def save_role_shares_in_memory(user_id, role_shares_with_names):
        """
        Save role shares in the shared memory store for use by the scheduler.
        """
        shared_session_store[user_id] = role_shares_with_names

    def send_wallet_shares():
        """
        Function to send shares to wallets, executed by the scheduler.
        """
        # Ensure the app context is available
        with app.app_context():  # Use app's app context directly
            for user_id, role_shares_with_names in shared_session_store.items():
                # Retrieve today's total sales for the user
                today_total_sales = today_sale(user_id)

                for role, data in role_shares_with_names.items():
                    share = data['share']
                    entity_id = data['id']

                    # Always create a new wallet entry for each transaction
                    wallet = RoyaltyWallet(
                        entity_id=entity_id,
                        role=role,
                        royalty_amount=share,
                        updated_at=datetime.now(timezone.utc) # Set the creation timestamp
                    )
                    db.session.add(wallet)

                db.session.commit()  # Save changes to the database

                # Clear the shared session store after processing
                with app.test_request_context():  # Create a request context to work with session
                    session.pop('role_shares', None)  # Removes role_shares from session
                    session.modified = True
                    print("sessison cleared successfully")

    # Schedule the task to run at 5:50 PM daily
    scheduler.add_job(send_wallet_shares, 'cron', hour=1, minute=1)

    # Start the scheduler
    scheduler.start()

    # Register blueprints
    from routes import create_app_routes
    create_app_routes(app)

    # Provide a way to save session data into the shared store during requests
    @app.route('/save_role_shares', methods=['GET'])
    def save_role_shares():
        """
        API endpoint to save role shares into the in-memory shared session store.
        """
        user_id = session.get('user_id')  # Replace with actual logic for fetching user ID
        role_shares_with_names = session.get('role_shares')  # Replace with session logic

        if user_id and role_shares_with_names:
            save_role_shares_in_memory(user_id, role_shares_with_names)
            flash("Kitchen is closed.", 'success')  # Flash success message
        else:
            flash("Missing data.", 'error')  # Flash error message

        return redirect(url_for('kitchen.kitchen_home'))

    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(app, debug=True)
