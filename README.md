# LabelVid - Video & Image Annotation Tool

<div align="center">

**A video clipping and image annotation tool with AI-powered features**

[English](README.md) | [中文文档](docs/README_zh.md)

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

</div>

---

## 📖 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Documentation](#documentation)
- [Building Executable](#building-executable)
- [License](#license)

---

[videomode](metadata/videomode.png)

## Overview

**LabelVid** is a comprehensive annotation tool designed for video analysis and image labeling workflows. It combines video clipping, speech recognition, LLM-powered caption analysis, and AI-assisted image segmentation into a unified interface.

**Perfect for:**
- 🎬 Video dataset preparation
- 📝 Caption extraction and analysis
- 🖼️ Image annotation (polygon, bounding box, etc.)
- 🤖 AI-powered object detection workflows
- 📊 Dataset organization with category/instance IDs

---

## Key Features

### 🎬 Video Mode

<details>
<summary><b>Video Playback & Navigation</b></summary>

- Multi-format support (MP4, AVI, MOV, MKV, WebM, etc.)
- Synchronized audio/video playback
- Variable playback speed (0.25x - 4x)
- Quick jump buttons (1s, 5s, 10s, 30s, 1min, 5min)
- Frame-by-frame navigation
- Adjustable preview quality for long videos

</details>

<details>
<summary><b>Video Clipping & Labeling</b></summary>

- Mark clip start/end with visual timeline
- Rich clip metadata:
  - **Label** (required) - with dropdown support
  - **Category ID** & **Instance ID** - for dataset organization
  - Detection/Recognition scores (0-5 scale)
  - Hazard flag, Scene, Description, Recognition
- Interactive timeline with draggable clip markers
- Right-click context menu for clip management
- Auto-save after each modification
- Frame extraction (first & last frame)
- Export to JSON or CSV

📖 [**Detailed Video Mode Guide →**](docs/VIDEO_MODE.md)

</details>

<details>
<summary><b>Object List Management</b></summary>

- Import JSON-based object lists for consistent labeling
- Dropdown selection with formatted display: `"chair [cat:30, inst:1]"`
- Auto-fill category/instance IDs based on selection
- Support for multiple instances of the same object
- Shared between Video and Image modes

📖 [**Object List Guide →**](docs/OBJECT_LIST_FEATURE.md) | [**Quick Start →**](docs/OBJECT_LIST_QUICKSTART.md)

</details>

### 🎤 AI Caption Extraction (Whisper)

<details>
<summary><b>Speech Recognition</b></summary>

- **OpenAI Whisper** integration (tiny → turbo models)
- Multi-language support with auto-detection
- Real-time caption display during playback
- Export to SRT/WebVTT subtitle formats
- Auto-load existing captions when opening videos
- Search captions and highlight on timeline

📖 [**Whisper Setup Guide →**](docs/WHISPER_SETUP.md)

</details>

### 🤖 LLM Caption Analysis

<details>
<summary><b>AI-Powered Analysis</b></summary>

- **Support for**: GPT-5, GPT-4o, Gemini, Claude
- Extract structured data from captions:
  - Object names, detection/recognition scores
  - Hazard flags, descriptions
- Smart chunking (20-segment chunks for optimal processing)
- Auto-fill video clips from analysis results
- Auto-save analysis to JSON
- Secure local API key storage
- Collapsible compact UI

📖 [**LLM Analysis Guide →**](docs/LLM_ANALYSIS.md) | [**Examples →**](docs/LLM_EXAMPLE.md)

</details>

### ⚡ Batch Processing

<details>
<summary><b>Multi-Video Automation</b></summary>

- Process multiple videos automatically
- **Modes**:
  - Caption Extraction Only
  - Caption + LLM Analysis (with auto-fill clips)
- Smart skip: auto-load existing captions
- Detailed real-time progress display:
  - Current video (e.g., "Video 5/15: experiment_005.mp4")
  - Current step (e.g., "Analyzing chunk 2/4...")
  - Detailed info (e.g., "Found 15 detections")
- Error handling: continue on failure

📖 [**Batch Process Guide →**](docs/BATCH_PROCESS_FEATURE.md)

</details>

### 🖼️ Image Mode

<details>
<summary><b>Image Annotation & Segmentation</b></summary>

- **Annotation Tools**:
  - Polygon, Rectangle, Circle, Line, Point
  - AI-assisted annotation (SAM/SAM2)
  - Edit/Move mode for shape modification
- **Label Management**:
  - Object list integration with dropdown selection
  - Category ID & Instance ID support
  - Group ID for organizing related shapes
  - Auto-fill IDs from object list
- **WST Mode** (Work with Saved Thumbnails):
  - Load pre-extracted frames
  - Auto-load current video's `frames/` folder
  - Label hints from video clips
- **Auto-Save**:
  - Save to image location automatically
  - Auto-save on image switch, mode switch, or app close
  - Keyboard shortcut: `Ctrl+S`
- **Export**: Labelme-compatible JSON format

📖 [**Image Mode Guide →**](docs/IMAGE_MODE.md) | [**SAM Setup →**](docs/SAM_SETUP.md)

</details>

### 📂 Output Organization

All outputs are organized in video-named folders:

```
video_name/
├── clips.json                 # Clip metadata (with category/instance IDs)
├── clips.csv                  # Legacy CSV format (auto-migrated)
├── frames/                    # Extracted frames
│   ├── clip1_start_0150.jpg
│   ├── clip1_start_0150.json  # Auto-saved annotations
│   └── ...
├── captions/
│   └── video_name.srt         # Whisper captions
├── annotations/               # Manual save annotations
│   └── frame_0150.json
└── llm_analysis/
    └── video_name_llm_detections.json  # LLM analysis results
```

---

## Installation

### Option 1: From Pre-built Release (Recommended)

Download the latest release from [Releases](https://github.com/yourusername/labelvid/releases):

```bash
# macOS
unzip LabelVid-v0.1.0-macOS-arm64-Full.zip
cd LabelVid-v0.1.0-macOS-arm64-Full
sudo xattr -rd com.apple.quarantine dist/LabelVid.app
open dist/LabelVid.app
```

The **Full Version** includes:
- ✅ FFmpeg bundled (no installation needed)
- ✅ Whisper ready to use
- ✅ LLM support (API key required)
- ✅ SAM/SAM2 models auto-download

### Option 2: From Source

```bash
# Clone repository
git clone https://github.com/yourusername/labelvid.git
cd labelvid

# Install dependencies
pip install -e .

# Install optional features
pip install -e ".[all]"  # All features (Whisper, LLM, SAM)
# Or individually:
pip install -e ".[whisper]"  # Whisper only
pip install -e ".[llm]"      # LLM only
pip install -e ".[ai]"       # SAM only
```

> **Note for Developers**: If you're building an executable with PyInstaller, use `opencv-python-headless` instead of `opencv-python` to avoid recursion errors during packaging. See [CV2_FIX_SUCCESS.md](CV2_FIX_SUCCESS.md) for details.

### System Requirements

**Required:**
- Python 3.8+
- FFmpeg (for audio extraction)
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/)

**Optional:**
- CUDA-compatible GPU (for faster Whisper/SAM inference)

📖 [**FFmpeg Troubleshooting →**](docs/FFMPEG_TROUBLESHOOTING.md)

---

## Quick Start

### Launch the App

```bash
# From release package
open dist/LabelVid.app  # macOS
./dist/LabelVid         # Linux
dist\LabelVid.exe       # Windows

# From source
labelvid                           # GUI only
labelvid /path/to/video.mp4       # Open video
labelvid /path/to/video/folder    # Load folder
python run.py                      # Development mode
```

### Basic Workflow

#### 1️⃣ Video Clipping

```
Open Video → Mark Start/End → Fill Clip Info → Extract Frames
```

<details>
<summary>Detailed Steps</summary>

1. **File → Open** or **Open Directory**
2. **File → Manage Object List** (optional, for consistent labeling)
3. Navigate to desired frame
4. Press `[` or click **Mark Start**
5. Navigate to end frame
6. Press `]` or click **Mark End**
7. Fill clip dialog:
   - Select label from dropdown (if object list loaded)
   - Category/Instance IDs auto-fill
   - Add scores, description (optional)
8. Click **Extract Frames** to export

</details>

#### 2️⃣ Caption Extraction & Analysis

```
Extract Captions → Analyze with LLM → Auto-fill Clips
```

<details>
<summary>Detailed Steps</summary>

1. Enable **"Captions (Whisper)"** checkbox
2. Select model and language
3. Click **Extract Captions**
4. Wait for processing (status bar shows progress)
5. Click **🤖 Analyze & Fill Clips**
6. Configure LLM (click ⚙️):
   - Select provider (OpenAI/Gemini/Claude)
   - Enter API key
   - Choose model
7. Click **Analyze** → clips auto-generated
8. Review and modify clips as needed

</details>

#### 3️⃣ Batch Processing

```
Load Videos → Select Mode → Monitor Progress → Review Results
```

<details>
<summary>Detailed Steps</summary>

1. **File → Open Directory** (select folder with multiple videos)
2. Click **⚡ Batch Process** button
3. Choose mode:
   - **Caption Extraction Only**
   - **Caption + LLM Analysis**
4. Monitor detailed progress for each video
5. Review summary of successful/failed videos

</details>

#### 4️⃣ Image Annotation

```
Switch to Image Mode → Create Shapes → Auto-Save
```

<details>
<summary>Detailed Steps</summary>

1. Click **Toggle Mode** or press `Ctrl+M`
2. Choose image source:
   - **Open Image File**: Single image
   - **WST (Work with Saved Thumbnails)**: Folder of images
   - **Auto-extract**: Extract frames automatically
3. Select annotation tool:
   - `P`: Polygon
   - `R`: Rectangle
   - `A`: AI Polygon (SAM)
4. Draw shape on image
5. Label dialog appears:
   - Select label from dropdown (if object list loaded)
   - Category/Instance IDs auto-fill
   - Add flags, description (optional)
6. Enable **"Auto-save to image location"** for quick workflow
7. Press `Ctrl+S` or click **💾 Save**

</details>

---

## Usage Guide

### Keyboard Shortcuts

| Shortcut | Action | Mode |
|----------|--------|------|
| **General** | | |
| `Ctrl+M` | Toggle Video/Image Mode | All |
| `Ctrl+O` | Open file | All |
| `Ctrl+D` | Open directory | All |
| `Ctrl+Q` | Quit | All |
| **Video Mode** | | |
| `Space` | Play/Pause | Video |
| `←` / `→` | Previous/Next frame | Video |
| `Shift+←/→` | Jump backward/forward | Video |
| `[` | Mark clip start | Video |
| `]` | Mark clip end | Video |
| `Delete` | Delete selected clip | Video |
| `1-6` | Quick jump (1s, 5s, 10s, 30s, 1min, 5min) | Video |
| **Image Mode** | | |
| `P` | Polygon mode | Image |
| `R` | Rectangle mode | Image |
| `A` | AI Polygon (SAM) | Image |
| `E` | Edit/Move mode | Image |
| `Ctrl+S` | Auto-save annotation | Image |
| `Ctrl+Shift+S` | Save with dialog | Image |
| `Enter`/`Space` | Finalize shape | Image |
| `Escape` | Cancel drawing | Image |
| `Delete` | Delete shape/point | Image |

### Common Tasks

<details>
<summary><b>How to use Object Lists?</b></summary>

1. Create JSON file:
```json
[
  {"category_id": 28, "instance_id": 0, "label_name": "red suitcase"},
  {"category_id": 30, "instance_id": 0, "label_name": "chair"},
  {"category_id": 30, "instance_id": 1, "label_name": "chair"}
]
```

2. Import: **File → Manage Object List → Import JSON**
3. Use in both Video and Image modes
4. Labels appear as dropdown with auto-fill IDs

📖 [**Full Object List Guide →**](docs/OBJECT_LIST_FEATURE.md)

</details>

<details>
<summary><b>How to configure LLM analysis?</b></summary>

1. Click **🤖 Analyze & Fill Clips** button
2. Click **⚙️** settings icon
3. Select provider:
   - **OpenAI**: GPT-5, GPT-5-mini, GPT-4o
   - **Gemini**: gemini-2.0-flash
   - **Claude**: claude-3.5-sonnet
4. Enter API key
5. Check **"Save API Key"** to remember
6. Click **Analyze**

📖 [**LLM Setup Guide →**](docs/LLM_ANALYSIS.md)

</details>

<details>
<summary><b>How to use AI-assisted annotation (SAM)?</b></summary>

1. Install: `pip install -e ".[ai]"`
2. Switch to Image Mode
3. Select **AI Polygon** tool (or press `A`)
4. Choose model: sam2:base (recommended)
5. Click to add positive points
6. Shift+Click for negative points
7. Press Enter/Space to finalize

📖 [**SAM Setup Guide →**](docs/SAM_SETUP.md)

</details>

<details>
<summary><b>How to extract frames from clips?</b></summary>

1. Mark clips in Video Mode
2. Click **Extract Frames** button
3. Frames saved to `<video_name>/frames/`
4. Each clip extracts first & last frame
5. Frame paths automatically saved to `clips.json`
6. Use in Image Mode (WST) for annotation

</details>

<details>
<summary><b>How does auto-save work in Image Mode?</b></summary>

- **Enable**: Check **"Auto-save to image location"**
- **Triggers**:
  - Switching images (Prev/Next)
  - Switching to Video Mode
  - Closing application
- **Location**: Same directory as image (e.g., `image.jpg` → `image.json`)
- **Manual save**: `Ctrl+Shift+S` for custom location

📖 [**Auto-Save Guide →**](docs/AUTO_SAVE_ANNOTATION_FEATURE.md)

</details>

---

## Documentation

### Feature Guides

- [📖 Video Mode Detailed Guide](docs/VIDEO_MODE.md)
- [📖 Image Mode Detailed Guide](docs/IMAGE_MODE.md)
- [📖 Object List Management](docs/OBJECT_LIST_FEATURE.md)
- [📖 LLM Caption Analysis](docs/LLM_ANALYSIS.md)
- [📖 Batch Processing](docs/BATCH_PROCESS_FEATURE.md)
- [📖 Auto-Save Annotation](docs/AUTO_SAVE_ANNOTATION_FEATURE.md)

### Setup & Configuration

- [⚙️ FFmpeg Installation & Troubleshooting](docs/FFMPEG_TROUBLESHOOTING.md)
- [⚙️ Whisper Setup](docs/WHISPER_SETUP.md)
- [⚙️ SAM/SAM2 Setup](docs/SAM_SETUP.md)
- [⚙️ LLM Configuration](docs/LLM_ANALYSIS.md)

### Development

- [🔧 Building Executable](docs/QUICK_RELEASE.md)
- [🔧 Full Version Build (with FFmpeg)](docs/FULL_VERSION_BUILD_GUIDE.md)
- [📋 Release Notes v0.1.0](docs/RELEASE_NOTES_v0.1.0.md)
- [🧪 Testing Guide](docs/TESTING.md)

---

## Building Executable

### Prerequisites

For building executables, **use `opencv-python-headless` instead of `opencv-python`**:

```bash
pip uninstall opencv-python
pip install opencv-python-headless==4.10.0.84
```

This avoids PyInstaller recursion errors during packaging. See [CV2_FIX_SUCCESS.md](CV2_FIX_SUCCESS.md) for details.

### Build Commands

```bash
# Quick build (recommended)
./build_release.sh

# Or manually
python build_exe.py --clean
python create_release.py

# Build Full Version (with bundled FFmpeg)
./build_full_release.sh
```

**Output:**
- `releases/LabelVid-v0.1.0-<platform>-<arch>.zip` (Standard version)
- `releases/LabelVid-v0.1.0-<platform>-<arch>-Full.zip` (Full version)

📖 [**Detailed Build Guide →**](docs/QUICK_RELEASE.md)

---

## License

This project is licensed under the **GPL-3.0 License**. See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## Acknowledgments

- [Labelme](https://github.com/wkentaro/labelme) - Image annotation inspiration
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [Segment Anything (SAM)](https://github.com/facebookresearch/segment-anything) - AI segmentation
- [OSAM](https://github.com/jovialniyo93/osam) - SAM integration wrapper

---

<div align="center">

**Made with ❤️ for AI/ML dataset preparation**

[⬆ Back to Top](#labelvid---video--image-annotation-tool)

</div>
