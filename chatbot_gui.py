import json
import random
import re
import sys
import requests
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton,
                             QLabel, QFrame, QScrollArea, QTextEdit, 
                             QComboBox, QSplitter, QSystemTrayIcon, 
                             QMenu, QAction, QStyle, QToolButton, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette, QMovie


class ChatBotWorker(QThread):
    """Worker thread to handle chatbot processing without freezing the GUI"""
    response_ready = pyqtSignal(str, str)  # response, message_type
    error_occurred = pyqtSignal(str)

    def __init__(self, chatbot, user_id, message):
        super().__init__()
        self.chatbot = chatbot
        self.user_id = user_id
        self.message = message

    def run(self):
        try:
            response, message_type = self.chatbot.process_query(self.user_id, self.message)
            self.response_ready.emit(response, message_type)
        except Exception as e:
            self.error_occurred.emit(str(e))


class AIChatBot:
    def __init__(self):
        self.name = "SupportBot"
        self.version = "2.0"
        self.greetings = [
            "Hello! How can I assist you today?",
            "Hi there! What can I help you with?",
            "Greetings! How may I be of service?"
        ]
        self.farewells = [
            "Goodbye! Have a great day!",
            "Thank you for chatting with us.再见!",
            "See you later! Feel free to return if you have more questions."
        ]

        # API keys will be injected from environment by run_chatbot.py
        self.api_keys = {
            "openweathermap": None,
            "newsapi": None,
            "exchange_rate": None,
        }

        # Predefined responses for common queries
        self.faq_responses = self.load_faq_responses()
        
        # Jokes database
        self.jokes = self.load_jokes()
        
        # Session data for each user
        self.sessions = {}
        
        # Supported currencies and their symbols
        self.currencies = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", 
            "CAD": "C$", "AUD": "A$", "INR": "₹", "CNY": "¥",
            "CHF": "Fr", "RUB": "₽", "BRL": "R$", "MXN": "$"
        }

    def load_faq_responses(self) -> Dict[str, List[str]]:
        """Load predefined FAQ responses from a JSON file"""
        try:
            with open('faq_responses.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "greeting": ["Hello! How can I help you today?", "Hi there! What can I assist you with?"],
                "farewell": ["Goodbye! Have a wonderful day!", "See you later! Thanks for chatting."],
                "help": ["I can help with account information, order status, payment issues, weather, news, currency conversion, calculations, jokes, and more!"],
                "account": [
                    "To access your account, please visit our website and click on 'Login'.",
                    "You can reset your password by clicking on 'Forgot Password' on the login page."
                ],
                "order": [
                    "To check your order status, I'll need your order number.",
                    "You can track your order using the tracking number sent to your email."
                ],
                "payment": [
                    "We accept credit cards, PayPal, and bank transfers.",
                    "For payment issues, please contact our billing department at billing@example.com."
                ],
                "features": [
                    "I can help with:\n- Account and order issues\n- Weather information\n- News updates\n- Currency conversion\n- Calculations\n- Telling jokes\n- Time and date information\n- And much more!",
                    "My capabilities include:\n- Answering FAQs\n- Providing weather forecasts\n- Sharing news headlines\n- Currency exchange rates\n- Basic calculations\n- Entertainment with jokes\n- Time and date queries"
                ],
                "default": [
                    "I'm not sure I understand. Could you please rephrase your question?",
                    "I don't have information about that yet. Would you like to speak with a human agent?",
                    "Let me connect you with a customer service representative for further assistance."
                ]
            }
    
    def load_jokes(self) -> List[str]:
        """Load jokes from a JSON file"""
        try:
            with open('jokes.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the scarecrow win an award? Because he was outstanding in his field!",
                "What do you call a fake noodle? An impasta!",
                "How does a penguin build its house? Igloos it together!",
                "Why did the math book look so sad? Because it had too many problems!",
                "What do you call a bear with no teeth? A gummy bear!",
                "How do you organize a space party? You planet!",
                "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a sleeping bull? A bulldozer!"
            ]

    def get_response(self, user_input: str) -> tuple:
        """Find the most appropriate response using keyword matching"""
        input_lower = user_input.lower()

        if any(word in input_lower for word in ['hello', 'hi', 'hey', 'greetings', 'hola']):
            return random.choice(self.faq_responses["greeting"]), "text"
        if any(word in input_lower for word in ['bye', 'goodbye', 'see you', 'farewell', 'adios']):
            return random.choice(self.faq_responses["farewell"]), "text"
        if any(word in input_lower for word in ['help', 'what can you do', 'support', 'features', 'capabilities']):
            return random.choice(self.faq_responses["features"]), "text"
        if any(word in input_lower for word in ['account', 'login', 'password', 'sign in', 'register']):
            return random.choice(self.faq_responses["account"]), "text"
        if any(word in input_lower for word in ['order', 'track', 'delivery', 'shipment', 'package']):
            return random.choice(self.faq_responses["order"]), "text"
        if any(word in input_lower for word in ['payment', 'pay', 'credit card', 'bill', 'invoice', 'refund']):
            return random.choice(self.faq_responses["payment"]), "text"
        if any(word in input_lower for word in ['joke', 'funny', 'laugh', 'humor']):
            return random.choice(self.jokes), "joke"
        if any(word in input_lower for word in ['thank', 'thanks', 'appreciate']):
            return "You're welcome! Is there anything else I can help you with?", "text"

        api_response, response_type = self.process_api_query(input_lower)
        if api_response:
            return api_response, response_type

        return random.choice(self.faq_responses["default"]), "text"

    def process_api_query(self, query: str) -> tuple:
        """Process queries that require API integration"""
        if any(word in query for word in ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloud']):
            return self.get_weather_data(query), "weather"
        if any(word in query for word in ['news', 'headlines', 'latest', 'update', 'headline']):
            return self.get_news_data(query), "news"
        if any(word in query for word in ['exchange', 'currency', 'convert', 'dollar', 'euro', 'pound', 'yen']):
            return self.get_exchange_rate(query), "currency"
        if any(word in query for word in ['time', 'date', 'clock', 'calendar', 'day']):
            return self.get_current_time(query), "time"
        if any(word in query for word in ['calculate', 'math', 'add', 'subtract', 'multiply', 'divide', 'square', 'root']):
            return self.calculate_expression(query), "calculation"
        return None, None

    def get_weather_data(self, query: str) -> str:
        """Get weather data from OpenWeatherMap API"""
        # Extract location from query
        location = "London"  # Default location
        words = query.split()
        for i, word in enumerate(words):
            if word in ['in', 'at', 'for', 'of'] and i + 1 < len(words):
                location = words[i + 1]
                # Handle multi-word locations
                if i + 2 < len(words) and words[i + 2] not in ['weather', 'temperature', 'forecast']:
                    location += " " + words[i + 2]
                break
        # If no location found, check for common city names
        if location == "London":
            cities = ['paris', 'new york', 'tokyo', 'berlin', 'moscow', 'beijing', 'sydney']
            for city in cities:
                if city in query:
                    location = city
                    break
        
        try:
            api_key = self.api_keys["openweathermap"]
            if not api_key:
                return "Please configure your OpenWeatherMap API key to get weather data."
            
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            description = data["weather"][0]["description"].capitalize()
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            city = data["name"]
            country = data["sys"]["country"]
            
            weather_icon = data["weather"][0]["icon"]
            icon_url = f"http://openweathermap.org/img/wn/{weather_icon}@2x.png"
            
            return (f"Weather in {city}, {country}:\n"
                   f"• Temperature: {temp}°C (feels like {feels_like}°C)\n"
                   f"• Conditions: {description}\n"
                   f"• Humidity: {humidity}%\n"
                   f"• Wind: {wind_speed} m/s\n"
                   f"• Icon: {icon_url}")
        except requests.exceptions.RequestException:
            return f"I couldn't fetch the weather data for {location}. Please try again later or check if the city name is correct."
        except Exception as e:
            return f"An error occurred while fetching weather data: {str(e)}"

    def get_news_data(self, query: str) -> str:
        """Get news data from NewsAPI"""
        category = "general"
        if any(word in query for word in ['sports', 'sport', 'football', 'basketball', 'tennis']):
            category = "sports"
        elif any(word in query for word in ['technology', 'tech', 'computer', 'software', 'ai']):
            category = "technology"
        elif any(word in query for word in ['business', 'economy', 'finance', 'market', 'stock']):
            category = "business"
        elif any(word in query for word in ['health', 'medical', 'medicine', 'hospital', 'doctor']):
            category = "health"
        elif any(word in query for word in ['entertainment', 'movie', 'music', 'celebrity', 'film']):
            category = "entertainment"
        elif any(word in query for word in ['science', 'scientific', 'research', 'discovery']):
            category = "science"
        
        try:
            api_key = self.api_keys["newsapi"]
            if not api_key:
                return "Please configure your NewsAPI key to get news data."
            
            url = f"https://newsapi.org/v2/top-headlines?category={category}&apiKey={api_key}&pageSize=5"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            
            if not articles:
                return f"No {category} news found right now. Please try another category."
            
            news_list = []
            for i, article in enumerate(articles[:3], 1):
                title = article['title']
                source = article['source']['name']
                # Shorten very long titles
                if len(title) > 100:
                    title = title[:100] + "..."
                news_list.append(f"{i}. {title} ({source})")
            
            return f"Here are the latest {category} news headlines:\n" + "\n".join(news_list)
        except requests.exceptions.RequestException:
            return "I couldn't fetch the latest news. Please check your internet connection or try again later."
        except Exception as e:
            return f"An error occurred while fetching news: {str(e)}"

    def get_exchange_rate(self, query: str) -> str:
        """Get currency exchange rates"""
        base_currency, target_currency = "USD", "EUR"
        
        # Extract currency codes from query
        words = query.upper().split()
        codes = list(self.currencies.keys())
        found = [w for w in words if w in codes]
        
        if len(found) >= 2:
            base_currency, target_currency = found[0], found[1]
        elif len(found) == 1:
            target_currency = found[0]
        else:
            # Try to find currency symbols or names
            currency_names = {
                "dollar": "USD", "euro": "EUR", "pound": "GBP", "yen": "JPY",
                "yuan": "CNY", "rupee": "INR", "ruble": "RUB", "franc": "CHF",
                "real": "BRL", "peso": "MXN"
            }
            
            for word in query.lower().split():
                if word in currency_names:
                    if base_currency == "USD":
                        base_currency = currency_names[word]
                    else:
                        target_currency = currency_names[word]
                        break
        
        try:
            api_key = self.api_keys["exchange_rate"]
            if not api_key:
                return "Please configure your ExchangeRate API key to get currency data."
            
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{base_currency}/{target_currency}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["result"] == "success":
                rate = data["conversion_rate"]
                base_symbol = self.currencies.get(base_currency, base_currency)
                target_symbol = self.currencies.get(target_currency, target_currency)
                
                return (f"Exchange Rate:\n"
                       f"• {base_currency} ({base_symbol}) to {target_currency} ({target_symbol})\n"
                       f"• Rate: 1 {base_currency} = {rate:.4f} {target_currency}\n"
                       f"• Last updated: {data['time_last_update_utc']}")
            else:
                return "Sorry, I couldn't retrieve the exchange rate at the moment."
        except requests.exceptions.RequestException:
            return "I couldn't fetch the exchange rate. Please check your internet connection or try again later."
        except Exception as e:
            return f"An error occurred while fetching exchange rates: {str(e)}"

    def get_current_time(self, query: str) -> str:
        location = "your location"
        words = query.split()
        for i, word in enumerate(words):
            if word in ['in', 'at', 'for', 'of'] and i + 1 < len(words):
                location = words[i + 1]
                # Handle multi-word locations
                if i + 2 < len(words) and words[i + 2] not in ['time', 'date']:
                    location += " " + words[i + 2]
                break
        
        now = datetime.now()
        
        # Add timezone information if location is a known city
        timezone_info = ""
        if "london" in location.lower():
            timezone_info = " (GMT+0/BST)"
        elif "new york" in location.lower():
            timezone_info = " (EST/EDT)"
        elif "tokyo" in location.lower():
            timezone_info = " (JST)"
        
        return (f"Current time in {location.title()}{timezone_info}:\n"
               f"• Time: {now.strftime('%H:%M:%S')}\n"
               f"• Date: {now.strftime('%A, %B %d, %Y')}\n"
               f"• UTC: {datetime.utcnow().strftime('%H:%M:%S')}")

    def calculate_expression(self, query: str) -> str:
        try:
            # Extract numbers and operators
            numbers = []
            operators = []
            
            # Convert words to numbers and operators
            word_to_number = {
                'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
                'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
                'ten': 10, 'plus': '+', 'minus': '-', 'times': '*', 'multiplied': '*',
                'divided': '/', 'by': '', 'over': '/', 'add': '+', 'subtract': '-',
                'multiply': '*', 'divide': '/'
            }
            
            # Clean the query
            clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
            words = clean_query.split()
            
            # Convert words to numbers and operators
            for word in words:
                if word in word_to_number:
                    item = word_to_number[word]
                    if isinstance(item, int):
                        numbers.append(str(item))
                    elif item:  # Skip empty strings
                        operators.append(item)
                elif word.isdigit():
                    numbers.append(word)
            
            # If we have numbers and operators, build expression
            if numbers and operators:
                # Simple case: two numbers and one operator
                if len(numbers) >= 2 and len(operators) >= 1:
                    expression = f"{numbers[0]} {operators[0]} {numbers[1]}"
                    result = eval(expression)
                    return f"Calculation: {expression} = {result}"
            
            # Try to find mathematical expressions in the text
            if 'square root of' in query:
                num = None
                for word in words:
                    if word.isdigit():
                        num = float(word)
                        break
                if num is not None and num >= 0:
                    result = math.sqrt(num)
                    return f"Square root of {num} is {result:.4f}"
            
            if 'power' in query or '^' in query:
                nums = [float(word) for word in words if word.isdigit()]
                if len(nums) >= 2:
                    result = math.pow(nums[0], nums[1])
                    return f"{nums[0]} to the power of {nums[1]} is {result:.4f}"
            
            # Try to evaluate any mathematical expression in the query
            math_expr = re.findall(r'(\d+\.?\d*[\+\-\*\/]\d+\.?\d*)', query)
            if math_expr:
                try:
                    result = eval(math_expr[0])
                    return f"Calculation: {math_expr[0]} = {result}"
                except:
                    pass
            
            return "I couldn't understand the calculation request. Please try phrasing it differently."
        except ZeroDivisionError:
            return "Error: Division by zero is not allowed."
        except Exception as e:
            return f"I couldn't perform that calculation: {str(e)}"

    def process_query(self, user_id: str, user_input: str) -> tuple:
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "history": [], 
                "created_at": datetime.now(),
                "message_count": 0
            }
        
        self.sessions[user_id]["history"].append({
            "query": user_input, 
            "timestamp": datetime.now(),
            "type": "user"
        })
        self.sessions[user_id]["message_count"] += 1
        
        response, response_type = self.get_response(user_input)
        
        self.sessions[user_id]["history"].append({
            "response": response, 
            "timestamp": datetime.now(),
            "type": "bot",
            "response_type": response_type
        })
        
        return response, response_type

    def get_session_history(self, user_id: str) -> List[Dict]:
        return self.sessions.get(user_id, {}).get("history", [])

    def clear_session(self, user_id: str):
        if user_id in self.sessions:
            del self.sessions[user_id]


class MessageWidget(QWidget):
    def __init__(self, text, is_user, timestamp=None, message_type="text"):
        super().__init__()
        self.is_user = is_user
        self.text = text
        self.timestamp = timestamp or datetime.now()
        self.message_type = message_type
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        bubble = QFrame()
        bubble.setFrameStyle(QFrame.Panel | QFrame.Raised)
        bubble.setLineWidth(1)
        bubble.setMaximumWidth(400)
        bubble.setStyleSheet(self.get_bubble_style())
        bubble_layout = QVBoxLayout(bubble)

        message_label = QLabel(self.text)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(self.get_text_style())
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        time_str = self.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setAlignment(Qt.AlignRight)
        time_label.setStyleSheet("color: gray; font-size: 10px; padding: 0 5px 5px 0;")

        bubble_layout.addWidget(message_label)
        bubble_layout.addWidget(time_label)

        if self.is_user:
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            layout.addWidget(bubble)
            layout.addStretch()

        self.setLayout(layout)

    def get_bubble_style(self):
        if self.is_user:
            return """
                QFrame {
                    background-color: #dcf8c6; 
                    border-radius: 15px; 
                    padding: 10px; 
                    margin: 5px;
                    border: 1px solid #b3e0a6;
                }
            """
        else:
            if self.message_type == "joke":
                return """
                    QFrame {
                        background-color: #fff9c4; 
                        border-radius: 15px; 
                        padding: 10px; 
                        margin: 5px;
                        border: 1px solid #ffe082;
                    }
                """
            elif self.message_type == "weather":
                return """
                    QFrame {
                        background-color: #bbdefb; 
                        border-radius: 15px; 
                        padding: 10px; 
                        margin: 5px;
                        border: 1px solid #90caf9;
                    }
                """
            elif self.message_type == "news":
                return """
                    QFrame {
                        background-color: #c8e6c9; 
                        border-radius: 15px; 
                        padding: 10px; 
                        margin: 5px;
                        border: 1px solid #a5d6a7;
                    }
                """
            elif self.message_type == "currency":
                return """
                    QFrame {
                        background-color: #e1bee7; 
                        border-radius: 15px; 
                        padding: 10px; 
                        margin: 5px;
                        border: 1px solid #ce93d8;
                    }
                """
            elif self.message_type == "calculation":
                return """
                    QFrame {
                        background-color: #ffcc80; 
                        border-radius: 15px; 
                        padding: 10px; 
                        margin: 5px;
                        border: 1px solid #ffb74d;
                    }
                """
            else:
                return """
                    QFrame {
                        background-color: #ffffff; 
                        border-radius: 15px; 
                        padding: 10px; 
                        margin: 5px;
                        border: 1px solid #e0e0e0;
                    }
                """

    def get_text_style(self):
        if self.message_type == "joke":
            return "color: #5d4037; padding: 5px; font-style: italic;"
        else:
            return "color: #000000; padding: 5px;"


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chatbot = AIChatBot()
        self.user_id = f"user_gui_{random.randint(1000, 9999)}"
        self.dark_mode = False
        self.init_ui()
        self.show_welcome_message()
        
        # Create system tray icon
        self.create_system_tray()

    def create_system_tray(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            
            tray_menu = QMenu()
            restore_action = tray_menu.addAction("Restore")
            quit_action = tray_menu.addAction("Quit")
            
            restore_action.triggered.connect(self.show)
            quit_action.triggered.connect(QApplication.quit)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self.tray_icon.activated.connect(self.tray_icon_activated)
        
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def init_ui(self):
        self.setWindowTitle('AI Customer Support Chatbot')
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border: none;
            }
            QLabel {
                color: white;
                padding: 10px;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 10px;
                text-align: left;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #4a6278;
            }
            QPushButton:pressed {
                background-color: #2c3e50;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # App title in sidebar
        title = QLabel("AI SupportBot")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("QLabel {font-size: 16px; font-weight: bold; padding: 15px;}")
        sidebar_layout.addWidget(title)
        
        # Add sidebar buttons
        self.quick_actions = [
            ("Account Help", "What can you help me with my account?"),
            ("Order Status", "How can I check my order status?"),
            ("Payment Issues", "I have a problem with my payment"),
            ("Weather", "What's the weather in London?"),
            ("Latest News", "Show me the latest technology news"),
            ("Currency Conversion", "Convert USD to EUR"),
            ("Tell me a joke", "Tell me a joke")
        ]
        
        for action, query in self.quick_actions:
            btn = QPushButton(action)
            btn.clicked.connect(lambda checked, q=query: self.send_quick_query(q))
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # Theme toggle button
        self.theme_btn = QPushButton("Switch to Dark Mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        sidebar_layout.addWidget(self.theme_btn)
        
        # Add sidebar to main layout
        main_layout.addWidget(sidebar)

        # Create chat area
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        
        # Chat title
        title = QLabel("AI Customer Support")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("QLabel {font-size: 18px; font-weight: bold; padding: 10px; background-color: #3498db; color: white; border-radius: 5px;}")
        chat_layout.addWidget(title)

        # Chat area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.chat_container)
        chat_layout.addWidget(self.scroll_area)

        # Typing indicator
        self.typing_indicator = QLabel("SupportBot is typing...")
        self.typing_indicator.setAlignment(Qt.AlignLeft)
        self.typing_indicator.setStyleSheet("QLabel {color: gray; font-style: italic; padding: 5px; background-color: #f0f0f0; border-radius: 5px;}")
        self.typing_indicator.hide()
        
        # Create typing animation
        self.typing_movie = QMovie(":img/typing.gif")  # Using resource file for typing animation
        if not self.typing_movie.isValid():
            # Fallback if GIF not available
            self.typing_indicator.setMovie(None)
        else:
            self.typing_indicator.setMovie(self.typing_movie)
        
        chat_layout.addWidget(self.typing_indicator)

        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        
        self.send_button = QPushButton()
        self.send_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.send_button.setIconSize(QSize(20, 20))
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db; 
                color: white; 
                border: none; 
                padding: 10px; 
                border-radius: 5px;
                min-width: 50px;
            } 
            QPushButton:hover {
                background-color: #2980b9;
            } 
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        chat_layout.addWidget(input_widget)
        
        # Add chat container to main layout
        main_layout.addWidget(chat_container, 1)  # 1 is stretch factor

    def show_welcome_message(self):
        welcome_msg = ("Hello! I'm your AI customer support assistant. I can help you with:\n"
                       "- Account information and login issues\n"
                       "- Order status and tracking\n"
                       "- Payment and billing questions\n"
                       "- Weather information\n"
                       "- News updates\n"
                       "- Currency exchange rates\n"
                       "- Simple calculations\n"
                       "- Jokes and entertainment\n"
                       "- And much more!\n\n"
                       "How can I help you today?")
        self.add_message(welcome_msg, False, "text")

    def add_message(self, text, is_user, message_type="text", timestamp=None):
        msg_widget = MessageWidget(text, is_user, timestamp, message_type)
        self.chat_layout.addWidget(msg_widget)
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def show_typing_indicator(self, show=True):
        self.typing_indicator.setVisible(show)
        if show and self.typing_movie.isValid():
            self.typing_movie.start()
        elif self.typing_movie.isValid():
            self.typing_movie.stop()
            
        if show:
            QTimer.singleShot(100, self.scroll_to_bottom)

    def send_message(self):
        message = self.input_field.text().strip()
        if not message: 
            return
            
        self.add_message(message, True)
        self.input_field.clear()
        self.show_typing_indicator(True)
        
        self.worker = ChatBotWorker(self.chatbot, self.user_id, message)
        self.worker.response_ready.connect(self.handle_bot_response)
        self.worker.error_occurred.connect(self.handle_bot_error)
        self.worker.start()

    def send_quick_query(self, query):
        self.input_field.setText(query)
        self.send_message()

    def handle_bot_response(self, response, message_type):
        self.show_typing_indicator(False)
        self.add_message(response, False, message_type)
        
        if any(word in response.lower() for word in ['goodbye', 'bye', 'see you']):
            QTimer.singleShot(2000, self.disable_input)

    def handle_bot_error(self, error_msg):
        self.show_typing_indicator(False)
        self.add_message(f"Sorry, I encountered an error: {error_msg}", False, "text")

    def disable_input(self):
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.input_field.setPlaceholderText("Chat has ended. Please close the window.")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            self.set_dark_theme()
            self.theme_btn.setText("Switch to Light Mode")
        else:
            self.set_light_theme()
            self.theme_btn.setText("Switch to Dark Mode")

    def set_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        self.setPalette(dark_palette)
        
        # Update specific widget styles
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #252525; }")
        self.chat_container.setStyleSheet("QWidget { background-color: #252525; }")
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #555;
                border-radius: 5px;
                font-size: 14px;
                background-color: #353535;
                color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)

    def set_light_theme(self):
        self.setPalette(self.style().standardPalette())
        
        # Reset specific widget styles
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.chat_container.setStyleSheet("QWidget { background-color: white; }")
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)

    def closeEvent(self, event):
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("AI Customer Support Chatbot")
    app.setApplicationVersion("2.0")
    
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()