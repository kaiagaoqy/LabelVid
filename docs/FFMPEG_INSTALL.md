# FFmpeg Installation Guide

FFmpeg is required for:
- **Audio playback** in video mode
- **Caption extraction** with Whisper
- **Audio stream detection**

## Quick Install

### macOS
```bash
brew install ffmpeg
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

### Windows

#### Option 1: Chocolatey (Recommended)
```powershell
choco install ffmpeg
```

#### Option 2: Scoop
```powershell
scoop install ffmpeg
```

#### Option 3: Manual Installation
1. Download from https://www.gyan.dev/ffmpeg/builds/
2. Extract to `C:\ffmpeg\`
3. Add `C:\ffmpeg\bin` to your PATH:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Edit "Path" under System variables
   - Add `C:\ffmpeg\bin`
   - Click OK and restart your terminal

## Verify Installation

Open a terminal and run:
```bash
ffmpeg -version
ffprobe -version
```

You should see version information for both commands.

## Troubleshooting

### "ffmpeg not found" Error in Packaged App

The standalone `.app`/`.exe` looks for ffmpeg in your system PATH. If you see this error:

1. **Verify ffmpeg is installed**:
   ```bash
   which ffmpeg  # macOS/Linux
   where ffmpeg  # Windows
   ```

2. **Check common locations**:
   - macOS:
     - `/usr/local/bin/ffmpeg` (Intel Homebrew)
     - `/opt/homebrew/bin/ffmpeg` (Apple Silicon Homebrew)
   - Linux:
     - `/usr/bin/ffmpeg`
   - Windows:
     - `C:\ffmpeg\bin\ffmpeg.exe`
     - `C:\ProgramData\chocolatey\bin\ffmpeg.exe`

3. **Restart the application** after installing ffmpeg

### Permissions Issues (macOS)

If ffmpeg is installed but not found:

```bash
# Add Homebrew bin to PATH (Apple Silicon)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or Intel Mac
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Windows PATH Not Working

After adding ffmpeg to PATH:
1. Close ALL terminal/PowerShell windows
2. Restart any running applications
3. Open a NEW terminal to test

## What Works Without FFmpeg?

LabelVid will still work for:
- ✅ Video playback (video only, no audio)
- ✅ Frame extraction
- ✅ Clip marking
- ✅ Image annotation

Features requiring FFmpeg:
- ❌ Audio playback
- ❌ Whisper caption extraction
- ❌ Audio stream detection

## Advanced: Custom FFmpeg Location

If ffmpeg is installed in a non-standard location, you can create a symlink:

### macOS/Linux
```bash
sudo ln -s /path/to/ffmpeg /usr/local/bin/ffmpeg
sudo ln -s /path/to/ffprobe /usr/local/bin/ffprobe
```

### Windows (Run as Administrator)
```powershell
mklink C:\Windows\System32\ffmpeg.exe "C:\path\to\ffmpeg.exe"
mklink C:\Windows\System32\ffprobe.exe "C:\path\to\ffprobe.exe"
```

## Still Having Issues?

1. Check the application logs for detailed error messages
2. Verify ffmpeg works from command line first
3. Try running the application from terminal to see error output
4. Open an issue on GitHub with:
   - Your OS and version
   - Output of `which ffmpeg` or `where ffmpeg`
   - Output of `ffmpeg -version`
   - Full error message from LabelVid
