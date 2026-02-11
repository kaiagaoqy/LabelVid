#!/bin/bash
# LabelVid Release Builder for Conda Environment
# Usage: ./build_release.sh

set -e  # Exit on error

echo "=================================="
echo "LabelVid Release Builder"
echo "=================================="
echo ""

# Check if we're in conda environment
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "⚠️  Warning: Not in a conda environment"
    echo "   Activating labelvid environment..."
    eval "$(conda shell.bash hook)"
    conda activate labelvid
fi

echo "✓ Environment: $CONDA_DEFAULT_ENV"
echo "✓ Python: $(which python)"
echo ""

# Check dependencies
echo "Checking dependencies..."
python -c "import whisper; print('✓ Whisper:', whisper.__version__)" 2>/dev/null || echo "○ Whisper: not installed"
python -c "import osam; print('✓ OSAM:', osam.__version__)" 2>/dev/null || echo "○ OSAM: not installed"
echo ""

# Build
echo "Building executable..."
python build_exe.py --clean

if [ $? -eq 0 ]; then
    echo ""
    echo "Creating release package..."
    python create_release.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "=================================="
        echo "✅ Build Complete!"
        echo "=================================="
        echo ""
        echo "Output: releases/LabelVid-v*-macOS-*.zip"
        echo ""
        echo "Next steps:"
        echo "  1. Test the .app in dist/"
        echo "  2. Upload releases/*.zip to GitHub"
    fi
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
