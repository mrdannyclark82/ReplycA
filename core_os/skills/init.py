import sys, os
from pathlib import Path
__all__ = []
for f in Path(__file__).parent.glob("skill_*.py"):
    mod_name = f.stem.replace("skill_", "")