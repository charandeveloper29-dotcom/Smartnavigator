"""Smart Navigator — Flask Application with SQLite Database"""
import os
from flask import Flask, render_template, session, g
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database initialization
from utils.sql_db import init_db, get_db

# Import blueprints
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.places_routes import places_bp
from routes.email_routes import email_bp
from routes.reviews_routes import reviews_bp
from routes.user_places_routes import user_places_bp
from routes.profile_routes import profile_bp

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.getenv('SECRET_KEY', 'smartnavigator2026')
    app.config['DATABASE'] = 'database/smart_navigator.db'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(places_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(user_places_bp)
    app.register_blueprint(profile_bp)
    
    # Close database connection after each request
    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db', None)
        if db is not None:
            db.close()
    
    return app

if __name__ == '__main__':
    app = create_app()
    print('[APP] Smart Navigator starting...')
    print('[APP] Open: http://127.0.0.1:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)