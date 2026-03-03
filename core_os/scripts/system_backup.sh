#!/bin/bash

# Configuration
BACKUP_DIR="core_os/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="full_system_backup_$TIMESTAMP.tar.gz"
LATEST_LINK="$BACKUP_DIR/latest_backup.tar.gz"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "[*] Initiating System Backup..."

# Create tarball of current directory, excluding backups and tmp
# We exclude the backup directory itself to prevent recursion loop
tar --exclude="$BACKUP_DIR" --exclude="venv" --exclude="__pycache__" --exclude=".git" -czf "$BACKUP_DIR/$BACKUP_NAME" .

if [ $? -eq 0 ]; then
    echo "[+] Backup created successfully: $BACKUP_DIR/$BACKUP_NAME"
    
    # Manage rotation: Remove old backups, keep only the 3 most recent
    # (Adjust 'tail -n +4' to change retention count: +4 keeps 3)
    ls -t "$BACKUP_DIR"/full_system_backup_*.tar.gz | tail -n +4 | xargs -r rm --
    
    # Update 'latest' symlink for easy restoration
    rm -f "$LATEST_LINK"
    ln -s "$BACKUP_NAME" "$LATEST_LINK"
    
    echo "[+] Rotation complete. Latest 3 backups retained."
else
    echo "[!] Backup FAILED."
    exit 1
fi
