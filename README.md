# LabelVid - Video Clipping & Image Annotation Tool

A professional video clipping and image annotation tool designed to work with [Labelme](https://github.com/wkentaro/labelme) for video annotation workflows.

[中文文档](docs/README_zh.md) | [Documentation](README.md)

## Features

### Video Mode (Video Clipping)
- **Video Loading**: Open video files or scan folders for videos (supports MP4, AVI, MOV, MKV, WebM, etc.)
- **Video Playback**: Play/pause, seek, and adjust playback speed (0.25x - 4x)
- **Audio Playback**: Synchronized audio playback with volume control
- **Clip Marking**: Mark start and end frames for video segments with detailed metadata
  - Required: Label name
  - Optional: Detection score (0-5), Recognition score (0-5), Hazard flag, Description, Recognition, Scene
  - Category ID and Instance ID for dataset organization
- **Object List Management**: Import JSON-based object lists for consistent labeling
  - Dropdown label selection with category/instance ID display
  - Auto-fill category and instance IDs when selecting labels
  - Support for multiple instances of the same object
  - Manual editing still available
- **Visual Clip Timeline**: Interactive timeline showing all clips with draggable markers
- **Frame Extraction**: Export first and last frames of each clip as images
- **CSV Export**: Generate a table with clip information (label, start/end frame, scores, hazard, description, category/instance IDs)
- **Auto-save**: Automatic saving of clips after each modification
- **Auto-load**: Automatically load existing clips.csv and captions when opening a video
- **Quick Jump**: Jump forward/backward by 1s, 5s, 10s, 30s, 1min, 5min for long videos
- **Preview Quality**: Adjustable preview quality for smooth playback of long videos
- **Clip Management**: Edit all fields, delete, and navigate clips via right-click context menu

### Caption & Speech Recognition
- **AI Caption Extraction**: Use OpenAI Whisper for automatic speech recognition
- **Multiple Models**: Support for tiny, base, small, medium, large, turbo models
- **Multi-language**: Auto-detect or manually select transcription language
- **Real-time Display**: Display captions in real-time during video playback
- **Auto-load Captions**: Automatically load existing SRT files when opening videos
- **Caption Export**: Export captions to SRT or WebVTT subtitle format
- **Caption Search**: Search for keywords in captions and navigate between results
- **Timeline Highlighting**: Highlight frames containing search keywords on the timeline

### LLM Caption Analysis
- **AI-Powered Analysis**: Use GPT-5, GPT-4o, Gemini, or Claude to analyze captions
- **Smart Chunking**: Automatically split long captions into 20-segment chunks for optimal processing
- **Object Detection Extraction**: Extract object names, detection scores, recognition scores, hazard flags, and descriptions
- **Multiple Providers**: Support for OpenAI (GPT-5, GPT-4o, etc.), Google (Gemini), and Anthropic (Claude)
- **Auto-Fill Clips**: Automatically create/update video clips from LLM analysis results (category/instance IDs default to 0)
- **Auto-Save JSON**: Results automatically saved to `<video_name>/llm_analysis/<video_name>_llm_detections.json`
- **Secure API Key Storage**: Save API keys locally with QSettings
- **Compact UI**: Collapsible settings panel for minimal screen space usage
- **[📖 Full Documentation](docs/LLM_ANALYSIS.md)**

### Batch Processing
- **One-Click Processing**: Process multiple videos automatically
- **Caption Extraction Only**: Extract captions and save to SRT for all videos
- **Caption + LLM Analysis**: Extract captions, analyze with LLM, and auto-fill clips
- **Smart Skip**: Automatically load existing captions if available
- **Detailed Progress**: Real-time progress display showing current video, step, and details
- **Error Handling**: Continue processing remaining videos if one fails

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
├── clips.csv          # Clip information (label, start/end frame, scores, hazard, description, category/instance IDs)
├── frames/            # Extracted frames
├── captions/          # SRT/VTT subtitle files
├── annotations/       # Labelme JSON annotations
└── llm_analysis/      # LLM-extracted object detections (JSON)
    └── <video_name>_llm_detections.json
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

For LLM caption analysis:
```bash
pip install -e ".[llm]"
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
sudo xattr -rd com.apple.quarantine PATH-TO-APP

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
2. **Import Object List** (optional):
   - File > 📋 Manage Object List
   - Import JSON file with object definitions
   - Format: `[{"category_id": 1, "instance_id": 0, "label_name": "chair"}, ...]`
   - See `object_list.json` or `example_object_list.json` for examples
3. **Navigate**: Use the slider, playback controls, or quick jump buttons
4. **Mark Clips**: 
   - Click "Mark Start" (or press `[`) to mark the beginning
   - Click "Mark End" (or press `]`) to mark the end
   - Enter clip details in the dialog:
     - **Label** (required): Select from dropdown (if object list imported) or type manually
     - **Category/Instance IDs**: Auto-filled when selecting from dropdown, or manually enter
     - **Recognition** (optional): Recognition result
     - **Scene** (optional): Scene description
     - **Detection Score** (optional): 0-5 scale
     - **Recognition Score** (optional): 0-5 scale
     - **Is Hazard** (optional): Yes/No/Not set
     - **Description** (optional): Free text
5. **Manage Clips**: 
   - Right-click clips to edit all fields, delete, or jump to start/end
   - Drag markers on the timeline to adjust clip boundaries
   - Double-click clips to edit
6. **LLM Analysis** (optional):
   - Extract captions using Whisper
   - Click "🤖 Analyze & Fill Clips"
   - Configure LLM provider and model (click ⚙️)
   - LLM will automatically fill clip fields from captions (category/instance IDs default to 0)
7. **Batch Processing** (optional):
   - Load multiple videos (File > Open Directory)
   - Click "⚡ Batch Process" button
   - Choose: Caption Extraction Only or Caption + LLM Analysis
   - Monitor detailed progress for each video
8. **Export**: Click "Extract Frames" to export frames and CSV

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

## Object List Management

Use object lists to standardize labeling across your dataset:

1. **Create Object List JSON**:
```json
[
  {
    "category_id": 28,
    "instance_id": 0,
    "label_name": "red suitcase"
  },
  {
    "category_id": 30,
    "instance_id": 0,
    "label_name": "chair"
  },
  {
    "category_id": 30,
    "instance_id": 1,
    "label_name": "chair"
  }
]
```

2. **Import Object List**:
   - File > 📋 Manage Object List
   - Click "📂 Import JSON"
   - Select your object list file

3. **Use in Clips**:
   - When creating/editing clips, labels appear as dropdown: `"chair [cat:30, inst:1]"`
   - Category and Instance IDs auto-fill when selecting from dropdown
   - Manually edit IDs if needed
   - Can still type custom labels not in the list

4. **Benefits**:
   - ✅ Consistent labeling across team
   - ✅ Clear distinction between multiple instances
   - ✅ Dataset-ready category/instance IDs
   - ✅ Faster labeling with dropdown selection

See `object_list.json` or `example_object_list.json` for full examples.

## Batch Processing

Process multiple videos automatically:

1. **Load Videos**: File > Open Directory
2. **Start Batch Process**: Click "⚡ Batch Process" button
3. **Choose Mode**:
   - **Caption Extraction Only**: Extract and save captions to SRT
   - **Caption + LLM Analysis**: Extract captions, analyze with LLM, auto-fill clips, save JSON
4. **Monitor Progress**: Real-time display shows:
   - Current video (e.g., "Video 5/15: experiment_005.mp4")
   - Current step (e.g., "Extracting captions...", "Analyzing chunk 2/4...")
   - Detailed information (e.g., "Loaded 72 caption segments", "Found 15 detections")
5. **Review Results**: Check summary of successful/failed videos

**Smart Skip**: If captions already exist, they're automatically loaded and LLM analysis proceeds directly.

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
