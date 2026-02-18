# Whisper Setup Guide

## Overview

OpenAI Whisper provides automatic speech recognition for extracting captions from videos.

## Installation

### Quick Install

```bash
pip install -e ".[whisper]"
```

This installs:
- `openai-whisper`
- `ffmpeg-python` (Python wrapper)

### System Requirements

**FFmpeg** is required:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# Windows (Scoop)
scoop install ffmpeg
```

**GPU Support** (optional, faster):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Available Models

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | 39M | Fastest | Low | Quick tests |
| `tiny.en` | 39M | Fastest | Low | English only, quick tests |
| `base` | 74M | Fast | Medium | General use |
| `base.en` | 74M | Fast | Medium | English only |
| `small` | 244M | Medium | Good | Recommended |
| `small.en` | 244M | Medium | Good | English only, recommended |
| `medium` | 769M | Slow | Better | High accuracy needed |
| `medium.en` | 769M | Slow | Better | English only, high accuracy |
| `large` | 1550M | Slowest | Best | Maximum accuracy |
| `large-v2` | 1550M | Slowest | Best | Improved large |
| `large-v3` | 1550M | Slowest | Best | Latest large |
| `turbo` | 809M | Fast | Best | **Recommended** (v3 speed, v2 accuracy) |

**Recommendation:**
- **General use**: `turbo` or `small`
- **English only**: `base.en` or `small.en`
- **Maximum accuracy**: `large-v3`
- **Quick tests**: `tiny`

## Usage

### In LabelVid

1. **Open video** in Video Mode
2. **Enable**: Check "Captions (Whisper)" checkbox
3. **Select model**: Choose from dropdown (e.g., `turbo`)
4. **Select language**:
   - **Auto**: Auto-detect language
   - **Manual**: Choose from list (en, zh, es, fr, etc.)
5. **Extract**: Click "Extract Captions" button
6. **Wait**: Progress shown in status bar
7. **View**: Captions appear during playback
8. **Export**: Click "Export SRT" to save

### Output Location

Captions are saved to:
```
<video_name>/captions/<video_name>.srt
```

### Auto-Load

When opening a video, LabelVid automatically:
1. Checks for existing SRT file
2. Loads captions if found
3. Displays during playback

## Troubleshooting

### Error: "FFmpeg not found"

**Solution 1: Check PATH**
```bash
which ffmpeg
# Should output: /usr/local/bin/ffmpeg or similar
```

**Solution 2: Install FFmpeg**
```bash
brew install ffmpeg  # macOS
```

**Solution 3: Use Full Version**
- Download `LabelVid-Full.zip` from releases
- FFmpeg is bundled, no installation needed

See [FFmpeg Troubleshooting Guide](FFMPEG_TROUBLESHOOTING.md).

### Error: "Whisper not installed"

```bash
pip install -e ".[whisper]"
```

### Error: "Out of memory"

Use a smaller model:
- Try `tiny` or `base` instead of `large`
- Or enable GPU support

### Slow Processing

**Solutions:**
1. Use smaller model (`turbo` instead of `large`)
2. Install GPU support:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
3. Use `.en` models for English (faster)

### Inaccurate Transcriptions

**Solutions:**
1. Use larger model (`large-v3` or `turbo`)
2. Manually specify language (don't use auto-detect)
3. Ensure good audio quality in video

## Command-Line Usage (Advanced)

```bash
# Extract captions from Python
from labelvid._whisper import WhisperTranscriber

transcriber = WhisperTranscriber(model_name="turbo")
segments = transcriber.transcribe(video_path="video.mp4", language="en")
transcriber.save_srt(segments, output_path="output.srt")
```

## Performance Tips

1. **Model Selection**:
   - Start with `small` or `turbo`
   - Upgrade to `large-v3` if accuracy is insufficient

2. **GPU Acceleration**:
   - Install CUDA-compatible PyTorch
   - 10-50x faster than CPU

3. **Language Specification**:
   - Manual language selection is faster than auto-detect

4. **Batch Processing**:
   - Use Batch Process feature for multiple videos
   - Processes overnight for large datasets

## Language Support

Whisper supports 99+ languages, including:

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `zh` | Chinese |
| `es` | Spanish | `ja` | Japanese |
| `fr` | French | `ko` | Korean |
| `de` | German | `ru` | Russian |
| `it` | Italian | `ar` | Arabic |
| `pt` | Portuguese | `hi` | Hindi |

Full list: https://github.com/openai/whisper#available-models-and-languages

## Related Documentation

- [FFmpeg Troubleshooting](FFMPEG_TROUBLESHOOTING.md)
- [LLM Caption Analysis](LLM_ANALYSIS.md)
- [Batch Processing](BATCH_PROCESS_FEATURE.md)
- [Video Mode Guide](VIDEO_MODE.md)
