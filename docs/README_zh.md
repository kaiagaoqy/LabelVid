# LabelVid - 视频剪辑与图像标注工具

一款专业的视频剪辑和图像标注工具，专为与 [Labelme](https://github.com/wkentaro/labelme) 配合使用而设计。

[English](../README.md) | [中文文档](README_zh.md)

## 功能特性

### 视频模式（视频剪辑）
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

### 字幕与语音识别
- **AI 字幕提取**：使用 OpenAI Whisper 进行自动语音识别
- **多种模型**：支持 tiny、base、small、medium、large、turbo 等模型
- **多语言支持**：自动检测或手动选择转录语言
- **实时显示**：视频播放时实时显示字幕
- **自动加载字幕**：打开视频时自动加载已有的 SRT 文件
- **字幕导出**：导出为 SRT 或 WebVTT 字幕格式

### 图像模式（图像标注）
- **多边形标注**：绘制多边形标注物体
- **矩形/边界框**：绘制矩形用于目标检测
- **圆形、线条、点**：多种形状类型满足不同标注需求
- **AI 辅助标注 (SAM)**：使用 SAM/SAM2 自动生成多边形
- **编辑模式**：移动、调整大小、修改形状
- **形状管理**：右键菜单支持编辑标签、删除形状
- **点编辑**：可删除多边形的单个顶点
- **Labelme 导出**：导出为 Labelme 兼容的 JSON 格式
- **WST 模式**：加载已提取的帧图像进行标注

### 输出文件组织
所有输出文件按视频名称组织：
```
视频名称/
├── clips.csv          # 片段信息
├── frames/            # 提取的帧图像
├── captions/          # SRT/VTT 字幕文件
└── annotations/       # Labelme JSON 标注文件
```

## 安装方法

### 从源码安装（开发模式）
```bash
cd labelvid
pip install -e .
```

### 可选依赖

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

### 系统要求

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

## 快速开始

无需安装即可快速测试：
```bash
python run.py
python run.py /path/to/video.mp4
python run.py /path/to/video/folder
```

## 使用方法

### 启动应用
```bash
labelvid
labelvid /path/to/video.mp4
labelvid /path/to/video/folder
```

### 视频模式工作流程
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

### 图像模式工作流程
1. **切换模式**：点击模式切换按钮或按 `Ctrl+M`
2. **选择图像来源**：当前帧、WST 文件夹或自动提取
3. **绘制形状**：选择工具并在图像上点击绘制
4. **标注形状**：完成绘制后输入标签
5. **编辑形状**：使用编辑/移动模式（`E`）修改形状
6. **保存**：点击"保存标注"导出 Labelme JSON 格式

## 快捷键

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

## AI 辅助标注 (SAM)

1. 安装：`pip install -e ".[ai]"`
2. 切换到图像模式
3. 选择"AI 多边形"并选择 SAM 模型版本
4. 点击添加正向点，Shift+点击添加负向点
5. 按 Enter/空格 或 Ctrl+点击 完成标注

**可用 SAM 模型：**
- `sam2:tiny/small/base/large` - SAM2 变体（推荐）
- `sam:vit_h/l/b` - 原始 SAM 变体

## Whisper 字幕提取

1. 安装：`pip install -e ".[whisper]"`
2. 在视频模式下加载视频
3. 勾选"Captions (Whisper)"复选框
4. 选择模型和语言
5. 点击"Extract Captions"提取字幕
6. 使用"Export SRT"导出 SRT/WebVTT 格式

**可用模型：** tiny, tiny.en, base, base.en, small, small.en, medium, medium.en, large, large-v2, large-v3, turbo

## 构建可执行文件

创建独立的可执行程序：

```bash
# 使用 conda 环境（推荐）
conda activate labelvid
./build_release.sh

# 或手动构建
python build_exe.py
python create_release.py
```

详细的发布说明请查看 [QUICK_RELEASE.md](QUICK_RELEASE.md)。

## 许可证

GPL-3.0
