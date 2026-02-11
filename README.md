# LabelVid - Video Clipping & Image Annotation Tool

A professional video clipping and image annotation tool designed to work with [Labelme](https://github.com/wkentaro/labelme) for video annotation workflows.

[中文文档](docs/README_zh.md) | [Documentation](README.md)

## Features

### Video Mode (Video Clipping)
- **Video Loading**: Open video files or scan folders for videos (supports MP4, AVI, MOV, MKV, WebM, etc.)
- **Video Playback**: Play/pause, seek, and adjust playback speed (0.25x - 4x)
- **Audio Playback**: Synchronized audio playback with volume control
- **Clip Marking**: Mark start and end frames for video segments with custom labels
- **Visual Clip Timeline**: Interactive timeline showing all clips with draggable markers
- **Frame Extraction**: Export first and last frames of each clip as images
- **CSV Export**: Generate a table with clip information (label, start frame, end frame)
- **Auto-save**: Automatic saving of clips after each modification
- **Auto-load**: Automatically load existing clips.csv and captions when opening a video
- **Quick Jump**: Jump forward/backward by 1s, 5s, 10s, 30s, 1min, 5min for long videos
- **Preview Quality**: Adjustable preview quality for smooth playback of long videos
- **Clip Management**: Edit, delete, and navigate clips via right-click context menu

### Caption & Speech Recognition
- **AI Caption Extraction**: Use OpenAI Whisper for automatic speech recognition
- **Multiple Models**: Support for tiny, base, small, medium, large, turbo models
- **Multi-language**: Auto-detect or manually select transcription language
- **Real-time Display**: Display captions in real-time during video playback
- **Auto-load Captions**: Automatically load existing SRT files when opening videos
- **Caption Export**: Export captions to SRT or WebVTT subtitle format

### Image Mode (Image Annotation)
- **Polygon Annotation**: Draw polygons around objects
- **Rectangle/Bounding Box**: Draw rectangles for object detection
- **Circle, Line, Point**: Additional shape types for various annotation needs
- **AI-Assisted Annotation (SAM)**: Use SAM/SAM2 for automatic polygon generation
- **Edit Mode**: Move, resize, and modify shapes
- **Shape Management**: Edit labels, delete shapes via right-click context menu
- **Point Editing**: Remove individual points from polygons
- **Labelme Export**: Export annotations in Labelme-compatible JSON format
- **WST Mode**: Work with Saved Thumbnails - load pre-extracted frames for annotation

### Output Organization
All outputs are organized in a video-named folder:
```
video_name/
├── clips.csv          # Clip information
├── frames/            # Extracted frames
├── captions/          # SRT/VTT subtitle files
└── annotations/       # Labelme JSON annotations
```

## Installation

### From Source (Development)
```bash
cd labelvid
pip install -e .
```

### Optional Dependencies

For AI-assisted annotation (SAM support):
```bash
pip install -e ".[ai]"
```

For Whisper caption extraction:
```bash
pip install -e ".[whisper]"
```

For all features:
```bash
pip install -e ".[all]"
```

### System Requirements

**FFmpeg** is required for audio extraction and Whisper:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg

# Windows (using Scoop)
scoop install ffmpeg
```

## Quick Start

For quick testing without installation:
```bash
python run.py
python run.py /path/to/video.mp4
python run.py /path/to/video/folder
```

## Usage

### Launch the Application
```bash
labelvid
labelvid /path/to/video.mp4
labelvid /path/to/video/folder
```

### Video Mode Workflow
1. **Open Video**: Use File > Open to select a video file
2. **Navigate**: Use the slider, playback controls, or quick jump buttons
3. **Mark Clips**: 
   - Click "Mark Start" (or press `[`) to mark the beginning
   - Click "Mark End" (or press `]`) to mark the end
   - Enter a label name for the clip
4. **Manage Clips**: 
   - Right-click clips to edit, delete, or jump to start/end
   - Drag markers on the timeline to adjust clip boundaries
5. **Export**: Click "Extract Frames" to export frames and CSV

### Image Mode Workflow
1. **Switch Mode**: Click the mode toggle button or press `Ctrl+M`
2. **Select Image Source**: Current frame, WST folder, or auto-extract
3. **Draw Shapes**: Choose tool and click on the image
4. **Label Shapes**: Enter a label when prompted
5. **Edit Shapes**: Use Edit/Move mode (`E`) to modify shapes
6. **Save**: Click "Save Annotation" for Labelme JSON format

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **General** | |
| Ctrl+M | Toggle Video/Image Mode |
| Ctrl+O | Open file |
| Ctrl+D | Open directory |
| Ctrl+Q | Quit |
| **Video Mode** | |
| Space | Play/Pause |
| Left/Right Arrow | Previous/Next frame |
| Shift+Left/Right | Jump backward/forward |
| `[` | Mark clip start |
| `]` | Mark clip end |
| Delete | Delete selected clip |
| 1-6 | Quick jump (1s, 5s, 10s, 30s, 1min, 5min) |
| **Image Mode** | |
| P | Polygon mode |
| R | Rectangle mode |
| A | AI Polygon (SAM) mode |
| E | Edit/Move mode |
| Ctrl+Shift+S | Save annotation |
| Escape | Cancel current drawing |
| Enter/Space | Finalize shape |
| Delete | Delete selected shape/point |

## AI-Assisted Annotation (SAM)

1. Install: `pip install -e ".[ai]"`
2. Switch to Image Mode
3. Select "AI Polygon" and choose SAM model version
4. Click to add positive points, Shift+Click for negative points
5. Press Enter/Space or Ctrl+Click to finalize

**Available SAM Models:**
- `sam2:tiny/small/base/large` - SAM2 variants (recommended)
- `sam:vit_h/l/b` - Original SAM variants

## Whisper Caption Extraction

1. Install: `pip install -e ".[whisper]"`
2. Load a video in Video Mode
3. Enable "Captions (Whisper)" checkbox
4. Select model and language
5. Click "Extract Captions"
6. Export to SRT/WebVTT using "Export SRT"

**Available Models:** tiny, tiny.en, base, base.en, small, small.en, medium, medium.en, large, large-v2, large-v3, turbo

## Building Executable

To create a standalone executable:

```bash
# For conda users (recommended)
conda activate labelvid
./build_release.sh

# Or manually
python build_exe.py
python create_release.py
```

See [QUICK_RELEASE.md](docs/QUICK_RELEASE.md) for detailed release instructions.

## License

GPL-3.0
