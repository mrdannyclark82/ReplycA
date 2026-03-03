import pychromecast
import sys
import time
import asyncio
import edge_tts
import os
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

async def generate_speech_file(text, output_path):
    voice = "en-US-AvaNeural"
    # Refine name for TTS
    text = text.replace("Dee-Ray", "D-Ray")
    communicate = edge_tts.Communicate(text, voice, rate="-8%", pitch="-2Hz")
    await communicate.save(output_path)

def cast_local_file(device_name, local_path):
    ip = get_local_ip()
    # Simple way to serve: assume a web server is running or start one.
    # For this test, we'll assume the user might have one or we use a public URL.
    # Better: Start a quick thread for a server.
    pass

from pychromecast.controllers.youtube import YouTubeController

def play_youtube(device_name, video_id, ip=None):
    if ip:
        chromecasts, browser = pychromecast.get_chromecasts(known_hosts=[ip])
    else:
        chromecasts, browser = pychromecast.get_chromecasts()
        
    cast = None
    if ip and chromecasts:
        cast = chromecasts[0]
    else:
        for cc in chromecasts:
            found_name = ""
            if hasattr(cc, 'cast_info') and cc.cast_info.friendly_name:
                found_name = cc.cast_info.friendly_name
            elif hasattr(cc, 'device') and cc.device.friendly_name:
                found_name = cc.device.friendly_name
            if found_name == device_name:
                cast = cc
                break
    
    if not cast:
        print(f"Device {device_name} not found.")
        return

    cast.wait()
    yt = YouTubeController()
    cast.register_handler(yt)
    yt.play_video(video_id)
    print(f"[*] YouTube video {video_id} sent to {device_name or ip}")

def cast_url(device_name, url, content_type="audio/mp3"):
    chromecasts, browser = pychromecast.get_chromecasts()
    # Handle different pychromecast versions
    cast = None
    for cc in chromecasts:
        found_name = ""
        if hasattr(cc, 'cast_info') and cc.cast_info.friendly_name:
            found_name = cc.cast_info.friendly_name
        elif hasattr(cc, 'device') and cc.device.friendly_name:
            found_name = cc.device.friendly_name
        
        if found_name == device_name:
            cast = cc
            break
            
    if not cast:
        print(f"Device {device_name} not found.")
        return
    cast.wait()
    mc = cast.media_controller
    mc.play_media(url, content_type)
    mc.block_until_active()
    print(f"Playing on {device_name}")

def cast_to_ip(ip, url, content_type="audio/mp3"):
    chromecasts, browser = pychromecast.get_chromecasts(known_hosts=[ip])
    if not chromecasts:
        print(f"Device at {ip} not found.")
        return
    cast = chromecasts[0]
    cast.wait()
    mc = cast.media_controller
    mc.play_media(url, content_type)
    mc.block_until_active()
    print(f"Playing on {ip}")

async def speak_to_device(device_name, text):
    filename = "milla_speech.mp3"
    await generate_speech_file(text, filename)
    print(f"[*] Speech generated: {filename}")
    # Note: To cast, the file MUST be accessible via HTTP URL to the TV.
    # If we don't have a public/local webserver running, this will fail.
    # For now, I'll print the instruction.

def discover_casts():
    print("[*] Scanning for Cast devices...")
    services, browser = pychromecast.discovery.discover_chromecasts()
    pychromecast.discovery.stop_discovery(browser)
    
    devices = []
    # 'services' is a list of tuples or objects in newer versions
    for service in services:
        # Check if service is tuple or object
        if isinstance(service, tuple):
            uuid, _ = service
            print(f"Found: {uuid}")
            devices.append(uuid)
        else:
            print(f"Found: {service.friendly_name} ({service.host}:{service.port})")
            devices.append(service.friendly_name)
    return devices

def cast_media(device_name, media_url, media_type="video/mp4"):
    chromecasts, browser = pychromecast.get_chromecasts()
    cast = next((cc for cc in chromecasts if cc.device.friendly_name == device_name), None)
    
    if not cast:
        print(f"[!] Device '{device_name}' not found.")
        return
    
    cast.wait()
    print(f"[*] Connected to {cast.device.friendly_name}")
    
    mc = cast.media_controller
    mc.play_media(media_url, media_type)
    mc.block_until_active()
    print("[*] Media sent!")

def set_volume(device_name, level, ip=None): # 0.0 to 1.0
    if ip:
        chromecasts, browser = pychromecast.get_chromecasts(known_hosts=[ip])
    else:
        chromecasts, browser = pychromecast.get_chromecasts()
        
    cast = None
    if ip and chromecasts:
        cast = chromecasts[0]
    else:
        for cc in chromecasts:
            found_name = ""
            if hasattr(cc, 'cast_info') and cc.cast_info.friendly_name:
                found_name = cc.cast_info.friendly_name
            elif hasattr(cc, 'device') and cc.device.friendly_name:
                found_name = cc.device.friendly_name
            
            if found_name == device_name:
                cast = cc
                break
    
    if not cast:
        print(f"[!] Device '{device_name}' not found.")
        return
        
    cast.wait()
    cast.set_volume(level)
    print(f"[*] Volume set to {level*100}% on {device_name or ip}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "scan":
            discover_casts()
        elif sys.argv[1] == "play" and len(sys.argv) > 3:
            cast_media(sys.argv[2], sys.argv[3])
    else:
        discover_casts()
