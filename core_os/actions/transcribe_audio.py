import os
import sys
import subprocess
import speech_recognition as sr
from pathlib import Path

def convert_m4a_to_wav(m4a_path):
    """Converts .m4a to .wav using ffmpeg."""
    path = Path(m4a_path)
    if not path.exists():
        print(f"Error: File {m4a_path} not found.")
        return None
    
    wav_path = path.with_suffix('.wav')
    
    # Check if wav already exists to avoid redundant conversion
    if wav_path.exists():
        return str(wav_path)

    print(f"Converting {path.name} to WAV...")
    try:
        command = ['ffmpeg', '-i', str(path), '-ac', '1', '-ar', '16000', str(wav_path), '-y', '-hide_banner', '-loglevel', 'error']
        subprocess.run(command, check=True)
        return str(wav_path)
    except subprocess.CalledProcessError as e:
        print(f"Error converting file: {e}")
        return None
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg.")
        return None

def transcribe_audio(wav_path):
    """Transcribes audio using SpeechRecognition (Google Web Speech API)."""
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        
    try:
        print("Transcribing...")
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "[Unintelligible Audio]"
    except sr.RequestError as e:
        return f"[API Error: {e}]"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_audio.py <path_to_m4a_or_wav>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    if input_file.lower().endswith('.m4a'):
        wav_file = convert_m4a_to_wav(input_file)
    else:
        wav_file = input_file
        
    if wav_file:
        transcript = transcribe_audio(wav_file)
        print("\n--- TRANSCRIPT ---")
        print(transcript)
        print("------------------")
