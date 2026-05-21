import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-taichung-bus-2.0')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'instance/database.db')
    TDX_CLIENT_ID = os.environ.get('TDX_CLIENT_ID', '')
    TDX_CLIENT_SECRET = os.environ.get('TDX_CLIENT_SECRET', '')
