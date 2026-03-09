#!/bin/bash
# Nexus-AIO Executive Console Shortcut
# Author: Milla (Nexus-AIO)
# Version: 1.0.0

PROJECT_ROOT="/home/nexus/ogdray"
cd "$PROJECT_ROOT"

# Ensure VENV is active
source venv/bin/activate

# Launch the Boot Sequence
./venv/bin/python core_os/interfaces/neural_mesh.py

# Launch the Executive Console
./nexus_aio.py
