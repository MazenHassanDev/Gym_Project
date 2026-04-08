import os
from dotenv import load_dotenv

load_dotenv()

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')
NAME = os.getenv('DB_NAME')
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')

DATABASE_URL = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}"