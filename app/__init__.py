import os
import sqlite3
from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure the instance path exists
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
    db_path = Config.DATABASE_PATH
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized successfully.")
