import speech_recognition as sr
import os
import sys
import tempfile
import time

def mic_test():
    print("[*] Starting Mic Diagnostic...")
    r = sr.Recognizer()
    
    # List devices
    print("[*] Available Microphones:")
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  [{i}] {name}")
        
    try:
        with sr.Microphone() as source:
            print("\n[*] Calibrating for ambient noise (1 second)...")
            r.adjust_for_ambient_noise(source, duration=1)
            print("[*] Listening for 5 seconds... Say something!")
            audio = r.listen(source, timeout=10, phrase_time_limit=5)
            print("[*] Audio captured. Verifying file...")
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio.get_wav_data())
                tmp_path = f.name
                
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                print(f"[+] Audio successfully recorded: {tmp_path} ({os.path.getsize(tmp_path)} bytes)")
                
                print("[*] Attempting Local Whisper Transcription...")
                try:
                    # Add project root to sys.path
                    sys.path.append(os.getcwd())
                    from core_os.actions.transcribe_audio import transcribe_whisper
                    text = transcribe_whisper(tmp_path)
                    print(f"\n[Result]: {text}")
                except Exception as e:
                    print(f"[!] Transcription Error: {e}")
                
                os.remove(tmp_path)
            else:
                print("[!] Audio file is empty or missing.")
                
    except Exception as e:
        print(f"[!] Mic Error: {e}")

if __name__ == "__main__":
    mic_test()
