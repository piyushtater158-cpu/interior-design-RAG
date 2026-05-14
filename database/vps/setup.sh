#!/bin/bash
# Optional: prepare a VPS with Python tooling for one-off scripts (e.g. Gemini tagging tests).
# Reference images for the seed pipeline live under reference_dataset/ at repo root.

set -e

echo "=== Optional VPS Python env ==="
python3 -m pip install --upgrade pip
python3 -m pip install google-genai python-dotenv pillow

echo ""
echo "=== Next steps ==="
echo "  Copy reference images to the server, preserving style subfolders expected by database/seed/config.py:"
echo "    scp -r reference_dataset user@vps:/path/to/repo/"
echo "  Or symlink an existing dataset directory to reference_dataset on the VPS."
