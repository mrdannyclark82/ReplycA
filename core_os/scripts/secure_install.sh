#!/bin/bash

# Configuration
SCRIPT_DIR="$(dirname "$0")"
BACKUP_SCRIPT="$SCRIPT_DIR/system_backup.sh"

echo "[*] SECURE INSTALL WRAPPER INITIATED"

# 1. Pre-Install Backup
echo ">>> Step 1: Executing Pre-Install Backup..."
"$BACKUP_SCRIPT"

if [ $? -ne 0 ]; then
    echo "[!] CRITICAL: Pre-install backup failed. Aborting installation to protect system state."
    exit 1
fi

echo ">>> Backup Verified. Proceeding to installation..."

# 2. Execute the actual install command passed as arguments
# Example usage: ./secure_install.sh pip install pandas
echo ">>> Step 2: Running Install Command: $@"
"$@"

INSTALL_EXIT_CODE=$?

# 3. Post-Install Verification (Simple check)
if [ $INSTALL_EXIT_CODE -eq 0 ]; then
    echo "[+] Installation successful."
else
    echo "[!] Installation FAILED (Exit Code: $INSTALL_EXIT_CODE)."
    echo "[!] Recommendation: Check logs and consider restoring from 'core_os/backups/latest_backup.tar.gz' if system is unstable."
fi

exit $INSTALL_EXIT_CODE
