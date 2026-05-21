import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DATABASE = os.path.join(BASE_DIR, os.environ.get('DATABASE_PATH') or 'instance/database.db')
    
    # TDX API credentials
    TDX_CLIENT_ID = os.environ.get('TDX_CLIENT_ID')
    TDX_CLIENT_SECRET = os.environ.get('TDX_CLIENT_SECRET')
