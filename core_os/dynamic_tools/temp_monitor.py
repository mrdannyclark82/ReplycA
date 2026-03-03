import os

def monitor_system_temperature():
    # Get the current CPU temperature
    temp = os.popen("sensors | grep 'Core 0'").read().strip().split(': ')[1].strip()
    
    print(f"Current CPU Temperature: {temp}°C")

# Call the function to monitor system temperature
monitor_system_temperature()