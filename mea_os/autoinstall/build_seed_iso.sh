#!/bin/bash
# ============================================================
# MEA OS — Seed ISO Builder
# Creates the small "seed" ISO that VirtualBox reads alongside
# the Ubuntu Server 24.04 ISO to trigger fully automated install.
#
# Requirements: genisoimage (sudo apt install genisoimage)
# Usage: bash build_seed_iso.sh
# Output: mea-os-seed.iso  (mount this as 2nd CD in VirtualBox)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="$SCRIPT_DIR/mea-os-seed.iso"

echo "[*] Building MEA OS seed ISO..."

# Verify required files exist
if [ ! -f "$SCRIPT_DIR/user-data" ] || [ ! -f "$SCRIPT_DIR/meta-data" ]; then
    echo "[!] ERROR: user-data or meta-data not found in $SCRIPT_DIR"
    exit 1
fi

# Check for genisoimage
if ! command -v genisoimage &>/dev/null; then
    echo "[*] Installing genisoimage..."
    sudo apt-get install -y genisoimage
fi

# Build the seed ISO
genisoimage \
    -output "$OUTPUT" \
    -volid cidata \
    -joliet \
    -rock \
    "$SCRIPT_DIR/user-data" \
    "$SCRIPT_DIR/meta-data"

echo ""
echo "✅ Seed ISO built: $OUTPUT"
echo ""
echo "VirtualBox setup:"
echo "  1. Create VM: Ubuntu 24.04, 4GB+ RAM, 40GB+ disk"
echo "  2. Storage → Controller: IDE → Add optical drive"
echo "     Disk 1: ubuntu-24.04-live-server-amd64.iso"
echo "     Disk 2: mea-os-seed.iso"
echo "  3. Boot — installer runs fully automatically"
echo "  4. After install: remove both ISOs, reboot"
echo "  5. Login: nexus / nexus2026  (change password after first boot)"
echo ""
echo "NOTE: Install takes ~10-15 min (pip install is the slow part)"
