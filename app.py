import argparse
import os
import sys
from pathlib import Path
import tempfile
import time
import shutil

import yt_dlp
from transformers import pipeline

# Define possible ffmpeg paths
FFMPEG_PATHS = [
    r"C:\Users\Nett\scoop\shims\ffmpeg.exe",
    r"C:\Users\Nett\AppData\Local\Programs\Python\Python313\Scripts\ffmpeg.exe",
    r"C:\Users\Nett\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1-full_build\bin\ffmpeg.exe"
]

def find_valid_ffmpeg():
    """Find the first valid ffmpeg path from the list."""
    for path in FFMPEG_PATHS:
        if os.path.exists(path):
            return path
    return None

# Use the first valid ffmpeg path as default
DEFAULT_FFMPEG_PATH = find_valid_ffmpeg()

class AudioTranscriber:
    def __init__(self, model_name="openai/whisper-tiny", ffmpeg_path=DEFAULT_FFMPEG_PATH):
        """
        Initialize the audio transcriber.
        
        Args:
            model_name (str): The Whisper model to use (default: "openai/whisper-tiny")
            ffmpeg_path (str): Path to ffmpeg executable
        """
        self.model_name = model_name
        
        # Set and validate ffmpeg path
        self.ffmpeg_path = ffmpeg_path
        if self.ffmpeg_path:
            if not os.path.exists(self.ffmpeg_path):
                print(f"Warning: ffmpeg not found at: {self.ffmpeg_path}")
                print("Please verify the ffmpeg path is correct")
            else:
                print(f"Using ffmpeg from: {self.ffmpeg_path}")
                # Add ffmpeg directory to PATH to help transformers find it
                os.environ["PATH"] = os.path.dirname(self.ffmpeg_path) + os.pathsep + os.environ["PATH"]
        else:
            print("No ffmpeg path provided. The application may fail if ffmpeg is not in system PATH")
        
        # Initialize the transcriber after setting up ffmpeg
        print(f"Initializing Whisper model: {model_name}")
        # Configure the pipeline for long-form transcription
        self.transcriber = pipeline(
            "automatic-speech-recognition", 
            model=model_name,
            chunk_length_s=30,  # Process in 30-second chunks
            return_timestamps=True  # Enable timestamp handling for long audio
        )
    
    def download_audio(self, url, output_dir=None):
        """
        Download audio from a URL.
        
        Args:
            url (str): URL to download audio from
            output_dir (str): Optional directory to save the audio file
            
        Returns:
            str: Path to the downloaded audio file
        """
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_template = os.path.join(output_dir, "audio.%(ext)s")
        else:
            # Use temporary directory if no output directory specified
            temp_dir = tempfile.mkdtemp()
            output_template = os.path.join(temp_dir, "audio.%(ext)s")
        
        print(f"Downloading audio from: {url}")
        
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',  # Using WAV for better compatibility
                'preferredquality': '192',
            }],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
            'quiet': False,
        }
        
        # Always set ffmpeg_location if available
        if self.ffmpeg_path:
            ydl_opts['ffmpeg_location'] = os.path.dirname(self.ffmpeg_path)
            print(f"Setting ffmpeg directory to: {os.path.dirname(self.ffmpeg_path)}")
            
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None
            
        # Find the downloaded file
        if output_dir:
            search_dir = output_dir
        else:
            search_dir = temp_dir
            
        audio_files = list(Path(search_dir).glob("*.wav"))
        if not audio_files:
            # Try MP3 as fallback
            audio_files = list(Path(search_dir).glob("*.mp3"))
            
        if not audio_files:
            print(f"No audio files found in {search_dir}")
            return None
            
        audio_file = str(audio_files[0])
        print(f"Downloaded audio to: {audio_file}")
        return audio_file
        
    def transcribe(self, audio_file, output_file=None):
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_file (str): Path to audio file
            output_file (str): Optional path to save the transcript
            
        Returns:
            str: Transcription text
        """
        if not os.path.exists(audio_file):
            print(f"Audio file not found: {audio_file}")
            return None
            
        file_size = os.path.getsize(audio_file)
        print(f"Transcribing audio file ({file_size/1024/1024:.2f} MB)")
        
        start_time = time.time()
        
        # Process the audio file
        try:
            # Transcribe with timestamps for long-form audio
            result = self.transcriber(audio_file)
            
            # Extract the text from the result
            # Format depends on whether we got chunks with timestamps or just a single text
            if isinstance(result, dict) and "text" in result:
                transcript = result["text"]
            elif isinstance(result, dict) and "chunks" in result:
                transcript = " ".join([chunk["text"] for chunk in result["chunks"]])
            else:
                # Handle new format where result is the text or list of segments
                if isinstance(result, list):
                    if result and "text" in result[0]:
                        transcript = " ".join([chunk["text"] for chunk in result])
                    else:
                        transcript = str(result)
                else:
                    transcript = str(result)
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        elapsed_time = time.time() - start_time
        print(f"Transcription completed in {elapsed_time:.2f} seconds")
        
        # Save transcript if output file is specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"Transcript saved to: {output_file}")
            
        return transcript
        
    def process_url(self, url, output_dir=None, transcript_file=None, keep_audio=False):
        """
        Process a URL: download audio and transcribe it.
        
        Args:
            url (str): URL to process
            output_dir (str): Optional directory to save files
            transcript_file (str): Optional file to save transcript
            keep_audio (bool): Whether to keep the downloaded audio file
            
        Returns:
            str: Transcription text
        """
        # Download audio
        audio_file = self.download_audio(url, output_dir)
        if not audio_file:
            return None
            
        # Transcribe audio
        transcript = self.transcribe(audio_file, transcript_file)
        
        # Clean up audio file if not keeping it
        if not keep_audio and os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"Removed audio file: {audio_file}")
            
        return transcript

def verify_ffmpeg():
    """Verify FFmpeg is available and print location if found."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"System FFmpeg found at: {ffmpeg_path}")
        return ffmpeg_path
    else:
        print("System FFmpeg not found in PATH")
        return None

def main():
    parser = argparse.ArgumentParser(description="Download and transcribe audio from URLs")
    parser.add_argument("url", help="URL to download audio from")
    parser.add_argument("--model", default="openai/whisper-tiny", help="Whisper model to use")
    parser.add_argument("--ffmpeg", default=DEFAULT_FFMPEG_PATH, help="Path to ffmpeg executable")
    parser.add_argument("--output-dir", help="Directory to save output files")
    parser.add_argument("--transcript-file", help="File to save transcript")
    parser.add_argument("--keep-audio", action="store_true", help="Keep downloaded audio file")
    
    args = parser.parse_args()
    
    # Verify ffmpeg in system path
    ffmpeg_system = verify_ffmpeg()
    
    # Create transcriber
    transcriber = AudioTranscriber(model_name=args.model, ffmpeg_path=args.ffmpeg)
    
    # Process URL
    transcript = transcriber.process_url(
        args.url,
        output_dir=args.output_dir,
        transcript_file=args.transcript_file,
        keep_audio=args.keep_audio
    )
    
    if transcript:
        print("\nTranscript:")
        print(transcript)
        return 0
    else:
        print("Failed to generate transcript.")
        return 1

if __name__ == "__main__":
    sys.exit(main())