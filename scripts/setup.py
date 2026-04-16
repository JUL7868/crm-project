# setup.py
# Project bootstrap script for CRM system

import os
from pathlib import Path
import json

# Base project path (one level above /scripts)
BASE_DIR = Path(__file__).resolve().parent.parent

# Folder structure
folders = [
    "app/core",
    "app/ui",
    "app/utils",
    "data/input",
    "data/output",
    "data/temp",
    "data/archive",
    "assets/images",
    "assets/icons",
    "assets/templates",
    "config",
    "logs",
    "scripts",
    "docs"
]

# Files to initialize
files = {
    "logs/app.log": "",
    "logs/errors.log": "",
    "config/settings.json": {
        "app_name": "CRM System",
        "version": "0.1",
        "debug": True
    },
    "config/rules.json": {},
    "config/mappings.json": {},
    "docs/architecture.md": "# Architecture\n\n",
    "docs/roadmap.md": "# Roadmap\n\n",
    "docs/notes.md": "# Notes\n\n"
}

def create_folders():
    for folder in folders:
        path = BASE_DIR / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Folder: {path}")

def create_files():
    for file_path, content in files.items():
        path = BASE_DIR / file_path
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                if isinstance(content, dict):
                    json.dump(content, f, indent=4)
                else:
                    f.write(content)
            print(f"[OK] File: {path}")
        else:
            print(f"[SKIP] Exists: {path}")

def main():
    print("Setting up CRM project structure...\n")
    create_folders()
    create_files()
    print("\nSetup complete.")

if __name__ == "__main__":
    main()