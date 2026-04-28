#!/bin/bash
# VPS setup script for CLIP embedding generation
# Run this on the SSH VPS before running embed_images.py

set -e

echo "=== VPS Setup for CLIP Embeddings ==="

# Update pip
python3 -m pip install --upgrade pip

# Install PyTorch (CPU-only — use CUDA version if GPU available)
# For GPU: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
python3 -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install sentence-transformers with image support
python3 -m pip install "sentence-transformers[image]" Pillow numpy

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Copy images to this server: scp -r 'interior design lora training data set' user@vps:/path/"
echo "  2. Run: python3 embed_images.py --images-dir /path/to/images --output-dir /path/to/output"
echo "  3. Copy results back: scp -r user@vps:/path/to/output ./database/seed/cache/embeddings/"
