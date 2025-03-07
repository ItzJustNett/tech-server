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
from pdf_converter import text_to_pdf

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