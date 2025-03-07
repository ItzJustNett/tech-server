import argparse
import os
from pathlib import Path
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import soundfile as sf
from scipy import signal

class WhisperTranscriber:
    def __init__(self, model_name="openai/whisper-small"):
        """
        Initialize the Whisper transcription model.
        
        Args:
            model_name (str): The name of the Whisper model to use.
                             Options: "openai/whisper-tiny", "openai/whisper-base", 
                                      "openai/whisper-small", "openai/whisper-medium", "openai/whisper-large"
        """
        print(f"Loading Whisper model: {model_name}")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load processor and model
        self.processor = WhisperProcessor.from_pretrained(model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(self.device)
        
        # Whisper models are trained on audio with a sampling rate of 16000
        self.target_sampling_rate = 16000
        
        print("Model loaded successfully!")
    
    def resample_audio(self, audio_array, orig_sr, target_sr):
        """
        Resample audio to target sampling rate
        
        Args:
            audio_array: NumPy array of audio samples
            orig_sr: Original sampling rate
            target_sr: Target sampling rate
            
        Returns:
            Resampled audio array
        """
        # Calculate resampling ratio
        number_of_samples = round(len(audio_array) * float(target_sr) / orig_sr)
        # Resample audio
        resampled_audio = signal.resample(audio_array, number_of_samples)
        return resampled_audio
    
    def transcribe_file(self, audio_path):
        """
        Transcribe a single audio file.
        
        Args:
            audio_path (str): Path to the audio file to transcribe
            
        Returns:
            str: Transcribed text
        """
        print(f"Transcribing: {audio_path}")
        
        # Load audio
        audio_array, sampling_rate = sf.read(audio_path)
        print(f"Original sampling rate: {sampling_rate} Hz")
        
        # Convert to mono if stereo
        if len(audio_array.shape) > 1:
            audio_array = audio_array.mean(axis=1)
        
        # Resample if necessary
        if sampling_rate != self.target_sampling_rate:
            print(f"Resampling from {sampling_rate} Hz to {self.target_sampling_rate} Hz")
            audio_array = self.resample_audio(audio_array, sampling_rate, self.target_sampling_rate)
            sampling_rate = self.target_sampling_rate
        
        # Process audio
        input_features = self.processor(
            audio_array, 
            sampling_rate=self.target_sampling_rate, 
            return_tensors="pt"
        ).input_features.to(self.device)
        
        # Generate transcription
        predicted_ids = self.model.generate(input_features)
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        return transcription
    
    def transcribe_directory(self, directory, output_dir=None):
        """
        Transcribe all audio files in a directory.
        
        Args:
            directory (str): Directory containing audio files
            output_dir (str, optional): Directory to save transcriptions. 
                                      If None, transcriptions are printed to console.
        
        Returns:
            dict: Dictionary mapping filenames to transcriptions
        """
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        results = {}
        directory_path = Path(directory)
        
        # Common audio file extensions
        audio_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
        
        for file_path in directory_path.iterdir():
            if file_path.suffix.lower() in audio_extensions:
                transcription = self.transcribe_file(str(file_path))
                results[file_path.name] = transcription
                
                if output_dir:
                    output_file = os.path.join(output_dir, f"{file_path.stem}.txt")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(transcription)
                    print(f"Saved transcription to: {output_file}")
                else:
                    print(f"\nTranscription for {file_path.name}:")
                    print(f"---------------------------")
                    print(transcription)
                    print(f"---------------------------\n")
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio files using Whisper")
    parser.add_argument("--model", type=str, default="openai/whisper-small", 
                        help="Whisper model to use (tiny, base, small, medium, large)")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to audio file or directory of audio files")
    parser.add_argument("--output", type=str, default=None, 
                        help="Directory to save transcriptions (if not provided, prints to console)")
    
    args = parser.parse_args()
    
    transcriber = WhisperTranscriber(model_name=args.model)
    
    if os.path.isdir(args.input):
        transcriber.transcribe_directory(args.input, args.output)
    else:
        transcription = transcriber.transcribe_file(args.input)
        
        if args.output:
            output_dir = args.output
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_file = os.path.join(output_dir, f"{Path(args.input).stem}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcription)
            print(f"Saved transcription to: {output_file}")
        else:
            print("\nTranscription:")
            print("---------------------------")
            print(transcription)
            print("---------------------------\n")


if __name__ == "__main__":
    main()