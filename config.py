# config.py
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
GPT_API_KEY = os.getenv('GPT_KEY')
