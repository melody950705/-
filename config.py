import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
    DATABASE = os.environ.get('DATABASE', 'instance/database.db')
    
    # TDX API configuration (for bus tracking data)
    TDX_CLIENT_ID = os.environ.get('TDX_CLIENT_ID', '')
    TDX_CLIENT_SECRET = os.environ.get('TDX_CLIENT_SECRET', '')
