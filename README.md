# Tech-server
# v1
 - AI
 - web
 - sub
 - pdf
 - TODO
 - ВШО integration

# v2
 - database
 - social interactions
 - profiles
 - languages

# v3
 - mini games
 - uniquie features
 - API

# Availible commands
```
# Show help information
python client.py help

# List available AI models
python client.py list-models

# Set preferred AI model for a user
python client.py set-model <user_id> <model_id>

# Generate an AI response
python client.py generate <prompt> [user_id]

# Transcribe audio/video from URL
python client.py transcribe-url <url> [language]

# Transcribe uploaded audio file
python client.py transcribe-voice <file_path>

# Convert text to speech
python client.py tts <text>

# Convert text to PDF
python client.py pdf <text> [title]

# Search the web
python client.py search <query>
```

# Complete List of API Endpoints in server.py
# Authentication Endpoints
```
GET /api/status - Check server status
POST /api/register - Register a new user
POST /api/login - Authenticate a user and receive JWT token
```
# AI Generation Endpoints (from botv6.py)
```
POST /api/generate - Generate AI responses using selected model
GET /api/ai/models - List all available AI models and current selection
POST /api/ai/models - Change the AI model for the current user
```
# Transcription Endpoints (from botv6.py)
```
POST /api/transcribe/url - Transcribe audio/video from a URL (YouTube, etc.)
POST /api/transcribe/voice - Transcribe uploaded voice file
```
# Content Generation Endpoints (from botv6.py)
```
POST /api/tts - Convert text to speech (returns audio file)
POST /api/pdf - Convert text to PDF (returns PDF file)
POST /api/web/search - Search the web for information on a query
```
# User & Learning Platform Endpoints (from main.py)
```
GET /api/user/profile - Get user profile and learning progress
```
