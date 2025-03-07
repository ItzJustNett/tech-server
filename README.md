Authentication

/api/status (GET) - Check server status
/api/register (POST) - Register new user
/api/login (POST) - Login user

AI Generation

/api/generate (POST) - Generate AI responses
/api/ai/models (GET) - Get available AI models
/api/ai/models (POST) - Set AI model

Transcription & Content

/api/transcribe/url (POST) - Transcribe audio/video from URLs
/api/transcribe/voice (POST) - Transcribe voice messages
/api/web/search (POST) - Perform web search
/api/tts (POST) - Convert text to speech
/api/pdf (POST) - Generate PDF from text

Garden System

/api/garden (GET) - Get garden status
/api/garden/water (POST) - Water plants
/api/garden/plant (POST) - Plant a seed
/api/garden/harvest (POST) - Harvest mature plant
/api/garden/seeds (GET) - Get available seeds

Inventory & Economy

/api/inventory (GET) - Get inventory
/api/inventory/use (POST) - Use inventory item
/api/shop (GET) - Get shop items
/api/shop/categories (GET) - Get shop categories
/api/shop/<category> (GET) - Get category items
/api/shop/purchase (POST) - Purchase item
/api/economy/balance (GET) - Get gem balance
/api/economy/transactions (GET) - Get transaction history
/api/economy/daily-bonus (POST) - Claim daily bonus

Helpers

/api/helpers (GET) - Get helpers
/api/helpers/activate (POST) - Activate helper
/api/helpers/deactivate (POST) - Deactivate helper

Learning

/api/courses (GET) - Get courses
/api/courses/<course_id> (GET) - Get specific course
/api/subjects (GET) - Get subjects
/api/subjects/<subject_id> (GET) - Get specific subject
/api/subjects/<subject_id>/courses (GET) - Get subject courses
/api/lessons/<lesson_id> (GET) - Get lesson
/api/lessons/<lesson_id>/complete (POST) - Complete lesson
/api/exercises/<exercise_id>/check (POST) - Check exercise

User Data

/api/user/profile (GET) - Get user profile
/api/leaderboard (GET) - Get XP leaderboard
