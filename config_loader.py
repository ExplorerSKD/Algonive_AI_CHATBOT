# config_loader.py
import os
from dotenv import load_dotenv

def load_api_keys():
    """Load API keys from environment variables"""
    load_dotenv()  # Load environment variables from .env file
    
    return {
        "openweathermap": os.getenv("bd5e378503939ddaee76f12ad7a97608"),
        "newsapi": os.getenv("293cafc942454bbd90950b7816acd37a"),
        "exchange_rate": os.getenv("e778d625f6319de9c68586b5")
    }