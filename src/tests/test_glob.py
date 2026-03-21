import glob
import os
from datetime import datetime, timedelta

ARCHIVE_PATH = "core_os/memory/thought_archives"
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
pattern = os.path.join(ARCHIVE_PATH, f"{yesterday}_*.md")
files = sorted(glob.glob(pattern))

print(f"Yesterday: {yesterday}")
print(f"Pattern: {pattern}")
print(f"Files found: {len(files)}")
for f in files[:5]:
    print(f" - {f}")
