import os
import sqlite3
from flask import Flask, g
from config import Config

def create_app(config_class=Config):
    # Create the Flask application instance
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Database teardown
    @app.teardown_appcontext
    def close_db_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.bus import bus_bp
    from app.routes.driver import driver_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(bus_bp, url_prefix='/bus')
    app.register_blueprint(driver_bp, url_prefix='/driver')

    return app

def get_db():
    """Helper to open a database connection if not already present in the request context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(Config.DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database using database/schema.sql."""
    # Find the schema.sql file relative to the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, 'database', 'schema.sql')
    
    # Ensure the instance directory exists for the database file
    db_path = Config.DATABASE
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    print(f"Initializing database at: {db_path}")
    print(f"Using schema file: {schema_path}")

    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized successfully.")
