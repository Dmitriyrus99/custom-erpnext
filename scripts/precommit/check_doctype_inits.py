import os
from pathlib import Path

ROOT = Path("apps/ferum_custom/ferum_custom/doctype")
missing = []

for p in ROOT.rglob("*"):
    if not p.is_dir():
        continue
    if p.name == "__pycache__":
        continue
    if not (p / "__init__.py").exists():
        missing.append(str(p))
if missing:
    print("❌ Missing __init__.py in:", *missing, sep="\n - ")
    exit(1)
print("✅ Doctype init check passed.")
