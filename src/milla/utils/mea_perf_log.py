import psutil
import time
import datetime
import os

LOG_FILE = "mea_performance.log"

def log_stats():
    # Ensure the file exists with a header if empty
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("Timestamp,CPU_Usage%,RAM_Usage%,Disk_Read_MB,Disk_Write_MB
")
            
    with open(LOG_FILE, "a") as f:
        f.write(f"
--- LOG SESSION START: {datetime.datetime.now()} ---
")
        
        last_io = psutil.disk_io_counters()
        
        while True:
            try:
                # Interval=1 gives us a more accurate CPU reading
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                current_io = psutil.disk_io_counters()
                
                # Calculate delta in MB
                read_mb = (current_io.read_bytes - last_io.read_bytes) / (1024 * 1024)
                write_mb = (current_io.write_bytes - last_io.write_bytes) / (1024 * 1024)
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"{timestamp},{cpu}%,{ram}%,{read_mb:.2f}MB/s,{write_mb:.2f}MB/s
"
                
                # Print to console for real-time visibility too
                print(f"[{timestamp}] CPU: {cpu}% | RAM: {ram}% | Disk: {read_mb:.2f}R/{write_mb:.2f}W MB/s", end='')
                
                f.write(log_entry)
                f.flush()
                
                last_io = current_io
                time.sleep(4) # Sample every 5 seconds total (1s from cpu_percent + 4s sleep)
            except KeyboardInterrupt:
                f.write(f"
--- LOG SESSION END: {datetime.datetime.now()} ---
")
                print("
Logging stopped.")
                break

if __name__ == "__main__":
    print(f"MEA OS Stability Watcher Active... Logging to {LOG_FILE}")
    log_stats()
