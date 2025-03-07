import requests
import json
import sys
import os

# API base URL - change this to your server's address
BASE_URL = "http://localhost:5000"

def print_response(response):
    """Pretty print the response from the API"""
    try:
        print(f"Status Code: {response.status_code}")
        if response.headers.get('Content-Type') == 'application/json':
            data = response.json()
            print("Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Content Type: {response.headers.get('Content-Type')}")
            print("Non-JSON response received")
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(response.text)

def list_models():
    """List available AI models"""
    url = f"{BASE_URL}/api/ai/models"
    response = requests.get(url)
    print_response(response)

def set_model(user_id, model_id):
    """Set preferred AI model for a user"""
    url = f"{BASE_URL}/api/ai/set-model"
    data = {
        "user_id": user_id,
        "model_id": model_id
    }
    response = requests.post(url, json=data)
    print_response(response)

def generate_response(prompt, user_id=None):
    """Generate an AI response"""
    url = f"{BASE_URL}/api/ai/generate"
    data = {
        "prompt": prompt,
        "user_id": user_id
    }
    response = requests.post(url, json=data)
    print_response(response)

def transcribe_url(url, language=None):
    """Transcribe audio/video from URL"""
    api_url = f"{BASE_URL}/api/transcribe/url"
    data = {
        "url": url,
        "language": language
    }
    response = requests.post(api_url, json=data)
    print_response(response)

def transcribe_voice(file_path):
    """Transcribe uploaded audio file"""
    url = f"{BASE_URL}/api/transcribe/voice"
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    print_response(response)

def text_to_speech(text):
    """Convert text to speech"""
    url = f"{BASE_URL}/api/tts"
    data = {
        "text": text
    }
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        output_file = "tts_output.mp3"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"Speech saved to {output_file}")
    else:
        print_response(response)

def text_to_pdf(text, title=None):
    """Convert text to PDF"""
    url = f"{BASE_URL}/api/pdf"
    data = {
        "text": text,
        "title": title
    }
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        output_file = "output.pdf"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"PDF saved to {output_file}")
    else:
        print_response(response)

def web_search(query):
    """Search the web"""
    url = f"{BASE_URL}/api/search"
    data = {
        "query": query
    }
    response = requests.post(url, json=data)
    print_response(response)

def print_help():
    """Print help information"""
    print("Available commands:")
    print("  list-models - List available AI models")
    print("  set-model <user_id> <model_id> - Set preferred AI model for a user")
    print("  generate <prompt> [user_id] - Generate an AI response")
    print("  transcribe-url <url> [language] - Transcribe audio/video from URL")
    print("  transcribe-voice <file_path> - Transcribe uploaded audio file")
    print("  tts <text> - Convert text to speech")
    print("  pdf <text> [title] - Convert text to PDF")
    print("  search <query> - Search the web")
    print("  help - Show this help message")

def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list-models":
        list_models()
    
    elif command == "set-model":
        if len(sys.argv) < 4:
            print("Usage: set-model <user_id> <model_id>")
            return
        set_model(sys.argv[2], sys.argv[3])
    
    elif command == "generate":
        if len(sys.argv) < 3:
            print("Usage: generate <prompt> [user_id]")
            return
        user_id = sys.argv[3] if len(sys.argv) > 3 else None
        generate_response(sys.argv[2], user_id)
    
    elif command == "transcribe-url":
        if len(sys.argv) < 3:
            print("Usage: transcribe-url <url> [language]")
            return
        language = sys.argv[3] if len(sys.argv) > 3 else None
        transcribe_url(sys.argv[2], language)
    
    elif command == "transcribe-voice":
        if len(sys.argv) < 3:
            print("Usage: transcribe-voice <file_path>")
            return
        transcribe_voice(sys.argv[2])
    
    elif command == "tts":
        if len(sys.argv) < 3:
            print("Usage: tts <text>")
            return
        text_to_speech(sys.argv[2])
    
    elif command == "pdf":
        if len(sys.argv) < 3:
            print("Usage: pdf <text> [title]")
            return
        title = sys.argv[3] if len(sys.argv) > 3 else None
        text_to_pdf(sys.argv[2], title)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: search <query>")
            return
        web_search(sys.argv[2])
    
    elif command == "help":
        print_help()
    
    else:
        print(f"Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()