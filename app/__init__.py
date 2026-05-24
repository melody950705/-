import os
import sqlite3
from flask import Flask
from config import Config

def create_app(config_class=Config):
    """
    Flask Application Factory
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register Blueprints
    from app.routes import main_bp, bus_bp, driver_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(bus_bp)
    app.register_blueprint(driver_bp)

    return app

def init_db():
    """
    Initializes the SQLite database with database/schema.sql
    And seeds a default driver if the drivers table is empty.
    """
    import sqlite3
    from werkzeug.security import generate_password_hash
    
    db_path = 'instance/database.db'
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    schema_path = 'database/schema.sql'
    if not os.path.exists(schema_path):
        # Fallback to check relative to package
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../database/schema.sql')

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    
    # Check if we have any drivers
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM drivers")
    count = cursor.fetchone()[0]
    if count == 0:
        hashed = generate_password_hash("123456")
        cursor.execute(
            "INSERT INTO drivers (username, password_hash, name) VALUES (?, ?, ?)",
            ("driver01", hashed, "王大明")
        )
        conn.commit()
        print("Default driver 'driver01' (password: 123456) seeded successfully.")
        
    conn.close()
    print("Database initialized successfully at instance/database.db.")
