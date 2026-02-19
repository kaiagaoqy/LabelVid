#!/bin/bash
# LabelVid Full Release Builder (with FFmpeg bundled)
# Usage: ./build_full_release.sh

set -e  # Exit on error

echo "══════════════════════════════════════════════════"
echo "  LabelVid Full Release Builder"
echo "  (All features included - FFmpeg bundled)"
echo "══════════════════════════════════════════════════"
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

# Check system architecture
ARCH=$(uname -m)
echo "✓ Architecture: $ARCH"
echo ""

# Check FFmpeg binaries
echo "Checking FFmpeg binaries..."
FFMPEG_BIN="resources/ffmpeg-macos-$ARCH"
FFPROBE_BIN="resources/ffprobe-macos-$ARCH"

if [ -f "$FFMPEG_BIN" ] && [ -f "$FFPROBE_BIN" ]; then
    echo "✓ FFmpeg binaries found:"
    ls -lh "$FFMPEG_BIN"
    ls -lh "$FFPROBE_BIN"
else
    echo "✗ FFmpeg binaries not found!"
    echo ""
    echo "Please copy FFmpeg binaries to resources/ directory:"
    echo "  cp /opt/homebrew/bin/ffmpeg resources/ffmpeg-macos-$ARCH"
    echo "  cp /opt/homebrew/bin/ffprobe resources/ffprobe-macos-$ARCH"
    echo ""
    exit 1
fi
echo ""

# Check dependencies
echo "Checking Python dependencies..."
python -c "import whisper; print('✓ Whisper:', whisper.__version__)" 2>/dev/null || echo "✗ Whisper: not installed"
python -c "import osam; print('✓ OSAM:', osam.__version__)" 2>/dev/null || echo "✗ OSAM: not installed"
python -c "import PyQt5; print('✓ PyQt5')" 2>/dev/null || echo "✗ PyQt5: not installed"
echo ""

# Build
echo "══════════════════════════════════════════════════"
echo "Building Full executable (with FFmpeg)..."
echo "══════════════════════════════════════════════════"
echo ""

python build_exe.py --clean

if [ $? -eq 0 ]; then
    echo ""
    echo "══════════════════════════════════════════════════"
    echo "Creating Full release package..."
    echo "══════════════════════════════════════════════════"
    echo ""
    
    # Create release with "Full" suffix
    python create_release.py --suffix Full
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "══════════════════════════════════════════════════"
        echo "✅ Full Build Complete!"
        echo "══════════════════════════════════════════════════"
        echo ""
        
        # Show release info
        RELEASE_FILE=$(ls -t releases/*Full*.zip 2>/dev/null | head -1)
        if [ -n "$RELEASE_FILE" ]; then
            echo "📦 Release package:"
            ls -lh "$RELEASE_FILE"
            echo ""
            
            # Calculate size
            SIZE=$(du -h "$RELEASE_FILE" | cut -f1)
            echo "Size: $SIZE"
            echo ""
        fi
        
        echo "Features included:"
        echo "  ✅ Video playback with audio"
        echo "  ✅ Image annotation (SAM/SAM2)"
        echo "  ✅ Whisper caption extraction (FFmpeg bundled)"
        echo "  ✅ LLM analysis (GPT, Gemini, Claude)"
        echo "  ✅ Batch processing"
        echo "  ✅ Object list management"
        echo ""
        echo "Next steps:"
        echo "  1. Test: open dist/LabelVid.app"
        echo "  2. Upload: releases/*Full*.zip to GitHub"
        echo ""
    else
        echo ""
        echo "❌ Release package creation failed!"
        exit 1
    fi
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
