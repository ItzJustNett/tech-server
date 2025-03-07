import os
import logging
import tempfile
import time
import io
from pathlib import Path
import json
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from yt_dlp import YoutubeDL

# Import components from existing code
from app import AudioTranscriber
from stt import WhisperTranscriber
from web import WebSearchAI
from gtts import gTTS
from pdf_converter import text_to_pdffrom flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import os
import json
import uuid
import io
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import tempfile
from pathlib import Path
import logging
import requests
import time
import sys
import shutil
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import random

# Import bot-related modules
from stt import WhisperTranscriber
from app import AudioTranscriber
from web import WebSearchAI
from pdf_converter import text_to_pdf
from gtts import gTTS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev_secret_key'
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=30)

# Get API keys from environment variables
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Initialize transcribers, web search, etc.
audio_transcriber = AudioTranscriber()
voice_transcriber = WhisperTranscriber(model_name="openai/whisper-small")
web_search_ai = WebSearchAI()

# Default AI model
DEFAULT_AI_MODEL = "google/gemini-2.0-flash-exp:free"

# Available AI models with descriptions
AI_MODELS = {
    "nousresearch/deephermes-3-llama-3-8b-preview:free": "Optimized for fast processing with good comprehension",
    "cognitivecomputations/dolphin3.0-r1-mistral-24b:free": "Great for creative writing and detailed explanations",
    "google/gemini-2.0-flash-lite-preview-02-05:free": "Fast responses with Google's knowledge foundation",
    "qwen/qwen-vl-plus:free": "Excellent multilingual capabilities and cultural understanding",
    "google/gemini-2.0-pro-exp-02-05:free": "Advanced reasoning and detailed knowledge base",
    "qwen/qwen2.5-vl-72b-instruct:free": "Superior at following complex instructions and detailed analysis",
    "deepseek/deepseek-r1-distill-llama-70b:free": "Balance of speed and accuracy with expansive knowledge",
    "deepseek/deepseek-r1:free": "Excellent for academic and technical content",
    "deepseek/deepseek-chat:free": "Optimized for conversational and quick responses",
    "google/gemini-2.0-flash-thinking-exp-1219:free": "Enhanced reasoning with fast response time",
    "qwen/qwen-2.5-coder-32b-instruct:free": "Specializes in programming and technical documentation",
    "mistralai/mistral-nemo:free": "Balanced performance across a wide range of topics",
    "google/gemini-2.0-flash-exp:free": "Fast, balanced model with good general knowledge (Default)"
}

# In-memory data storage (replace with database in production)
users = {}
subjects = {}
courses = {}
user_progress = {}
lessons = {}
exercises = {}
achievements = {}
user_models = {}  # Dictionary to store user model preferences
user_urls = {}    # Dictionary to store user URLs for transcription

# New data structures for garden and economy system
gardens = {}      # User gardens
inventory = {}    # User inventories
shop_items = {}   # Shop items
economy = {}      # User gem balances and transactions
helpers = {}      # User helpers/robots

# ===== PLANT DATA MODELS =====
# Define different plant types with properties
PLANT_TYPES = {
    "sunflower": {
        "name": "Sunflower",
        "icon": "🌻",
        "description": "A cheerful plant that grows quickly",
        "growth_time": 3,  # Days to full growth
        "max_health": 5,   # Days without water before dying
        "xp_reward": 50,   # XP earned when harvested
        "gem_reward": 10,  # Gems earned when harvested
        "seed_cost": 15,   # Cost to buy a seed
        "levels": [
            {"name": "Seed", "icon": "🌱", "days": 0},
            {"name": "Sprout", "icon": "🌿", "days": 1},
            {"name": "Young", "icon": "🌱🌻", "days": 2},
            {"name": "Mature", "icon": "🌻", "days": 3}
        ]
    },
    "rose": {
        "name": "Rose",
        "icon": "🌹",
        "description": "Beautiful but needs more care",
        "growth_time": 5,
        "max_health": 3,
        "xp_reward": 100,
        "gem_reward": 20,
        "seed_cost": 30,
        "levels": [
            {"name": "Seed", "icon": "🌱", "days": 0},
            {"name": "Sprout", "icon": "🌿", "days": 1},
            {"name": "Bud", "icon": "🌱🌹", "days": 3},
            {"name": "Mature", "icon": "🌹", "days": 5}
        ]
    },
    "cactus": {
        "name": "Cactus",
        "icon": "🌵",
        "description": "Resilient plant that's hard to kill",
        "growth_time": 7,
        "max_health": 10,
        "xp_reward": 150,
        "gem_reward": 25,
        "seed_cost": 40,
        "levels": [
            {"name": "Seed", "icon": "🌱", "days": 0},
            {"name": "Tiny Cactus", "icon": "🪴", "days": 2},
            {"name": "Growing", "icon": "🌱🌵", "days": 5},
            {"name": "Mature", "icon": "🌵", "days": 7}
        ]
    },
    "tree": {
        "name": "Tree",
        "icon": "🌳",
        "description": "Slow growing but provides ongoing rewards",
        "growth_time": 10,
        "max_health": 7,
        "xp_reward": 300,
        "gem_reward": 50,
        "seed_cost": 100,
        "levels": [
            {"name": "Seed", "icon": "🌱", "days": 0},
            {"name": "Sapling", "icon": "🌱🌿", "days": 3},
            {"name": "Young Tree", "icon": "🌴", "days": 7},
            {"name": "Mature", "icon": "🌳", "days": 10}
        ]
    },
    "bonsai": {
        "name": "Bonsai",
        "icon": "🪴",
        "description": "Artful plant that provides special bonuses",
        "growth_time": 14,
        "max_health": 4,
        "xp_reward": 500,
        "gem_reward": 100,
        "seed_cost": 200,
        "levels": [
            {"name": "Seed", "icon": "🌱", "days": 0},
            {"name": "Seedling", "icon": "🌱🪴", "days": 5},
            {"name": "Shaped", "icon": "🪴", "days": 10},
            {"name": "Mature", "icon": "🪴", "days": 14}
        ]
    }
}

# ===== SHOP ITEM DATA MODELS =====
# Define shop items
SHOP_ITEMS = {
    # Seeds
    "sunflower_seed": {
        "id": "sunflower_seed",
        "name": "Sunflower Seed",
        "description": "Plant a cheerful sunflower",
        "icon": "🌻",
        "category": "seeds",
        "price": 15,
        "type": "plant",
        "plant_type": "sunflower"
    },
    "rose_seed": {
        "id": "rose_seed",
        "name": "Rose Seed",
        "description": "Plant a beautiful rose",
        "icon": "🌹",
        "category": "seeds",
        "price": 30,
        "type": "plant",
        "plant_type": "rose"
    },
    "cactus_seed": {
        "id": "cactus_seed",
        "name": "Cactus Seed",
        "description": "Plant a resilient cactus",
        "icon": "🌵",
        "category": "seeds",
        "price": 40,
        "type": "plant",
        "plant_type": "cactus"
    },
    "tree_seed": {
        "id": "tree_seed",
        "name": "Tree Seed",
        "description": "Plant a strong tree",
        "icon": "🌳",
        "category": "seeds",
        "price": 100,
        "type": "plant",
        "plant_type": "tree"
    },
    "bonsai_seed": {
        "id": "bonsai_seed",
        "name": "Bonsai Seed",
        "description": "Plant an artful bonsai",
        "icon": "🪴",
        "category": "seeds",
        "price": 200,
        "type": "plant",
        "plant_type": "bonsai"
    },
    
    # Helpers
    "basic_robot": {
        "id": "basic_robot",
        "name": "Basic Robot Gardener",
        "description": "Waters your plants for up to 1 day while you're away",
        "icon": "🤖",
        "category": "helpers",
        "price": 500,
        "type": "helper",
        "effect": {
            "type": "auto_water",
            "duration": 1  # days
        }
    },
    "advanced_robot": {
        "id": "advanced_robot",
        "name": "Advanced Robot Gardener",
        "description": "Waters your plants for up to 2 days while you're away",
        "icon": "🤖",
        "category": "helpers",
        "price": 1000,
        "type": "helper",
        "effect": {
            "type": "auto_water",
            "duration": 2  # days
        }
    },
    
    # Tools
    "fertilizer": {
        "id": "fertilizer",
        "name": "Fertilizer",
        "description": "Speeds up plant growth for 1 day",
        "icon": "💩",
        "category": "tools",
        "price": 50,
        "type": "consumable",
        "effect": {
            "type": "growth_boost",
            "multiplier": 2,
            "duration": 1  # days
        }
    },
    "super_fertilizer": {
        "id": "super_fertilizer",
        "name": "Super Fertilizer",
        "description": "Greatly speeds up plant growth for 1 day",
        "icon": "💩✨",
        "category": "tools",
        "price": 100,
        "type": "consumable",
        "effect": {
            "type": "growth_boost",
            "multiplier": 3,
            "duration": 1  # days
        }
    },
    "watering_can": {
        "id": "watering_can",
        "name": "Watering Can",
        "description": "Increases the health recovery when watering",
        "icon": "🚿",
        "category": "tools",
        "price": 150,
        "type": "permanent",
        "effect": {
            "type": "water_boost",
            "multiplier": 1.5
        }
    },
    
    # Decorations
    "garden_fence": {
        "id": "garden_fence",
        "name": "Garden Fence",
        "description": "A decorative fence for your garden",
        "icon": "🧱",
        "category": "decorations",
        "price": 300,
        "type": "decoration",
        "effect": {
            "type": "aesthetic"
        }
    },
    "stone_path": {
        "id": "stone_path",
        "name": "Stone Path",
        "description": "A beautiful stone path for your garden",
        "icon": "🪨",
        "category": "decorations",
        "price": 250,
        "type": "decoration",
        "effect": {
            "type": "aesthetic"
        }
    }
}

# Initialize shop items
for item_id, item in SHOP_ITEMS.items():
    shop_items[item_id] = item

# Helper function to generate AI responses with OpenRouter
def generate_ai_response(prompt, user_id=None):
    # Determine which model to use
    model = DEFAULT_AI_MODEL
    if user_id and user_id in user_models:
        model = user_models[user_id]
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://personallearningbot.com",  # Replace with your domain
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            # Extract model name for logging/display
            used_model = result.get("model", model).split("/")[-1].split(":")[0]
            response_content = result["choices"][0]["message"]["content"]
            return f"[{used_model}] {response_content}"
        else:
            return "Sorry, I couldn't generate a response."
    except Exception as e:
        logger.error(f"Error generating AI response with model {model}: {e}")
        return f"Error generating response with {model.split('/')[-1]}: {str(e)}"

# Helper functions
def generate_token(user_id):
    """Generate JWT token for authentication"""
    payload = {
        'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA'],
        'iat': datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def authenticate(token):
    """Validate JWT token and return user_id"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_progress(user_id):
    """Get or initialize user progress"""
    if user_id not in user_progress:
        user_progress[user_id] = {
            'courses': {},
            'xp': 0,
            'achievements': []
        }
    return user_progress[user_id]

# NEW HELPER FUNCTIONS FOR GARDEN & ECONOMY SYSTEM

def get_user_garden(user_id):
    """Get or initialize user garden"""
    if user_id not in gardens:
        gardens[user_id] = {
            'plots': [],  # Empty garden plots initially
            'last_watered': datetime.utcnow().strftime('%Y-%m-%d'),
            'level': 1,   # Garden level determines number of available plots
            'decorations': []  # Decorations placed in the garden
        }
        
        # Initialize with 2 plots for new gardens
        for i in range(2):
            gardens[user_id]['plots'].append({
                'id': str(uuid.uuid4()),
                'plant': None,
                'planted_date': None,
                'last_growth_date': None,
                'growth_days': 0,
                'health': 0,
                'watered': False
            })
            
    return gardens[user_id]

def get_user_inventory(user_id):
    """Get or initialize user inventory"""
    if user_id not in inventory:
        inventory[user_id] = {
            'seeds': {},
            'tools': {},
            'helpers': {},
            'decorations': {}
        }
    return inventory[user_id]

def get_user_economy(user_id):
    """Get or initialize user economy"""
    if user_id not in economy:
        economy[user_id] = {
            'gems': 100,  # Start with 100 gems
            'transactions': [],
            'last_daily_bonus': None
        }
    return economy[user_id]

def get_user_helpers(user_id):
    """Get or initialize user helpers/robots"""
    if user_id not in helpers:
        helpers[user_id] = {
            'active': {},
            'available': {}
        }
    return helpers[user_id]

def add_gems(user_id, amount, reason):
    """Add gems to user's account and record transaction"""
    user_economy = get_user_economy(user_id)
    user_economy['gems'] += amount
    
    transaction = {
        'id': str(uuid.uuid4()),
        'date': datetime.utcnow().isoformat(),
        'amount': amount,
        'type': 'credit',
        'reason': reason,
        'balance': user_economy['gems']
    }
    
    user_economy['transactions'].append(transaction)
    return True

def remove_gems(user_id, amount, reason):
    """Remove gems from user's account and record transaction"""
    user_economy = get_user_economy(user_id)
    
    if user_economy['gems'] < amount:
        return False
    
    user_economy['gems'] -= amount
    
    transaction = {
        'id': str(uuid.uuid4()),
        'date': datetime.utcnow().isoformat(),
        'amount': amount,
        'type': 'debit',
        'reason': reason,
        'balance': user_economy['gems']
    }
    
    user_economy['transactions'].append(transaction)
    return True

def add_to_inventory(user_id, item_id, quantity=1):
    """Add an item to user's inventory"""
    user_inventory = get_user_inventory(user_id)
    
    if item_id not in shop_items:
        return False
    
    item = shop_items[item_id]
    category = item['category']
    
    if item_id not in user_inventory[category]:
        user_inventory[category][item_id] = {
            'id': item_id,
            'quantity': 0,
            'acquired_date': datetime.utcnow().isoformat()
        }
    
    user_inventory[category][item_id]['quantity'] += quantity
    return True

def remove_from_inventory(user_id, item_id, quantity=1):
    """Remove an item from user's inventory"""
    user_inventory = get_user_inventory(user_id)
    
    if item_id not in shop_items:
        return False
    
    item = shop_items[item_id]
    category = item['category']
    
    if item_id not in user_inventory[category] or user_inventory[category][item_id]['quantity'] < quantity:
        return False
    
    user_inventory[category][item_id]['quantity'] -= quantity
    
    # Remove the entry if quantity becomes zero
    if user_inventory[category][item_id]['quantity'] <= 0:
        del user_inventory[category][item_id]
    
    return True

def update_garden(user_id, current_date=None):
    """Update garden state based on time passed"""
    if current_date is None:
        current_date = datetime.utcnow().date()
    else:
        current_date = datetime.strptime(current_date, '%Y-%m-%d').date()
    
    garden = get_user_garden(user_id)
    user_helper = get_user_helpers(user_id)
    
    # Check if garden was watered today or if robot is active
    last_watered = datetime.strptime(garden['last_watered'], '%Y-%m-%d').date()
    days_since_watered = (current_date - last_watered).days
    
    # Check if robot is active
    robot_active = False
    for helper_id, helper in user_helper['active'].items():
        if helper['effect']['type'] == 'auto_water':
            if helper['days_remaining'] > 0:
                # Robot is active and can water
                robot_active = True
                helper['days_remaining'] -= 1
                # Remove robot if duration expired
                if helper['days_remaining'] <= 0:
                    del user_helper['active'][helper_id]
                break
    
    # Process each plot
    for plot in garden['plots']:
        if plot['plant'] is None:
            continue
        
        plant_type = plot['plant']
        plant_data = PLANT_TYPES[plant_type]
        
        # Update plant health based on watering
        if days_since_watered <= 0 or robot_active:
            # Watered today or by robot
            plot['health'] = min(plant_data['max_health'], plot['health'] + 1)
            plot['watered'] = True
        else:
            # Not watered
            plot['health'] = max(0, plot['health'] - 1)
            plot['watered'] = False
            
            # Plant dies if health reaches 0
            if plot['health'] <= 0:
                plot['plant'] = None
                plot['planted_date'] = None
                plot['last_growth_date'] = None
                plot['growth_days'] = 0
                continue
        
        # Update growth only if the plant was watered
        if plot['watered']:
            # Check if there are active fertilizers
            growth_multiplier = 1
            for helper_id, helper in user_helper['active'].items():
                if helper['effect']['type'] == 'growth_boost':
                    growth_multiplier = max(growth_multiplier, helper['effect']['multiplier'])
            
            # Calculate days since last growth date
            if plot['last_growth_date'] is None:
                plot['last_growth_date'] = current_date.strftime('%Y-%m-%d')
            else:
                last_growth = datetime.strptime(plot['last_growth_date'], '%Y-%m-%d').date()
                days_to_add = (current_date - last_growth).days * growth_multiplier
                plot['growth_days'] = min(plant_data['growth_time'], plot['growth_days'] + days_to_add)
                plot['last_growth_date'] = current_date.strftime('%Y-%m-%d')
                
    # Update last watered date if watered today or by robot
    if days_since_watered <= 0 or robot_active:
        garden['last_watered'] = current_date.strftime('%Y-%m-%d')
    
    return garden

def harvest_plant(user_id, plot_id):
    """Harvest a plant and get rewards"""
    garden = get_user_garden(user_id)
    
    # Find the plot
    plot = None
    for p in garden['plots']:
        if p['id'] == plot_id:
            plot = p
            break
    
    if plot is None or plot['plant'] is None:
        return None
    
    plant_type = plot['plant']
    plant_data = PLANT_TYPES[plant_type]
    
    # Check if the plant is fully grown
    if plot['growth_days'] < plant_data['growth_time']:
        return None
    
    # Calculate rewards based on plant type
    xp_reward = plant_data['xp_reward']
    gem_reward = plant_data['gem_reward']
    
    # Add rewards to user
    progress = get_user_progress(user_id)
    progress['xp'] += xp_reward
    add_gems(user_id, gem_reward, f"Harvested {plant_data['name']}")
    
    # Clear the plot
    plot['plant'] = None
    plot['planted_date'] = None
    plot['last_growth_date'] = None
    plot['growth_days'] = 0
    plot['health'] = 0
    plot['watered'] = False
    
    # Possibly give a seed back (50% chance)
    seed_id = f"{plant_type}_seed"
    if random.random() < 0.5:
        add_to_inventory(user_id, seed_id)
    
    return {
        'xp_reward': xp_reward,
        'gem_reward': gem_reward,
        'plant_name': plant_data['name'],
        'seed_returned': (random.random() < 0.5)
    }

def get_current_plant_level(plant_type, growth_days):
    """Get the current level of a plant based on growth days"""
    plant_data = PLANT_TYPES[plant_type]
    
    current_level = None
    for i, level in enumerate(reversed(plant_data['levels'])):
        if growth_days >= level['days']:
            current_level = level
            break
    
    if current_level is None:
        current_level = plant_data['levels'][0]
    
    return current_level

# Text to speech helper function
def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        return audio_io
    except Exception as e:
        logger.error(f"Error converting text to speech: {e}")
        return None

# YouTube and subtitle related functions from botv6.py
def fetch_and_parse_subtitle(subtitle_url):
    """
    Fetches and parses the subtitle content from the given URL.
    
    :param subtitle_url: The URL of the subtitle file.
    :return: Subtitle content as a string or None if failed.
    """
    try:
        response = requests.get(subtitle_url)
        if response.status_code != 200:
            return None

        subtitle_data = response.json()  # Parse the JSON response
        return parse_json_subtitle(subtitle_data)

    except Exception as e:
        logger.error(f"Error fetching subtitles: {e}")
        return None

def parse_json_subtitle(json_data):
    """
    Parses JSON subtitle data into plain text.
    
    :param json_data: The raw JSON subtitle data.
    :return: Subtitle text as a string.
    """
    try:
        events = json_data.get("events", [])
        subtitle_text = []

        for event in events:
            segs = event.get("segs", [])
            if not segs:
                continue

            # Combine all segments in the event
            event_text = "".join(segment.get("utf8", "") for segment in segs if "utf8" in segment)
            if event_text.strip():  # Ignore empty lines
                subtitle_text.append(event_text)

        return "\n".join(subtitle_text)  # Join all subtitle lines with newlines
    except Exception as e:
        logger.error(f"Error parsing subtitle JSON: {e}")
        return None

def sanitize_filename(filename):
    """
    Sanitizes a filename to remove invalid characters.
    
    :param filename: Original filename.
    :return: Sanitized filename.
    """
    if not filename:
        return "unknown_video"
        
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename

def check_for_subtitles(youtube_url, preferred_lang=None):
    """
    Checks if subtitles are available for the given YouTube URL.
    
    :param youtube_url: The URL of the YouTube video.
    :param preferred_lang: Preferred subtitle language code ('en' or 'uk')
    :return: Tuple of (subtitle_content, language, subtitle_type, video_title) or (None, None, None, title) if no subtitles.
    """
    try:
        # Define options for yt_dlp
        ydl_opts = {
            "skip_download": True,  # Skip downloading the video itself
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_title = info.get("title", "Unknown Video")
            
            available_languages = info.get("subtitles", {})
            auto_captions = info.get("automatic_captions", {})
            
            # Set requested languages based on preference
            if preferred_lang:
                requested_languages = [preferred_lang]
            else:
                requested_languages = ["en", "uk"]
            
            # Try manual subtitles first for the preferred language
            for lang in requested_languages:
                if lang in available_languages:
                    subtitle_info = available_languages[lang][0]
                    subtitle_content = fetch_and_parse_subtitle(subtitle_info["url"])
                    if subtitle_content:
                        return subtitle_content, lang, "Manual", video_title
            
            # Try auto-generated captions if no manual subtitles
            for lang in requested_languages:
                if lang in auto_captions:
                    subtitle_info = auto_captions[lang][0]
                    subtitle_content = fetch_and_parse_subtitle(subtitle_info["url"])
                    if subtitle_content:
                        return subtitle_content, lang, "Auto-Generated", video_title
            
            # No subtitles found for preferred language
            return None, None, None, video_title

    except Exception as e:
        logger.error(f"Error checking for subtitles: {e}")
        return None, None, None, None

# Routes

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'version': '1.0.0'
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    username = data['username']
    password = data['password']
    email = data.get('email', '')
    
    if username in users:
        return jsonify({'error': 'Username already exists'}), 409
    
    user_id = str(uuid.uuid4())
    users[username] = {
        'id': user_id,
        'username': username,
        'password_hash': generate_password_hash(password),
        'email': email,
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Initialize user progress
    get_user_progress(user_id)
    
    # Initialize user garden
    get_user_garden(user_id)
    
    # Initialize user inventory and add starter items
    user_inventory = get_user_inventory(user_id)
    add_to_inventory(user_id, "sunflower_seed", 3)  # Start with 3 sunflower seeds
    add_to_inventory(user_id, "fertilizer", 1)      # And 1 fertilizer
    
    # Initialize user economy
    get_user_economy(user_id)
    
    # Initialize user helpers
    get_user_helpers(user_id)
    
    # Set default AI model for the new user
    user_models[user_id] = DEFAULT_AI_MODEL
    
    token = generate_token(user_id)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user_id,
            'username': username,
            'email': email
        }
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
    
    username = data['username']
    password = data['password']
    
    if username not in users:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    user = users[username]
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    token = generate_token(user['id'])
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    })

# BOT FEATURE ROUTES

@app.route('/api/generate', methods=['POST'])
def ai_generate():
    """API endpoint for generating AI responses (equivalent to /gen command)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    # Allow anonymous usage but with limited functionality
    if not user_id and not OPENROUTER_API_KEY:
        return jsonify({'error': 'Authentication required for AI generation'}), 401
    
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Prompt is required'}), 400
    
    prompt = data['prompt']
    context = data.get('context', '')
    
    # Get model name for display
    model_id = DEFAULT_AI_MODEL
    if user_id and user_id in user_models:
        model_id = user_models[user_id]
    model_name = model_id.split('/')[-1].split(':')[0]
    
    if context:
        full_prompt = f"{prompt}\n\nContext: \"{context}\""
    else:
        full_prompt = prompt
    
    try:
        # Generate response using OpenRouter
        response = generate_ai_response(full_prompt, user_id)
        
        # Add small XP reward for using AI generation (if authenticated)
        if user_id:
            progress = get_user_progress(user_id)
            progress['xp'] += 2
            
            # Small chance to find gems (5%)
            if random.random() < 0.05:
                gem_reward = random.randint(1, 5)
                add_gems(user_id, gem_reward, "Found while using AI")
                response += f"\n\n[You found {gem_reward} gems! 💎]"
        
        return jsonify({
            'response': response,
            'model': model_name
        })
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/models', methods=['GET'])
def get_ai_models():
    """API endpoint to get available AI models (equivalent to /gen-select command display)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    current_model = DEFAULT_AI_MODEL
    if user_id and user_id in user_models:
        current_model = user_models[user_id]
    
    # Format models for response
    formatted_models = []
    for model_id, description in AI_MODELS.items():
        model_name = model_id.split('/')[-1].split(':')[0]
        formatted_models.append({
            'id': model_id,
            'name': model_name,
            'description': description,
            'is_current': model_id == current_model
        })
    
    return jsonify({
        'models': formatted_models,
        'current_model': current_model
    })

@app.route('/api/ai/models', methods=['POST'])
def set_ai_model():
    """API endpoint to set AI model (equivalent to /gen-select command action)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    if not data or 'model_id' not in data:
        return jsonify({'error': 'Model ID is required'}), 400
    
    model_id = data['model_id']
    
    # Check if model exists
    if model_id != 'default' and model_id not in AI_MODELS:
        return jsonify({'error': 'Invalid model ID'}), 400
    
    # Set or reset model
    if model_id == 'default':
        if user_id in user_models:
            del user_models[user_id]
        model_name = DEFAULT_AI_MODEL.split('/')[-1].split(':')[0]
        success_message = f"Reset to default model: {model_name}"
    else:
        user_models[user_id] = model_id
        model_name = model_id.split('/')[-1].split(':')[0]
        success_message = f"Model changed to: {model_name}"
    
    return jsonify({
        'success': True,
        'message': success_message,
        'current_model': model_id if model_id != 'default' else DEFAULT_AI_MODEL
    })

@app.route('/api/transcribe/url', methods=['POST'])
def transcribe_url():
    """API endpoint for transcribing audio/video from URLs (equivalent to /sub command)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    # Allow anonymous usage
    data = request.json
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    lang = data.get('language', 'en')  # Default to English if not specified
    
    try:
        # First check if subtitles are available
        subtitle_content, subtitle_lang, subtitle_type, video_title = check_for_subtitles(url, preferred_lang=lang)
        
        if subtitle_content:
            # Subtitles were found
            lang_name = "English" if subtitle_lang == "en" else "Ukrainian" if subtitle_lang == "uk" else subtitle_lang
            
            # Add XP reward if user is authenticated
            if user_id:
                progress = get_user_progress(user_id)
                progress['xp'] += 5
                
                # Small chance to find gems (10%)
                if random.random() < 0.1:
                    gem_reward = random.randint(3, 8)
                    add_gems(user_id, gem_reward, f"Found while transcribing {video_title}")
            
            return jsonify({
                'success': True,
                'transcript': subtitle_content,
                'source': 'subtitles',
                'language': lang_name,
                'subtitle_type': subtitle_type,
                'title': video_title,
                'url': url
            })
        
        # If no subtitles found, fall back to audio transcription
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript_file = os.path.join(temp_dir, "transcript.txt")
            
            # Process the URL using AudioTranscriber
            transcript = audio_transcriber.process_url(
                url,
                output_dir=temp_dir,
                transcript_file=transcript_file,
                keep_audio=False
            )
            
            if transcript:
                # Add XP reward if user is authenticated
                if user_id:
                    progress = get_user_progress(user_id)
                    progress['xp'] += 10  # More XP for audio transcription
                    
                    # Small chance to find gems (15%)
                    if random.random() < 0.15:
                        gem_reward = random.randint(5, 10)
                        add_gems(user_id, gem_reward, f"Found while transcribing audio from {url}")
                
                return jsonify({
                    'success': True,
                    'transcript': transcript,
                    'source': 'audio',
                    'language': 'auto-detected',
                    'title': video_title if video_title else "Unknown Title",
                    'url': url
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to transcribe URL'
                }), 500
    except Exception as e:
        logger.error(f"Error transcribing URL: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/web/search', methods=['POST'])
def web_search():
    """API endpoint for web search (equivalent to /web command)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    # Allow anonymous usage for web search
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Search query is required'}), 400
    
    query = data['query']
    
    try:
        # Use the WebSearchAI class to perform the search
        search_result = web_search_ai.answer_query(query)
        
        # Add XP reward if user is authenticated
        if user_id:
            progress = get_user_progress(user_id)
            progress['xp'] += 3
            
            # Small chance to find gems (8%)
            if random.random() < 0.08:
                gem_reward = random.randint(2, 7)
                add_gems(user_id, gem_reward, f"Found while searching for {query}")
        
        return jsonify({
            'success': True,
            'result': search_result,
            'query': query
        })
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech_api():
    """API endpoint for text-to-speech conversion (equivalent to /tts command)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    # Allow anonymous usage for TTS
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'Text is required'}), 400
    
    text = data['text']
    
    try:
        # Convert text to speech
        audio_io = text_to_speech(text)
        if audio_io:
            # Add XP reward if user is authenticated
            if user_id:
                progress = get_user_progress(user_id)
                progress['xp'] += 1
            
            return send_file(
                audio_io,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name="speech.mp3"
            )
        else:
            return jsonify({'error': 'Failed to convert text to speech'}), 500
    except Exception as e:
        logger.error(f"Error in TTS process: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf', methods=['POST'])
def generate_pdf():
    """API endpoint for PDF generation (equivalent to /pdf command)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    # Allow anonymous usage for PDF generation
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'Text content is required'}), 400
    
    text = data['text']
    title = data.get('title', '')
    
    # Add title as markdown heading if provided
    if title:
        text_to_convert = f"# {title}\n\n{text}"
    else:
        text_to_convert = text
    
    try:
        # Generate a filename
        filename = f"document_{int(time.time())}.pdf"
        if title:
            safe_title = ''.join(c for c in title if c.isalnum() or c in ' _-')
            if len(safe_title) <= 30:
                filename = f"{safe_title}.pdf"
        
        # Convert text to PDF
        pdf_path = text_to_pdf(text_to_convert, filename)
        
        if pdf_path and os.path.exists(pdf_path):
            # Add XP reward if user is authenticated
            if user_id:
                progress = get_user_progress(user_id)
                progress['xp'] += 2
                
                # Small chance to find gems (5%)
                if random.random() < 0.05:
                    gem_reward = random.randint(1, 5)
                    add_gems(user_id, gem_reward, "Found while generating PDF")
            
            # Send the PDF document
            response = send_file(
                pdf_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=filename
            )
            
            # Clean up the PDF file after sending (using a callback)
            @response.call_on_close
            def cleanup():
                try:
                    os.unlink(pdf_path)
                    # Try to remove the parent directory if it's a temp dir
                    parent_dir = os.path.dirname(pdf_path)
                    if os.path.exists(parent_dir) and tempfile.gettempdir() in parent_dir:
                        os.rmdir(parent_dir)
                except Exception as e:
                    logger.error(f"Error cleaning up PDF file: {e}")
            
            return response
        else:
            return jsonify({'error': 'Failed to generate PDF'}), 500
    except Exception as e:
        logger.error(f"Error in PDF generation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe/voice', methods=['POST'])
def transcribe_voice():
    """API endpoint for transcribing voice messages (equivalent to voice message handler)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    # Allow anonymous usage for voice transcription
    # Check if file was uploaded
    if 'voice' not in request.files:
        return jsonify({'error': 'Voice file is required'}), 400
    
    voice_file = request.files['voice']
    
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            voice_file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe the voice message
            transcription = voice_transcriber.transcribe_file(temp_file_path)
            
            if transcription:
                # Generate AI response to the transcription if requested
                generate_response = request.form.get('generate_response', 'false').lower() == 'true'
                
                response_data = {
                    'success': True,
                    'transcription': transcription
                }
                
                # Add XP reward if user is authenticated
                if user_id:
                    progress = get_user_progress(user_id)
                    progress['xp'] += 3
                    
                    # Small chance to find gems (7%)
                    if random.random() < 0.07:
                        gem_reward = random.randint(2, 6)
                        add_gems(user_id, gem_reward, "Found while transcribing voice")
                        response_data['gem_reward'] = gem_reward
                
                if generate_response:
                    ai_response = generate_ai_response(transcription, user_id)
                    response_data['ai_response'] = ai_response
                
                return jsonify(response_data)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to transcribe voice message'
                }), 500
        except Exception as e:
            logger.error(f"Error transcribing voice message: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        return jsonify({'error': str(e)}), 500

# GARDEN API ENDPOINTS

@app.route('/api/garden', methods=['GET'])
def get_garden():
    """Get user's garden status"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Update garden status
    garden = update_garden(user_id)
    
    # Format garden data for response
    formatted_plots = []
    for plot in garden['plots']:
        plot_data = {
            'id': plot['id'],
            'empty': plot['plant'] is None,
        }
        
        if plot['plant'] is not None:
            plant_type = plot['plant']
            plant_data = PLANT_TYPES[plant_type]
            current_level = get_current_plant_level(plant_type, plot['growth_days'])
            
            plot_data.update({
                'plant_type': plant_type,
                'plant_name': plant_data['name'],
                'icon': current_level['icon'],
                'level_name': current_level['name'],
                'health': plot['health'],
                'max_health': plant_data['max_health'],
                'growth_days': plot['growth_days'],
                'growth_time': plant_data['growth_time'],
                'progress': min(100, int(plot['growth_days'] / plant_data['growth_time'] * 100)),
                'watered': plot['watered'],
                'harvestable': plot['growth_days'] >= plant_data['growth_time'],
                'planted_date': plot['planted_date']
            })
        
        formatted_plots.append(plot_data)
    
    # Get active helpers
    user_helpers = get_user_helpers(user_id)
    active_helpers = []
    
    for helper_id, helper in user_helpers['active'].items():
        active_helpers.append({
            'id': helper_id,
            'name': helper['name'],
            'icon': helper['icon'],
            'effect_type': helper['effect']['type'],
            'days_remaining': helper['days_remaining']
        })
    
    return jsonify({
        'garden_level': garden['level'],
        'last_watered': garden['last_watered'],
        'plots': formatted_plots,
        'decorations': garden['decorations'],
        'active_helpers': active_helpers
    })

@app.route('/api/garden/water', methods=['POST'])
def water_garden():
    """Water all plants in the garden"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    garden = get_user_garden(user_id)
    
    # Check if already watered today
    last_watered = datetime.strptime(garden['last_watered'], '%Y-%m-%d').date()
    today = datetime.utcnow().date()
    
    if last_watered == today:
        return jsonify({
            'success': False,
            'message': 'Your garden has already been watered today!'
        }), 400
    
    # Update watering status
    garden['last_watered'] = today.strftime('%Y-%m-%d')
    
    # Update plant health
    plants_watered = 0
    for plot in garden['plots']:
        if plot['plant'] is not None:
            plant_type = plot['plant']
            plant_data = PLANT_TYPES[plant_type]
            
            # Apply watering can effect if owned
            water_multiplier = 1
            user_inventory = get_user_inventory(user_id)
            if 'watering_can' in user_inventory['tools']:
                water_multiplier = shop_items['watering_can']['effect']['multiplier']
            
            # Update health and watered status
            health_gain = 1 * water_multiplier
            plot['health'] = min(plant_data['max_health'], plot['health'] + health_gain)
            plot['watered'] = True
            plants_watered += 1
            
            # Update growth if not already updated today
            if plot['last_growth_date'] != today.strftime('%Y-%m-%d'):
                plot['growth_days'] = min(plant_data['growth_time'], plot['growth_days'] + 1)
                plot['last_growth_date'] = today.strftime('%Y-%m-%d')
    
    # Add XP for watering plants
    if plants_watered > 0:
        progress = get_user_progress(user_id)
        progress['xp'] += 5  # Base XP for watering
        
        # Add gems sometimes (20% chance)
        if random.random() < 0.2:
            gem_reward = random.randint(1, 3)
            add_gems(user_id, gem_reward, "Found while watering plants")
            
            return jsonify({
                'success': True,
                'message': f'You watered {plants_watered} plants and found {gem_reward} gems! 💎',
                'plants_watered': plants_watered,
                'gem_reward': gem_reward,
                'xp_earned': 5
            })
    
    return jsonify({
        'success': True,
        'message': f'You watered {plants_watered} plants!',
        'plants_watered': plants_watered,
        'xp_earned': 5
    })

@app.route('/api/garden/plant', methods=['POST'])
def plant_seed():
    """Plant a seed in an empty plot"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    if not data or 'plot_id' not in data or 'seed_id' not in data:
        return jsonify({'error': 'Plot ID and seed ID are required'}), 400
    
    plot_id = data['plot_id']
    seed_id = data['seed_id']
    
    # Check if seed exists and is a plant type
    if seed_id not in shop_items or shop_items[seed_id]['category'] != 'seeds':
        return jsonify({'error': 'Invalid seed ID'}), 400
    
    # Get plant type from seed
    plant_type = shop_items[seed_id]['plant_type']
    
    # Check if user has the seed
    user_inventory = get_user_inventory(user_id)
    if seed_id not in user_inventory['seeds'] or user_inventory['seeds'][seed_id]['quantity'] <= 0:
        return jsonify({'error': 'You do not have this seed'}), 400
    
    # Find the plot
    garden = get_user_garden(user_id)
    plot = None
    for p in garden['plots']:
        if p['id'] == plot_id:
            plot = p
            break
    
    if plot is None:
        return jsonify({'error': 'Invalid plot ID'}), 400
    
    # Check if plot is empty
    if plot['plant'] is not None:
        return jsonify({'error': 'This plot already has a plant'}), 400
    
    # Plant the seed
    plot['plant'] = plant_type
    plot['planted_date'] = datetime.utcnow().strftime('%Y-%m-%d')
    plot['last_growth_date'] = datetime.utcnow().strftime('%Y-%m-%d')
    plot['growth_days'] = 0
    plot['health'] = PLANT_TYPES[plant_type]['max_health']  # Start with full health
    plot['watered'] = True  # Initially watered
    
    # Remove the seed from inventory
    remove_from_inventory(user_id, seed_id, 1)
    
    # Add some XP for planting
    progress = get_user_progress(user_id)
    progress['xp'] += 3
    
    plant_data = PLANT_TYPES[plant_type]
    
    return jsonify({
        'success': True,
        'message': f'You planted a {plant_data["name"]}!',
        'plant_type': plant_type,
        'plant_name': plant_data['name'],
        'icon': plant_data['levels'][0]['icon'],
        'xp_earned': 3
    })

@app.route('/api/garden/harvest', methods=['POST'])
def harvest_plant_endpoint():
    """Harvest a mature plant"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    if not data or 'plot_id' not in data:
        return jsonify({'error': 'Plot ID is required'}), 400
    
    plot_id = data['plot_id']
    
    # Harvest the plant
    result = harvest_plant(user_id, plot_id)
    
    if result is None:
        return jsonify({
            'success': False,
            'message': 'Cannot harvest this plant. It may not be ready or the plot is empty.'
        }), 400
    
    return jsonify({
        'success': True,
        'message': f'You harvested a {result["plant_name"]} and earned {result["xp_reward"]} XP and {result["gem_reward"]} gems!',
        'xp_reward': result['xp_reward'],
        'gem_reward': result['gem_reward'],
        'seed_returned': result['seed_returned']
    })

@app.route('/api/garden/seeds', methods=['GET'])
def get_available_seeds():
    """Get user's available seeds"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_inventory = get_user_inventory(user_id)
    
    available_seeds = []
    for seed_id, seed_info in user_inventory['seeds'].items():
        if seed_info['quantity'] > 0 and seed_id in shop_items:
            item = shop_items[seed_id]
            available_seeds.append({
                'id': seed_id,
                'name': item['name'],
                'description': item['description'],
                'icon': item['icon'],
                'quantity': seed_info['quantity'],
                'plant_type': item['plant_type']
            })
    
    return jsonify({
        'seeds': available_seeds
    })

# INVENTORY API ENDPOINTS

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get user's inventory"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_inventory = get_user_inventory(user_id)
    
    formatted_inventory = {}
    
    # Format each category
    for category, items in user_inventory.items():
        formatted_inventory[category] = []
        for item_id, item_info in items.items():
            if item_id in shop_items:
                shop_item = shop_items[item_id]
                formatted_inventory[category].append({
                    'id': item_id,
                    'name': shop_item['name'],
                    'description': shop_item['description'],
                    'icon': shop_item['icon'],
                    'quantity': item_info['quantity'],
                    'type': shop_item['type'],
                    'acquired_date': item_info['acquired_date']
                })
    
    return jsonify({
        'inventory': formatted_inventory
    })

@app.route('/api/inventory/use', methods=['POST'])
def use_inventory_item():
    """Use an item from the inventory"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    if not data or 'item_id' not in data:
        return jsonify({'error': 'Item ID is required'}), 400
    
    item_id = data['item_id']
    
    # Check if the item exists
    if item_id not in shop_items:
        return jsonify({'error': 'Invalid item ID'}), 400
    
    shop_item = shop_items[item_id]
    category = shop_item['category']
    
    # Check if user has the item
    user_inventory = get_user_inventory(user_id)
    if item_id not in user_inventory[category] or user_inventory[category][item_id]['quantity'] <= 0:
        return jsonify({'error': 'You do not have this item'}), 400
    
    # Process based on item type
    if shop_item['type'] == 'helper':
        # Activate helper
        user_helper = get_user_helpers(user_id)
        
        # Check if this type of helper is already active
        for active_id, active_helper in user_helper['active'].items():
            if active_helper['effect']['type'] == shop_item['effect']['type']:
                return jsonify({
                    'success': False,
                    'message': f'A {shop_item["effect"]["type"]} helper is already active'
                }), 400
        
        # Create new active helper
        helper_id = str(uuid.uuid4())
        user_helper['active'][helper_id] = {
            'id': helper_id,
            'name': shop_item['name'],
            'icon': shop_item['icon'],
            'effect': shop_item['effect'],
            'days_remaining': shop_item['effect']['duration'],
            'activated_date': datetime.utcnow().isoformat()
        }
        
        # Remove from inventory
        remove_from_inventory(user_id, item_id, 1)
        
        return jsonify({
            'success': True,
            'message': f'Activated {shop_item["name"]} for {shop_item["effect"]["duration"]} days!',
            'helper_id': helper_id,
            'days_remaining': shop_item['effect']['duration']
        })
    
    elif shop_item['type'] == 'consumable':
        # Apply consumable effect
        user_helper = get_user_helpers(user_id)
        
        # Check effect type
        if shop_item['effect']['type'] == 'growth_boost':
            # Add as active effect
            effect_id = str(uuid.uuid4())
            user_helper['active'][effect_id] = {
                'id': effect_id,
                'name': shop_item['name'],
                'icon': shop_item['icon'],
                'effect': shop_item['effect'],
                'days_remaining': shop_item['effect']['duration'],
                'activated_date': datetime.utcnow().isoformat()
            }
            
            # Remove from inventory
            remove_from_inventory(user_id, item_id, 1)
            
            return jsonify({
                'success': True,
                'message': f'Applied {shop_item["name"]}! Plants will grow {shop_item["effect"]["multiplier"]}x faster for {shop_item["effect"]["duration"]} days.',
                'effect_id': effect_id,
                'days_remaining': shop_item['effect']['duration']
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Unknown effect type: {shop_item["effect"]["type"]}'
            }), 400
    
    elif shop_item['type'] == 'decoration':
        # Add decoration to garden
        garden = get_user_garden(user_id)
        
        # Check if decoration is already placed
        for decoration in garden['decorations']:
            if decoration['item_id'] == item_id:
                return jsonify({
                    'success': False,
                    'message': 'This decoration is already placed in your garden'
                }), 400
        
        # Add decoration
        decoration_id = str(uuid.uuid4())
        garden['decorations'].append({
            'id': decoration_id,
            'item_id': item_id,
            'name': shop_item['name'],
            'icon': shop_item['icon'],
            'placed_date': datetime.utcnow().isoformat()
        })
        
        # Remove from inventory
        remove_from_inventory(user_id, item_id, 1)
        
        return jsonify({
            'success': True,
            'message': f'Placed {shop_item["name"]} in your garden!',
            'decoration_id': decoration_id
        })
    
    else:
        return jsonify({
            'success': False,
            'message': f'Cannot use this type of item: {shop_item["type"]}'
        }), 400

# SHOP API ENDPOINTS

@app.route('/api/shop', methods=['GET'])
def get_shop_items():
    """Get all available shop items"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    formatted_items = []
    for item_id, item in shop_items.items():
        formatted_items.append({
            'id': item_id,
            'name': item['name'],
            'description': item['description'],
            'icon': item['icon'],
            'category': item['category'],
            'price': item['price'],
            'type': item['type']
        })
    
    # Get user's economy data if authenticated
    gems = 0
    if user_id:
        user_economy = get_user_economy(user_id)
        gems = user_economy['gems']
    
    return jsonify({
        'shop_items': formatted_items,
        'user_gems': gems
    })

@app.route('/api/shop/categories', methods=['GET'])
def get_shop_categories():
    """Get all shop categories"""
    # Collect unique categories
    categories = set()
    for item in shop_items.values():
        categories.add(item['category'])
    
    return jsonify({
        'categories': list(categories)
    })

@app.route('/api/shop/<category>', methods=['GET'])
def get_shop_category(category):
    """Get items in a specific shop category"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    # Filter items by category
    category_items = []
    for item_id, item in shop_items.items():
        if item['category'] == category:
            category_items.append({
                'id': item_id,
                'name': item['name'],
                'description': item['description'],
                'icon': item['icon'],
                'category': item['category'],
                'price': item['price'],
                'type': item['type']
            })
    
    # Get user's economy data if authenticated
    gems = 0
    if user_id:
        user_economy = get_user_economy(user_id)
        gems = user_economy['gems']
    
    return jsonify({
        'category': category,
        'items': category_items,
        'user_gems': gems
    })

@app.route('/api/shop/purchase', methods=['POST'])
def purchase_item():
    """Purchase an item from the shop"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    if not data or 'item_id' not in data:
        return jsonify({'error': 'Item ID is required'}), 400
    
    item_id = data['item_id']
    quantity = data.get('quantity', 1)
    
    # Check if item exists
    if item_id not in shop_items:
        return jsonify({'error': 'Invalid item ID'}), 400
    
    item = shop_items[item_id]
    total_price = item['price'] * quantity
    
    # Check if user has enough gems
    user_economy = get_user_economy(user_id)
    if user_economy['gems'] < total_price:
        return jsonify({
            'success': False,
            'message': 'Not enough gems for this purchase',
            'required': total_price,
            'available': user_economy['gems']
        }), 400
    
    # Process purchase
    if remove_gems(user_id, total_price, f"Purchased {quantity}x {item['name']}"):
        # Add item to inventory
        add_to_inventory(user_id, item_id, quantity)
        
        return jsonify({
            'success': True,
            'message': f'Successfully purchased {quantity}x {item["name"]} for {total_price} gems',
            'item_id': item_id,
            'quantity': quantity,
            'gems_spent': total_price,
            'gems_remaining': user_economy['gems']
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to process purchase'
        }), 500

# ECONOMY API ENDPOINTS

@app.route('/api/economy/balance', methods=['GET'])
def get_balance():
    """Get user's gem balance"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_economy = get_user_economy(user_id)
    
    return jsonify({
        'gems': user_economy['gems'],
        'last_daily_bonus': user_economy['last_daily_bonus']
    })

@app.route('/api/economy/transactions', methods=['GET'])
def get_transactions():
    """Get user's transaction history"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_economy = get_user_economy(user_id)
    
    # Sort transactions by date (newest first)
    transactions = sorted(
        user_economy['transactions'], 
        key=lambda x: x['date'], 
        reverse=True
    )
    
    return jsonify({
        'transactions': transactions
    })

@app.route('/api/economy/daily-bonus', methods=['POST'])
def claim_daily_bonus():
    """Claim daily login bonus"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_economy = get_user_economy(user_id)
    
    # Check if already claimed today
    today = datetime.utcnow().date()
    
    if user_economy['last_daily_bonus'] is not None:
        last_claim = datetime.strptime(user_economy['last_daily_bonus'], '%Y-%m-%d').date()
        if last_claim == today:
            return jsonify({
                'success': False,
                'message': 'You have already claimed your daily bonus today'
            }), 400
    
    # Calculate bonus amount (base + some random value)
    base_bonus = 15
    random_bonus = random.randint(5, 20)
    total_bonus = base_bonus + random_bonus
    
    # Add gems
    add_gems(user_id, total_bonus, "Daily login bonus")
    
    # Update last claim date
    user_economy['last_daily_bonus'] = today.strftime('%Y-%m-%d')
    
    # Also water the garden
    garden = get_user_garden(user_id)
    
    # Check if already watered today
    last_watered = datetime.strptime(garden['last_watered'], '%Y-%m-%d').date()
    
    if last_watered != today:
        garden['last_watered'] = today.strftime('%Y-%m-%d')
        
        # Update plant health
        for plot in garden['plots']:
            if plot['plant'] is not None:
                plant_type = plot['plant']
                plant_data = PLANT_TYPES[plant_type]
                
                # Update health and watered status
                plot['health'] = min(plant_data['max_health'], plot['health'] + 1)
                plot['watered'] = True
                
                # Update growth if not already updated today
                if plot['last_growth_date'] != today.strftime('%Y-%m-%d'):
                    plot['growth_days'] = min(plant_data['growth_time'], plot['growth_days'] + 1)
                    plot['last_growth_date'] = today.strftime('%Y-%m-%d')
    
    return jsonify({
        'success': True,
        'message': f'Claimed daily bonus of {total_bonus} gems!',
        'bonus_amount': total_bonus,
        'current_balance': user_economy['gems']
    })

# USER PROFILE ENDPOINT

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Find user info
    user_info = None
    for username, user in users.items():
        if user['id'] == user_id:
            user_info = user
            break
    
    if not user_info:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user progress
    progress = get_user_progress(user_id)
    
    # Get garden summary
    garden = get_user_garden(user_id)
    plants_count = 0
    mature_plants = 0
    for plot in garden['plots']:
        if plot['plant'] is not None:
            plants_count += 1
            plant_type = plot['plant']
            plant_data = PLANT_TYPES[plant_type]
            if plot['growth_days'] >= plant_data['growth_time']:
                mature_plants += 1
    
    # Get economic summary
    user_economy = get_user_economy(user_id)
    
    # Get inventory summary
    user_inventory = get_user_inventory(user_id)
    inventory_count = sum(
        sum(item['quantity'] for item in category.values())
        for category in user_inventory.values()
    )
    
    # Format user courses
    user_courses = []
    for course_id, course_progress in progress.get('courses', {}).items():
        if course_id in courses:
            course = courses[course_id]
            total_lessons = len(course.get('lessons', []))
            completed_lessons = len(course_progress.get('completed_lessons', []))
            percentage = round((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0)
            
            user_courses.append({
                'title': course['title'],
                'subject': course['subject_name'],
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'percentage': percentage,
                'level': course_progress.get('level', 1),
                'xp': course_progress.get('xp', 0)
            })
    
    return jsonify({
        'user': {
            'username': user_info['username'],
            'email': user_info['email'],
            'created_at': user_info['created_at']
        },
        'learning': {
            'xp': progress.get('xp', 0),
            'achievements': progress.get('achievements', []),
            'courses': user_courses
        },
        'garden': {
            'level': garden['level'],
            'plots_total': len(garden['plots']),
            'plots_used': plants_count,
            'plants_mature': mature_plants,
            'last_watered': garden['last_watered']
        },
        'economy': {
            'gems': user_economy['gems'],
            'transactions_count': len(user_economy['transactions']),
            'last_daily_bonus': user_economy['last_daily_bonus']
        },
        'inventory': {
            'items_count': inventory_count,
            'seeds_count': sum(item['quantity'] for item in user_inventory['seeds'].values()) if 'seeds' in user_inventory else 0,
            'helpers_count': sum(item['quantity'] for item in user_inventory['helpers'].values()) if 'helpers' in user_inventory else 0
        }
    })

# HELPER ENDPOINTS

@app.route('/api/helpers', methods=['GET'])
def get_helpers():
    """Get user's active and available helpers"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_helper = get_user_helpers(user_id)
    
    # Format active helpers
    active_helpers = []
    for helper_id, helper in user_helper['active'].items():
        active_helpers.append({
            'id': helper_id,
            'name': helper['name'],
            'icon': helper['icon'],
            'effect_type': helper['effect']['type'],
            'days_remaining': helper['days_remaining'],
            'activated_date': helper['activated_date']
        })
    
    # Get available helpers from inventory
    user_inventory = get_user_inventory(user_id)
    available_helpers = []
    
    if 'helpers' in user_inventory:
        for item_id, item_info in user_inventory['helpers'].items():
            if item_id in shop_items:
                shop_item = shop_items[item_id]
                available_helpers.append({
                    'id': item_id,
                    'name': shop_item['name'],
                    'description': shop_item['description'],
                    'icon': shop_item['icon'],
                    'effect_type': shop_item['effect']['type'],
                    'duration': shop_item['effect']['duration'],
                    'quantity': item_info['quantity']
                })
    
    return jsonify({
        'active_helpers': active_helpers,
        'available_helpers': available_helpers
    })

@app.route('/api/helpers/activate', methods=['POST'])
def activate_helper():
    """Activate a helper"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    if not data or 'item_id' not in data:
        return jsonify({'error': 'Item ID is required'}), 400
    
    item_id = data['item_id']
    
    # Check if the item exists and is a helper
    if item_id not in shop_items or shop_items[item_id]['category'] != 'helpers':
        return jsonify({'error': 'Invalid helper ID'}), 400
    
    # Use the inventory endpoint to activate the helper
    return use_inventory_item()

@app.route('/api/helpers/deactivate', methods=['POST'])
def deactivate_helper():
    """Deactivate a helper"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    if not data or 'helper_id' not in data:
        return jsonify({'error': 'Helper ID is required'}), 400
    
    helper_id = data['helper_id']
    
    # Check if helper is active
    user_helper = get_user_helpers(user_id)
    if helper_id not in user_helper['active']:
        return jsonify({'error': 'Helper is not active'}), 400
    
    # Get helper info before removing
    helper = user_helper['active'][helper_id]
    name = helper['name']
    
    # Remove helper
    del user_helper['active'][helper_id]
    
    return jsonify({
        'success': True,
        'message': f'Deactivated {name}',
        'helper_id': helper_id
    })

# Course related endpoints
@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all available courses"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    result_courses = []
    for course_id, course in courses.items():
        course_data = {
            'id': course_id,
            'title': course['title'],
            'subject_name': course['subject_name'],
            'difficulty': course['difficulty'],
            'description': course.get('description', '')
        }
        
        # Add progress if user is authenticated
        if user_id:
            progress = get_user_progress(user_id)
            if course_id in progress.get('courses', {}):
                course_progress = progress['courses'][course_id]
                course_data['progress'] = {
                    'level': course_progress.get('level', 1),
                    'xp': course_progress.get('xp', 0),
                    'completed_lessons': course_progress.get('completed_lessons', [])
                }
        
        result_courses.append(course_data)
    
    return jsonify({
        'courses': result_courses
    })

@app.route('/api/courses/<course_id>', methods=['GET'])
def get_course(course_id):
    """Get a specific course and its lessons"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if course_id not in courses:
        return jsonify({'error': 'Course not found'}), 404
    
    course = courses[course_id]
    
    # Deep copy to avoid modifying the original
    course_data = {
        'id': course_id,
        'title': course['title'],
        'subject_name': course['subject_name'],
        'difficulty': course['difficulty'],
        'description': course.get('description', ''),
        'lessons': course.get('lessons', [])
    }
    
    # Add progress if user is authenticated
    if user_id:
        progress = get_user_progress(user_id)
        if course_id in progress.get('courses', {}):
            course_data['progress'] = progress['courses'][course_id]
    
    return jsonify(course_data)

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """Get all learning subjects"""
    result_subjects = []
    for subject_id, subject in subjects.items():
        result_subjects.append({
            'id': subject_id,
            'name': subject['name'],
            'description': subject.get('description', ''),
            'icon': subject.get('icon', '📚')
        })
    
    return jsonify({
        'subjects': result_subjects
    })

@app.route('/api/subjects/<subject_id>', methods=['GET'])
def get_subject(subject_id):
    """Get a specific subject"""
    if subject_id not in subjects:
        return jsonify({'error': 'Subject not found'}), 404
    
    subject = subjects[subject_id]
    
    # Get courses for this subject
    subject_courses = []
    for course_id, course in courses.items():
        if course.get('subject_id') == subject_id:
            subject_courses.append({
                'id': course_id,
                'title': course['title'],
                'difficulty': course['difficulty'],
                'description': course.get('description', '')
            })
    
    return jsonify({
        'id': subject_id,
        'name': subject['name'],
        'description': subject.get('description', ''),
        'icon': subject.get('icon', '📚'),
        'courses': subject_courses
    })

@app.route('/api/subjects/<subject_id>/courses', methods=['GET'])
def get_subject_courses(subject_id):
    """Get courses for a specific subject"""
    if subject_id not in subjects:
        return jsonify({'error': 'Subject not found'}), 404
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    # Get courses for this subject
    subject_courses = []
    for course_id, course in courses.items():
        if course.get('subject_id') == subject_id:
            course_data = {
                'id': course_id,
                'title': course['title'],
                'difficulty': course['difficulty'],
                'description': course.get('description', '')
            }
            
            # Add progress if user is authenticated
            if user_id:
                progress = get_user_progress(user_id)
                if course_id in progress.get('courses', {}):
                    course_progress = progress['courses'][course_id]
                    course_data['progress'] = {
                        'level': course_progress.get('level', 1),
                        'xp': course_progress.get('xp', 0),
                        'completed_lessons': course_progress.get('completed_lessons', [])
                    }
            
            subject_courses.append(course_data)
    
    return jsonify({
        'courses': subject_courses
    })

@app.route('/api/lessons/<lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    """Get a specific lesson and its exercises"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if lesson_id not in lessons:
        return jsonify({'error': 'Lesson not found'}), 404
    
    lesson = lessons[lesson_id]
    
    # Deep copy to avoid modifying the original
    lesson_data = {
        'id': lesson_id,
        'title': lesson['title'],
        'description': lesson.get('description', ''),
        'course_id': lesson['course_id'],
        'xp_reward': lesson.get('xp_reward', 10),
        'exercises': lesson.get('exercises', [])
    }
    
    return jsonify(lesson_data)

@app.route('/api/lessons/<lesson_id>/complete', methods=['POST'])
def complete_lesson(lesson_id):
    """Mark a lesson as completed"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    if lesson_id not in lessons:
        return jsonify({'error': 'Lesson not found'}), 404
    
    lesson = lessons[lesson_id]
    course_id = lesson['course_id']
    
    # Get user progress
    progress = get_user_progress(user_id)
    
    # Initialize course progress if not exists
    if course_id not in progress['courses']:
        progress['courses'][course_id] = {
            'level': 1,
            'xp': 0,
            'completed_lessons': []
        }
    
    course_progress = progress['courses'][course_id]
    
    # Check if already completed
    if lesson_id in course_progress['completed_lessons']:
        return jsonify({
            'success': False,
            'message': 'Lesson already completed'
        }), 400
    
    # Add to completed lessons
    course_progress['completed_lessons'].append(lesson_id)
    
    # Calculate XP reward
    xp_reward = lesson.get('xp_reward', 10)
    course_progress['xp'] += xp_reward
    progress['xp'] += xp_reward
    
    # Calculate new level (1 level per 100 XP)
    new_level = max(1, course_progress['xp'] // 100 + 1)
    level_up = new_level > course_progress['level']
    course_progress['level'] = new_level
    
    # Add gems for completing lesson
    gem_reward = random.randint(5, 15)
    add_gems(user_id, gem_reward, f"Completed lesson: {lesson['title']}")
    
    # Check for new achievements (placeholder)
    new_achievements = []
    
    # Update garden - complete lessons water plants
    garden = get_user_garden(user_id)
    today = datetime.utcnow().date()
    
    # Check if already watered today
    last_watered = datetime.strptime(garden['last_watered'], '%Y-%m-%d').date()
    
    if last_watered != today:
        garden['last_watered'] = today.strftime('%Y-%m-%d')
        
        # Water plants
        for plot in garden['plots']:
            if plot['plant'] is not None:
                plant_type = plot['plant']
                plant_data = PLANT_TYPES[plant_type]
                
                # Update health and watered status
                plot['health'] = min(plant_data['max_health'], plot['health'] + 1)
                plot['watered'] = True
                
                # Update growth
                if plot['last_growth_date'] != today.strftime('%Y-%m-%d'):
                    plot['growth_days'] = min(plant_data['growth_time'], plot['growth_days'] + 1)
                    plot['last_growth_date'] = today.strftime('%Y-%m-%d')
    
    return jsonify({
        'success': True,
        'message': f'Lesson completed! You earned {xp_reward} XP and {gem_reward} gems.',
        'xp_earned': xp_reward,
        'gem_reward': gem_reward,
        'total_xp': progress['xp'],
        'course_level': course_progress['level'],
        'level_up': level_up,
        'new_achievements': new_achievements,
        'plants_watered': (last_watered != today)
    })

@app.route('/api/exercises/<exercise_id>/check', methods=['POST'])
def check_exercise(exercise_id):
    """Check an exercise answer"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = authenticate(token)
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    if exercise_id not in exercises:
        return jsonify({'error': 'Exercise not found'}), 404
    
    data = request.json
    if not data or 'answer' not in data:
        return jsonify({'error': 'Answer is required'}), 400
    
    answer = data['answer']
    exercise = exercises[exercise_id]
    
    # Check the answer (this would normally be more sophisticated)
    correct = False
    correct_answer = exercise.get('correct_answer', '')
    
    if exercise['type'] == 'multiple_choice':
        correct = answer == correct_answer
    elif exercise['type'] == 'text_input':
        # Simple string comparison, could be more sophisticated
        correct = answer.lower().strip() == correct_answer.lower().strip()
    elif exercise['type'] == 'true_false':
        correct = answer == correct_answer
    elif exercise['type'] == 'fill_blanks':
        # For fill in the blanks, answer should be a list
        if isinstance(answer, list) and isinstance(correct_answer, list):
            correct = all(a.lower().strip() == c.lower().strip() 
                         for a, c in zip(answer, correct_answer))
        else:
            correct = False
    
    # Small XP reward for attempting
    if user_id:
        progress = get_user_progress(user_id)
        xp_reward = 1 if correct else 0
        progress['xp'] += xp_reward
    
    return jsonify({
        'correct': correct,
        'correct_answer': correct_answer,
        'explanation': exercise.get('explanation', '')
    })

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get user leaderboard by XP"""
    # Collect user progress data
    leaderboard_data = []
    
    for username, user_data in users.items():
        user_id = user_data['id']
        if user_id in user_progress:
            progress = user_progress[user_id]
            
            # Get garden info
            garden = gardens.get(user_id, {})
            plants_count = 0
            if 'plots' in garden:
                for plot in garden['plots']:
                    if plot.get('plant') is not None:
                        plants_count += 1
            
            # Get economy info
            user_economy = economy.get(user_id, {'gems': 0})
            
            leaderboard_data.append({
                'username': username,
                'xp': progress.get('xp', 0),
                'plants': plants_count,
                'gems': user_economy.get('gems', 0)
            })
    
    # Sort by XP (descending)
    leaderboard_data.sort(key=lambda x: x['xp'], reverse=True)
    
    # Take top 20
    top_leaderboard = leaderboard_data[:20]
    
    return jsonify({
        'leaderboard': top_leaderboard
    })

# Initialize sample data when server starts
def initialize_sample_data():
    # Create a sample subject if none exist
    if not subjects:
        subjects['python'] = {
            'id': 'python',
            'name': 'Python Programming',
            'description': 'Learn Python programming from scratch',
            'icon': '🐍'
        }
        
        subjects['math'] = {
            'id': 'math',
            'name': 'Mathematics',
            'description': 'Essential mathematics for everyone',
            'icon': '🔢'
        }
    
    # Create sample courses if none exist
    if not courses:
        courses['python-basics'] = {
            'id': 'python-basics',
            'title': 'Python Basics',
            'subject_id': 'python',
            'subject_name': 'Python Programming',
            'difficulty': 'Beginner',
            'description': 'Introduction to Python programming language',
            'lessons': [
                {
                    'id': 'python-intro',
                    'title': 'Introduction to Python',
                    'description': 'Learn about Python and set up your environment'
                },
                {
                    'id': 'python-syntax',
                    'title': 'Python Syntax',
                    'description': 'Learn basic Python syntax and structure'
                }
            ]
        }
        
        courses['algebra-101'] = {
            'id': 'algebra-101',
            'title': 'Algebra Fundamentals',
            'subject_id': 'math',
            'subject_name': 'Mathematics',
            'difficulty': 'Intermediate',
            'description': 'Core concepts of algebra',
            'lessons': [
                {
                    'id': 'algebra-intro',
                    'title': 'Introduction to Algebra',
                    'description': 'Basic algebraic concepts'
                },
                {
                    'id': 'linear-equations',
                    'title': 'Linear Equations',
                    'description': 'Solving linear equations'
                }
            ]
        }
    
    # Create sample lessons if none exist
    if not lessons:
        lessons['python-intro'] = {
            'id': 'python-intro',
            'title': 'Introduction to Python',
            'description': 'Learn about Python and set up your environment',
            'course_id': 'python-basics',
            'xp_reward': 20,
            'exercises': [
                {
                    'id': 'python-intro-1',
                    'type': 'multiple_choice',
                    'question': 'What is Python?',
                    'options': [
                        'A snake',
                        'A programming language',
                        'A web browser',
                        'An operating system'
                    ],
                    'correct_answer': 'A programming language',
                    'explanation': 'Python is a high-level, interpreted programming language known for its readability.'
                }
            ]
        }
        
        lessons['python-syntax'] = {
            'id': 'python-syntax',
            'title': 'Python Syntax',
            'description': 'Learn basic Python syntax and structure',
            'course_id': 'python-basics',
            'xp_reward': 25,
            'exercises': [
                {
                    'id': 'python-syntax-1',
                    'type': 'text_input',
                    'question': 'What function is used to print text in Python?',
                    'correct_answer': 'print',
                    'explanation': 'The print() function is used to output text in Python.'
                }
            ]
        }
        
        lessons['algebra-intro'] = {
            'id': 'algebra-intro',
            'title': 'Introduction to Algebra',
            'description': 'Basic algebraic concepts',
            'course_id': 'algebra-101',
            'xp_reward': 20,
            'exercises': [
                {
                    'id': 'algebra-intro-1',
                    'type': 'true_false',
                    'question': 'Algebra uses letters to represent unknown numbers.',
                    'correct_answer': True,
                    'explanation': 'In algebra, letters like x, y, and z are often used as variables to represent unknown values.'
                }
            ]
        }
        
        lessons['linear-equations'] = {
            'id': 'linear-equations',
            'title': 'Linear Equations',
            'description': 'Solving linear equations',
            'course_id': 'algebra-101',
            'xp_reward': 30,
            'exercises': [
                {
                    'id': 'linear-equations-1',
                    'type': 'text_input',
                    'question': 'Solve for x: 2x + 5 = 13',
                    'correct_answer': '4',
                    'explanation': '2x + 5 = 13 → 2x = 8 → x = 4'
                }
            ]
        }
    
    # Create sample exercises if none exist
    if not exercises:
        exercises['python-intro-1'] = {
            'id': 'python-intro-1',
            'type': 'multiple_choice',
            'question': 'What is Python?',
            'options': [
                'A snake',
                'A programming language',
                'A web browser',
                'An operating system'
            ],
            'correct_answer': 'A programming language',
            'explanation': 'Python is a high-level, interpreted programming language known for its readability.'
        }
        
        exercises['python-syntax-1'] = {
            'id': 'python-syntax-1',
            'type': 'text_input',
            'question': 'What function is used to print text in Python?',
            'correct_answer': 'print',
            'explanation': 'The print() function is used to output text in Python.'
        }
        
        exercises['algebra-intro-1'] = {
            'id': 'algebra-intro-1',
            'type': 'true_false',
            'question': 'Algebra uses letters to represent unknown numbers.',
            'correct_answer': True,
            'explanation': 'In algebra, letters like x, y, and z are often used as variables to represent unknown values.'
        }
        
        exercises['linear-equations-1'] = {
            'id': 'linear-equations-1',
            'type': 'text_input',
            'question': 'Solve for x: 2x + 5 = 13',
            'correct_answer': '4',
            'explanation': '2x + 5 = 13 → 2x = 8 → x = 4'
        }
    
    # Initialize some achievements
    if not achievements:
        achievements['first_lesson'] = {
            'id': 'first_lesson',
            'name': 'First Step',
            'description': 'Complete your first lesson',
            'icon': '🏆',
            'xp_bonus': 10
        }
        
        achievements['plant_master'] = {
            'id': 'plant_master',
            'name': 'Garden Master',
            'description': 'Grow all types of plants',
            'icon': '🌻',
            'xp_bonus': 50
        }
    
    print("Sample data initialized!")

initialize_sample_data()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get API keys from environment variables
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Initialize the AudioTranscriber
transcriber = AudioTranscriber()

# Initialize the WhisperTranscriber for voice messages
voice_transcriber = WhisperTranscriber(model_name="openai/whisper-small")

# Initialize web search
web_search_ai = WebSearchAI()

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Dictionary to store user model preferences
user_models = {}

# Default AI model to use
DEFAULT_AI_MODEL = "google/gemini-2.0-flash-exp:free"

# Available AI models with descriptions
AI_MODELS = {
    "nousresearch/deephermes-3-llama-3-8b-preview:free": "Optimized for fast processing with good comprehension",
    "cognitivecomputations/dolphin3.0-r1-mistral-24b:free": "Great for creative writing and detailed explanations",
    "google/gemini-2.0-flash-lite-preview-02-05:free": "Fast responses with Google's knowledge foundation",
    "qwen/qwen-vl-plus:free": "Excellent multilingual capabilities and cultural understanding",
    "google/gemini-2.0-pro-exp-02-05:free": "Advanced reasoning and detailed knowledge base",
    "qwen/qwen2.5-vl-72b-instruct:free": "Superior at following complex instructions and detailed analysis",
    "deepseek/deepseek-r1-distill-llama-70b:free": "Balance of speed and accuracy with expansive knowledge",
    "deepseek/deepseek-r1:free": "Excellent for academic and technical content",
    "deepseek/deepseek-chat:free": "Optimized for conversational and quick responses",
    "google/gemini-2.0-flash-thinking-exp-1219:free": "Enhanced reasoning with fast response time",
    "qwen/qwen-2.5-coder-32b-instruct:free": "Specializes in programming and technical documentation",
    "mistralai/mistral-nemo:free": "Balanced performance across a wide range of topics",
    "google/gemini-2.0-flash-exp:free": "Fast, balanced model with good general knowledge (Default)"
}

# Create Flask app
app = Flask(__name__)

# Helper function to generate AI responses with OpenRouter
def generate_ai_response(prompt, user_id=None):
    # Determine which model to use
    model = DEFAULT_AI_MODEL
    if user_id and user_id in user_models:
        model = user_models[user_id]
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://personallearningbot.com",  # Replace with your domain
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            # Extract model name for logging/display
            used_model = result.get("model", model).split("/")[-1].split(":")[0]
            response_content = result["choices"][0]["message"]["content"]
            return {
                "success": True,
                "model": used_model,
                "content": response_content
            }
        else:
            return {
                "success": False,
                "error": "No response from AI service"
            }
    except Exception as e:
        logger.error(f"Error generating AI response with model {model}: {e}")
        return {
            "success": False,
            "error": f"Error: {str(e)}"
        }

# Helper function to convert text to speech
def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        return audio_io
    except Exception as e:
        logger.error(f"Error converting text to speech: {e}")
        return None

def fetch_and_parse_subtitle(subtitle_url):
    """
    Fetches and parses the subtitle content from the given URL.
    
    :param subtitle_url: The URL of the subtitle file.
    :return: Subtitle content as a string or None if failed.
    """
    try:
        response = requests.get(subtitle_url)
        if response.status_code != 200:
            return None

        subtitle_data = response.json()  # Parse the JSON response
        return parse_json_subtitle(subtitle_data)

    except Exception as e:
        logger.error(f"Error fetching subtitles: {e}")
        return None

def parse_json_subtitle(json_data):
    """
    Parses JSON subtitle data into plain text.
    
    :param json_data: The raw JSON subtitle data.
    :return: Subtitle text as a string.
    """
    try:
        events = json_data.get("events", [])
        subtitle_text = []

        for event in events:
            segs = event.get("segs", [])
            if not segs:
                continue

            # Combine all segments in the event
            event_text = "".join(segment.get("utf8", "") for segment in segs if "utf8" in segment)
            if event_text.strip():  # Ignore empty lines
                subtitle_text.append(event_text)

        return "\n".join(subtitle_text)  # Join all subtitle lines with newlines
    except Exception as e:
        logger.error(f"Error parsing subtitle JSON: {e}")
        return None

def sanitize_filename(filename):
    """
    Sanitizes a filename to remove invalid characters.
    
    :param filename: Original filename.
    :return: Sanitized filename.
    """
    if not filename:
        return "unknown_video"
        
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename

def check_for_subtitles(youtube_url, preferred_lang=None):
    """
    Checks if subtitles are available for the given YouTube URL.
    
    :param youtube_url: The URL of the YouTube video.
    :param preferred_lang: Preferred subtitle language code ('en' or 'uk')
    :return: Tuple of (subtitle_content, language, subtitle_type, video_title) or (None, None, None, title) if no subtitles.
    """
    try:
        # Define options for yt_dlp
        ydl_opts = {
            "skip_download": True,  # Skip downloading the video itself
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_title = info.get("title", "Unknown Video")
            
            available_languages = info.get("subtitles", {})
            auto_captions = info.get("automatic_captions", {})
            
            # Set requested languages based on preference
            if preferred_lang:
                requested_languages = [preferred_lang]
            else:
                requested_languages = ["en", "uk"]
            
            # Try manual subtitles first for the preferred language
            for lang in requested_languages:
                if lang in available_languages:
                    subtitle_info = available_languages[lang][0]
                    subtitle_content = fetch_and_parse_subtitle(subtitle_info["url"])
                    if subtitle_content:
                        return subtitle_content, lang, "Manual", video_title
            
            # Try auto-generated captions if no manual subtitles
            for lang in requested_languages:
                if lang in auto_captions:
                    subtitle_info = auto_captions[lang][0]
                    subtitle_content = fetch_and_parse_subtitle(subtitle_info["url"])
                    if subtitle_content:
                        return subtitle_content, lang, "Auto-Generated", video_title
            
            # No subtitles found for preferred language
            return None, None, None, video_title

    except Exception as e:
        logger.error(f"Error checking for subtitles: {e}")
        return None, None, None, None

# Routes
@app.route('/')
def index():
    return jsonify({
        "name": "Personal Learning API",
        "version": "1.0",
        "endpoints": [
            "/api/ai/generate",
            "/api/ai/models",
            "/api/ai/set-model",
            "/api/transcribe/url",
            "/api/transcribe/voice",
            "/api/tts",
            "/api/pdf",
            "/api/search"
        ],
        "documentation": "See /api/docs for more information"
    })

@app.route('/api/docs')
def docs():
    return jsonify({
        "endpoints": {
            "/api/ai/generate": {
                "method": "POST",
                "description": "Generate an AI response",
                "parameters": {
                    "prompt": "Text prompt to send to the AI",
                    "user_id": "(Optional) User ID for model preference"
                },
                "returns": "JSON with AI response"
            },
            "/api/ai/models": {
                "method": "GET",
                "description": "List available AI models",
                "returns": "JSON list of available models and descriptions"
            },
            "/api/ai/set-model": {
                "method": "POST",
                "description": "Set preferred AI model for a user",
                "parameters": {
                    "user_id": "User identifier",
                    "model_id": "Model identifier from /api/ai/models"
                },
                "returns": "Success/failure message"
            },
            "/api/transcribe/url": {
                "method": "POST",
                "description": "Transcribe audio/video from URL",
                "parameters": {
                    "url": "URL to video/audio content",
                    "language": "(Optional) Preferred subtitle language (en/uk)"
                },
                "returns": "Transcription text"
            },
            "/api/transcribe/voice": {
                "method": "POST",
                "description": "Transcribe uploaded audio file",
                "parameters": {
                    "file": "Audio file upload"
                },
                "returns": "Transcription text"
            },
            "/api/tts": {
                "method": "POST",
                "description": "Convert text to speech",
                "parameters": {
                    "text": "Text to convert to speech"
                },
                "returns": "Audio file (MP3)"
            },
            "/api/pdf": {
                "method": "POST",
                "description": "Convert text to PDF",
                "parameters": {
                    "text": "Text to convert to PDF",
                    "title": "(Optional) Title for the PDF"
                },
                "returns": "PDF file"
            },
            "/api/search": {
                "method": "POST",
                "description": "Search the web",
                "parameters": {
                    "query": "Search query"
                },
                "returns": "Search results"
            }
        }
    })

@app.route('/api/ai/generate', methods=['POST'])
def ai_generate():
    if not request.json or 'prompt' not in request.json:
        return jsonify({"success": False, "error": "Missing 'prompt' parameter"}), 400
    
    prompt = request.json.get('prompt')
    user_id = request.json.get('user_id', None)
    
    result = generate_ai_response(prompt, user_id)
    
    if result.get("success", False):
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/api/ai/models', methods=['GET'])
def ai_models():
    models_info = {}
    for model_id, description in AI_MODELS.items():
        model_name = model_id.split('/')[-1].split(':')[0]
        models_info[model_id] = {
            "name": model_name,
            "description": description,
            "is_default": (model_id == DEFAULT_AI_MODEL)
        }
    
    return jsonify({
        "success": True,
        "models": models_info
    })

@app.route('/api/ai/set-model', methods=['POST'])
def set_model():
    if not request.json:
        return jsonify({"success": False, "error": "Missing JSON body"}), 400
    
    user_id = request.json.get('user_id')
    model_id = request.json.get('model_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "Missing 'user_id' parameter"}), 400
    
    if not model_id:
        # Reset to default
        if user_id in user_models:
            del user_models[user_id]
        return jsonify({
            "success": True,
            "message": "Reset to default model",
            "model": DEFAULT_AI_MODEL
        })
    
    if model_id not in AI_MODELS and model_id != "default":
        return jsonify({
            "success": False, 
            "error": f"Invalid model ID. Use /api/ai/models to get valid IDs"
        }), 400
    
    if model_id == "default":
        if user_id in user_models:
            del user_models[user_id]
        return jsonify({
            "success": True,
            "message": "Reset to default model",
            "model": DEFAULT_AI_MODEL
        })
    else:
        user_models[user_id] = model_id
        return jsonify({
            "success": True,
            "message": f"Model set to {model_id}",
            "model": model_id
        })

@app.route('/api/transcribe/url', methods=['POST'])
def transcribe_url():
    if not request.json or 'url' not in request.json:
        return jsonify({"success": False, "error": "Missing 'url' parameter"}), 400
    
    url = request.json.get('url')
    language = request.json.get('language', 'en')  # Default to English
    
    # First try to get subtitles
    subtitle_content, lang, subtitle_type, video_title = check_for_subtitles(url, preferred_lang=language)
    
    if subtitle_content:
        # Return the subtitles if found
        return jsonify({
            "success": True,
            "source": "subtitles",
            "language": lang,
            "subtitle_type": subtitle_type,
            "video_title": video_title,
            "transcription": subtitle_content
        })
    else:
        # Fall back to audio transcription
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                transcript_file = os.path.join(temp_dir, "transcript.txt")
                
                # Process the URL using the AudioTranscriber
                transcript = transcriber.process_url(
                    url,
                    output_dir=temp_dir,
                    transcript_file=transcript_file,
                    keep_audio=False
                )
                
                if transcript:
                    return jsonify({
                        "success": True,
                        "source": "audio_transcription",
                        "video_title": video_title,
                        "transcription": transcript
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to transcribe audio from URL"
                    }), 500
        except Exception as e:
            logger.error(f"Error in transcription process: {e}")
            return jsonify({
                "success": False,
                "error": f"Error during transcription: {str(e)}"
            }), 500

@app.route('/api/transcribe/voice', methods=['POST'])
def transcribe_voice():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe the voice message
            transcription = voice_transcriber.transcribe_file(temp_file_path)
            
            if transcription:
                return jsonify({
                    "success": True,
                    "transcription": transcription
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to transcribe audio"
                }), 500
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error transcribing voice: {e}")
        return jsonify({
            "success": False,
            "error": f"Error during transcription: {str(e)}"
        }), 500

@app.route('/api/tts', methods=['POST'])
def tts():
    if not request.json or 'text' not in request.json:
        return jsonify({"success": False, "error": "Missing 'text' parameter"}), 400
    
    text = request.json.get('text')
    
    try:
        # Convert text to speech
        audio_io = text_to_speech(text)
        if audio_io:
            return send_file(
                audio_io,
                mimetype='audio/mp3',
                as_attachment=True,
                download_name='tts_output.mp3'
            )
        else:
            return jsonify({
                "success": False,
                "error": "Failed to convert text to speech"
            }), 500
    except Exception as e:
        logger.error(f"Error in TTS process: {e}")
        return jsonify({
            "success": False,
            "error": f"Error during text-to-speech conversion: {str(e)}"
        }), 500

@app.route('/api/pdf', methods=['POST'])
def pdf():
    if not request.json or 'text' not in request.json:
        return jsonify({"success": False, "error": "Missing 'text' parameter"}), 400
    
    text = request.json.get('text')
    title = request.json.get('title', '')
    
    # Combine title and text if title is provided
    if title:
        text_to_convert = f"# {title}\n\n{text}"
    else:
        text_to_convert = text
    
    try:
        # Generate a unique filename
        timestamp = int(time.time())
        if title:
            # Create a safe filename from title
            safe_title = ''.join(c for c in title if c.isalnum() or c in ' _-')
            filename = f"{safe_title}_{timestamp}.pdf"
        else:
            filename = f"document_{timestamp}.pdf"
        
        # Convert text to PDF
        pdf_path = text_to_pdf(text_to_convert, filename)
        
        if pdf_path and os.path.exists(pdf_path):
            try:
                return send_file(
                    pdf_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=filename
                )
            finally:
                # Clean up the PDF file after sending
                try:
                    os.unlink(pdf_path)
                    # Try to remove the parent directory if it's a temp dir
                    parent_dir = os.path.dirname(pdf_path)
                    if os.path.exists(parent_dir) and tempfile.gettempdir() in parent_dir:
                        os.rmdir(parent_dir)
                except Exception as e:
                    logger.error(f"Error cleaning up PDF file: {e}")
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate PDF"
            }), 500
    except Exception as e:
        logger.error(f"Error in PDF conversion: {e}")
        return jsonify({
            "success": False,
            "error": f"Error during PDF conversion: {str(e)}"
        }), 500

@app.route('/api/search', methods=['POST'])
def web_search():
    if not request.json or 'query' not in request.json:
        return jsonify({"success": False, "error": "Missing 'query' parameter"}), 400
    
    query = request.json.get('query')
    
    try:
        # Perform the web search
        search_result = web_search_ai.answer_query(query)
        
        return jsonify({
            "success": True,
            "query": query,
            "result": search_result
        })
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return jsonify({
            "success": False,
            "error": f"Error during web search: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Check if required environment variables are set
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY environment variable is not set. AI response features will not work.")
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Start the server
    app.run(host='0.0.0.0', port=port, debug=False)
