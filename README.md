# LabelVid - Video Clipping & Image Annotation Tool

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

A professional video clipping and image annotation tool designed to work with [Labelme](https://github.com/wkentaro/labelme) for video annotation workflows.

### Features

#### Video Mode (Video Clipping)
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

#### Caption & Speech Recognition
- **AI Caption Extraction**: Use OpenAI Whisper for automatic speech recognition
- **Multiple Models**: Support for tiny, base, small, medium, large, turbo models
- **Multi-language**: Auto-detect or manually select transcription language
- **Real-time Display**: Display captions in real-time during video playback
- **Auto-load Captions**: Automatically load existing SRT files when opening videos
- **Caption Export**: Export captions to SRT or WebVTT subtitle format

#### Image Mode (Image Annotation)
- **Polygon Annotation**: Draw polygons around objects
- **Rectangle/Bounding Box**: Draw rectangles for object detection
- **Circle, Line, Point**: Additional shape types for various annotation needs
- **AI-Assisted Annotation (SAM)**: Use SAM/SAM2 for automatic polygon generation
- **Edit Mode**: Move, resize, and modify shapes
- **Shape Management**: Edit labels, delete shapes via right-click context menu
- **Point Editing**: Remove individual points from polygons
- **Labelme Export**: Export annotations in Labelme-compatible JSON format
- **WST Mode**: Work with Saved Thumbnails - load pre-extracted frames for annotation

#### Output Organization
All outputs are organized in a video-named folder:
```
video_name/
├── clips.csv          # Clip information
├── frames/            # Extracted frames
├── captions/          # SRT/VTT subtitle files
└── annotations/       # Labelme JSON annotations
```

### Installation

#### From Source (Development)
```bash
cd labelvid
pip install -e .
```

#### Optional Dependencies

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

#### System Requirements

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

### Quick Start

For quick testing without installation:
```bash
python run.py
python run.py /path/to/video.mp4
python run.py /path/to/video/folder
```

### Usage

#### Launch the Application
```bash
labelvid
labelvid /path/to/video.mp4
labelvid /path/to/video/folder
```

#### Video Mode Workflow
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

#### Image Mode Workflow
1. **Switch Mode**: Click the mode toggle button or press `Ctrl+M`
2. **Select Image Source**: Current frame, WST folder, or auto-extract
3. **Draw Shapes**: Choose tool and click on the image
4. **Label Shapes**: Enter a label when prompted
5. **Edit Shapes**: Use Edit/Move mode (`E`) to modify shapes
6. **Save**: Click "Save Annotation" for Labelme JSON format

### Keyboard Shortcuts

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

### AI-Assisted Annotation (SAM)

1. Install: `pip install -e ".[ai]"`
2. Switch to Image Mode
3. Select "AI Polygon" and choose SAM model version
4. Click to add positive points, Shift+Click for negative points
5. Press Enter/Space or Ctrl+Click to finalize

**Available SAM Models:**
- `sam2:tiny/small/base/large` - SAM2 variants (recommended)
- `sam:vit_h/l/b` - Original SAM variants

### Whisper Caption Extraction

1. Install: `pip install -e ".[whisper]"`
2. Load a video in Video Mode
3. Enable "Captions (Whisper)" checkbox
4. Select model and language
5. Click "Extract Captions"
6. Export to SRT/WebVTT using "Export SRT"

**Available Models:** tiny, tiny.en, base, base.en, small, small.en, medium, medium.en, large, large-v2, large-v3, turbo

### License

GPL-3.0

---

<a name="中文"></a>
## 中文

一款专业的视频剪辑和图像标注工具，专为与 [Labelme](https://github.com/wkentaro/labelme) 配合使用而设计。

### 功能特性

#### 视频模式（视频剪辑）
- **视频加载**：打开视频文件或扫描文件夹（支持 MP4、AVI、MOV、MKV、WebM 等格式）
- **视频播放**：播放/暂停、拖动进度条、调整播放速度（0.25x - 4x）
- **音频播放**：同步音频播放，支持音量控制
- **片段标记**：标记视频片段的起始和结束帧，并添加自定义标签
- **可视化时间轴**：交互式时间轴显示所有片段，支持拖拽调整
- **帧提取**：导出每个片段的首尾帧图像
- **CSV 导出**：生成包含片段信息的表格（标签、起始帧、结束帧）
- **自动保存**：每次修改后自动保存片段信息
- **自动加载**：打开视频时自动加载已有的 clips.csv 和字幕文件
- **快速跳转**：支持 1秒、5秒、10秒、30秒、1分钟、5分钟 的快速跳转
- **预览质量**：可调节预览质量，确保长视频流畅播放
- **片段管理**：右键菜单支持编辑、删除、跳转到起始/结束帧

#### 字幕与语音识别
- **AI 字幕提取**：使用 OpenAI Whisper 进行自动语音识别
- **多种模型**：支持 tiny、base、small、medium、large、turbo 等模型
- **多语言支持**：自动检测或手动选择转录语言
- **实时显示**：视频播放时实时显示字幕
- **自动加载字幕**：打开视频时自动加载已有的 SRT 文件
- **字幕导出**：导出为 SRT 或 WebVTT 字幕格式

#### 图像模式（图像标注）
- **多边形标注**：绘制多边形标注物体
- **矩形/边界框**：绘制矩形用于目标检测
- **圆形、线条、点**：多种形状类型满足不同标注需求
- **AI 辅助标注 (SAM)**：使用 SAM/SAM2 自动生成多边形
- **编辑模式**：移动、调整大小、修改形状
- **形状管理**：右键菜单支持编辑标签、删除形状
- **点编辑**：可删除多边形的单个顶点
- **Labelme 导出**：导出为 Labelme 兼容的 JSON 格式
- **WST 模式**：加载已提取的帧图像进行标注

#### 输出文件组织
所有输出文件按视频名称组织：
```
视频名称/
├── clips.csv          # 片段信息
├── frames/            # 提取的帧图像
├── captions/          # SRT/VTT 字幕文件
└── annotations/       # Labelme JSON 标注文件
```

### 安装方法

#### 从源码安装（开发模式）
```bash
cd labelvid
pip install -e .
```

#### 可选依赖

安装 AI 辅助标注（SAM 支持）：
```bash
pip install -e ".[ai]"
```

安装 Whisper 字幕提取：
```bash
pip install -e ".[whisper]"
```

安装所有功能：
```bash
pip install -e ".[all]"
```

#### 系统要求

**FFmpeg** 是音频提取和 Whisper 所必需的：
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (使用 Chocolatey)
choco install ffmpeg

# Windows (使用 Scoop)
scoop install ffmpeg
```

### 快速开始

无需安装即可快速测试：
```bash
python run.py
python run.py /path/to/video.mp4
python run.py /path/to/video/folder
```

### 使用方法

#### 启动应用
```bash
labelvid
labelvid /path/to/video.mp4
labelvid /path/to/video/folder
```

#### 视频模式工作流程
1. **打开视频**：使用 文件 > 打开 选择视频文件
2. **导航**：使用滑块、播放控件或快速跳转按钮
3. **标记片段**：
   - 点击"标记起点"（或按 `[`）标记起始位置
   - 点击"标记终点"（或按 `]`）标记结束位置
   - 输入片段标签名称
4. **管理片段**：
   - 右键点击片段可编辑、删除或跳转
   - 拖动时间轴上的标记可调整片段边界
5. **导出**：点击"提取帧"导出图像和 CSV

#### 图像模式工作流程
1. **切换模式**：点击模式切换按钮或按 `Ctrl+M`
2. **选择图像来源**：当前帧、WST 文件夹或自动提取
3. **绘制形状**：选择工具并在图像上点击绘制
4. **标注形状**：完成绘制后输入标签
5. **编辑形状**：使用编辑/移动模式（`E`）修改形状
6. **保存**：点击"保存标注"导出 Labelme JSON 格式

### 快捷键

| 按键 | 功能 |
|-----|--------|
| **通用** | |
| Ctrl+M | 切换视频/图像模式 |
| Ctrl+O | 打开文件 |
| Ctrl+D | 打开目录 |
| Ctrl+Q | 退出 |
| **视频模式** | |
| 空格 | 播放/暂停 |
| 左/右方向键 | 上一帧/下一帧 |
| Shift+左/右 | 向前/向后跳转 |
| `[` | 标记片段起点 |
| `]` | 标记片段终点 |
| Delete | 删除选中的片段 |
| 1-6 | 快速跳转（1秒、5秒、10秒、30秒、1分钟、5分钟）|
| **图像模式** | |
| P | 多边形模式 |
| R | 矩形模式 |
| A | AI 多边形（SAM）模式 |
| E | 编辑/移动模式 |
| Ctrl+Shift+S | 保存标注 |
| Escape | 取消当前绘制 |
| Enter/空格 | 完成形状 |
| Delete | 删除选中的形状/点 |

### AI 辅助标注 (SAM)

1. 安装：`pip install -e ".[ai]"`
2. 切换到图像模式
3. 选择"AI 多边形"并选择 SAM 模型版本
4. 点击添加正向点，Shift+点击添加负向点
5. 按 Enter/空格 或 Ctrl+点击 完成标注

**可用 SAM 模型：**
- `sam2:tiny/small/base/large` - SAM2 变体（推荐）
- `sam:vit_h/l/b` - 原始 SAM 变体

### Whisper 字幕提取

1. 安装：`pip install -e ".[whisper]"`
2. 在视频模式下加载视频
3. 勾选"Captions (Whisper)"复选框
4. 选择模型和语言
5. 点击"Extract Captions"提取字幕
6. 使用"Export SRT"导出 SRT/WebVTT 格式

**可用模型：** tiny, tiny.en, base, base.en, small, small.en, medium, medium.en, large, large-v2, large-v3, turbo

### 许可证

GPL-3.0
