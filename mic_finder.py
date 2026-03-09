import speech_recognition as sr
import os
import sys

def test_mic_index(idx):
    print(f"[*] Testing Mic Index {idx}...")
    r = sr.Recognizer()
    try:
        with sr.Microphone(device_index=idx) as source:
            r.adjust_for_ambient_noise(source, duration=1)
            print("  [+] Listening...")
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("  [+] Audio captured!")
            return True
    except Exception as e:
        print(f"  [!] Failed on index {idx}: {e}")
        return False

if __name__ == "__main__":
    indices = [18, 17, 16] # Built-in, default, pulse
    for i in indices:
        if test_mic_index(i):
            print(f"SUCCESS: Found working mic at index {i}")
            sys.exit(0)
    print("No working mic found in the priority list.")
