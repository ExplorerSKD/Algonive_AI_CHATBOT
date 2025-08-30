# chatbot_wrapper.py
from config_loader import load_api_keys

class AIChatBotWrapper:
    def __init__(self, original_chatbot):
        self.original_chatbot = original_chatbot
        self.api_keys = load_api_keys()
        
        # Override the API keys in the original chatbot
        self.original_chatbot.api_keys = self.api_keys
        
        # Validate API keys
        self.validate_api_keys()
    
    def validate_api_keys(self):
        """Check if API keys are properly configured"""
        for service, key in self.api_keys.items():
            if not key:
                print(f"Warning: {service} API key not found in environment variables")
    
    def __getattr__(self, name):
        """Delegate all other attributes/methods to the original chatbot"""
        return getattr(self.original_chatbot, name)