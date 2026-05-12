from routes.profile_routes import profile_bp

"""
Smart Navigator - Main Application Entry Point
A travel exploration web app built with Flask + SQLite database
"""

import os
import webbrowser
from threading import Timer
from datetime import timedelta
from flask import Flask, render_template, g
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.places_routes import places_bp
from routes.reviews_routes import reviews_bp
from routes.profile_routes import profile_bp
from routes.user_places_routes import user_places_bp
from routes.otp_routes import otp_bp
from routes.email_routes import email_bp


def create_app():
    """Application factory pattern."""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # ─── Configuration ────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smart_navigator_secret_2024_dev')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static/images/places')
    app.config['DATABASE'] = 'database/smart_navigator.db'
    
    # ─── Initialize SQLite Database ───────────────────────────────────────────
    from utils.sql_db import init_db
    with app.app_context():
        init_db(app.config['DATABASE'])

    # ─── Register Blueprints ──────────────────────────────────────────────────
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(places_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(user_places_bp)
    app.register_blueprint(otp_bp)
    app.register_blueprint(email_bp)

    # ─── Template Context Processors ─────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        """Inject app-wide variables into all templates."""
        from utils.auth_helper import get_current_user
        return {
            'app_name': 'Smart Navigator',
            'current_user': get_current_user()
        }

    # ─── Error Handlers ───────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
    
    # ─── Close Database Connection ────────────────────────────────────────────
    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # ─── Ensure Upload Dirs Exist ──────────────────────────────────────────────
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static/images/hotels'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static/images/avatars'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)

    return app


app = create_app()

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════╗
║       🧭  SMART NAVIGATOR  🧭             ║
║   Travel Exploration Web App              ║
║   Running at: http://127.0.0.1:5000       ║
╚═══════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)
    
    def open_browser():
        webbrowser.open('http://127.0.0.1:5000')
    
    # Open browser after 1 second delay
    Timer(1, open_browser).start()
    
    app.run(debug=True)