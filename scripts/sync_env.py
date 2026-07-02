# Sync environment variables between frontend and backend
# Usage: python sync_env.py

import os
import shutil

BACKEND_ENV = r"D:\projects\sci-agent\backend\.env"
FRONTEND_ENV = r"D:\projects\sci-agent\frontend\.env.local"
TEMPLATE = r"D:\projects\sci-agent\.env.example"

def sync():
    # Read backend .env
    backend_vars = {}
    if os.path.exists(BACKEND_ENV):
        with open(BACKEND_ENV, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    backend_vars[key.strip()] = value.strip().strip('"')

    # Read template
    frontend_keys = {}
    if os.path.exists(TEMPLATE):
        with open(TEMPLATE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    frontend_keys[key.strip()] = value.strip().strip('"')

    # Merge: backend vars override template
    merged = {**frontend_keys, **backend_vars}

    # Write frontend .env.local
    lines = [f"{k}={v}" for k, v in merged.items()]
    with open(FRONTEND_ENV, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Synced {len(merged)} env vars to frontend/.env.local")

if __name__ == "__main__":
    sync()
