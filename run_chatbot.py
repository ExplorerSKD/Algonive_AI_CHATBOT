# run_chatbot.py
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables FIRST
load_dotenv()

# Now import your main module
from chatbot_gui import AIChatBot, main 
original_init = AIChatBot.__init__

def new_init(self):
    original_init(self)
    # Override API keys with environment variables
    self.api_keys = {
        "openweathermap": os.getenv("OPENWEATHERMAP_API_KEY"),
        "newsapi": os.getenv("NEWSAPI_KEY"),
        "exchange_rate": os.getenv("EXCHANGERATE_API_KEY"),
    }
    
    # Validate API keys
    self.validate_api_keys()

# Add validation method to the class
def validate_api_keys(self):
    """Check if API keys are properly configured"""
    missing_keys = []
    for service, key in self.api_keys.items():
        if not key:
            missing_keys.append(service)
    
    if missing_keys:
        print(f"Warning: The following API keys are missing: {', '.join(missing_keys)}")
        print("Please check your .env file")

# Attach methods to AIChatBot
AIChatBot.validate_api_keys = validate_api_keys
AIChatBot.__init__ = new_init

# Run the application
if __name__ == "__main__":
    main()
