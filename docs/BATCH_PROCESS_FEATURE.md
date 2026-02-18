# Batch Process Feature

## ✨ 新功能 (New Feature)

添加了**批量处理**功能，可以一键处理多个视频的 caption 提取和 LLM 分析。

## 📊 功能说明 (Features)

### 1. 批量 Caption 提取
- 自动提取所有加载视频的 captions
- 使用 Whisper 进行语音识别
- 自动保存为 SRT 文件

### 2. 批量 Caption + LLM 分析
- 提取 captions
- 使用 LLM 分析 captions
- 自动填充 clips
- 自动保存 JSON 结果

### 3. 智能跳过
- 如果视频已有 captions，自动加载并跳过提取
- 直接进行 LLM 分析

## 🎯 使用场景 (Use Cases)

### 场景 1: 批量提取字幕
```
1. 打开文件夹，加载多个视频
2. 点击 "⚡ Batch Process" 或 菜单 "Batch Process > Caption Extraction Only"
3. 等待处理完成
4. 所有视频的 captions 自动保存
```

### 场景 2: 批量 LLM 分析
```
1. 打开文件夹，加载多个视频
2. 配置 LLM 设置（点击 ⚙️）
3. 点击 "⚡ Batch Process" 选择 "Caption + LLM Analysis"
4. 等待处理完成
5. 所有视频的 captions、LLM 结果、clips 自动保存
```

### 场景 3: 已有 Captions 的视频
```
1. 打开文件夹（视频已有 .srt 文件）
2. 点击 "⚡ Batch Process" 选择 "Caption + LLM Analysis"
3. 自动加载现有 captions
4. 直接进行 LLM 分析
5. 节省 caption 提取时间
```

## 🎨 UI 设计 (UI Design)

### 工具栏按钮
```
[📂 Open] [📁 Open Dir] [⏮] [⏭] [📤 Extract] | [⚡ Batch Process] | [🎬 Video Mode]
```

**位置**: Video Mode 按钮前

### 菜单栏
```
File | Edit | View | Batch Process | Mode | Annotation | Help
                     ↑ 新增菜单
```

**菜单项**:
- 📝 Caption Extraction Only
- 🤖 Caption + LLM Analysis

### 批量处理对话框
```
┌─────────────────────────────────────┐
│ Batch Process                       │
├─────────────────────────────────────┤
│ Process 15 loaded videos:           │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📝 Caption Extraction Only      │ │
│ │ Extract captions using Whisper  │ │
│ │ and save to SRT                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🤖 Caption + LLM Analysis       │ │
│ │ Extract captions and analyze    │ │
│ │ with LLM                        │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Cancel                          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 进度对话框
```
┌─────────────────────────────────────┐
│ Batch Process                       │
├─────────────────────────────────────┤
│ Processing 5/15: video_003.mp4      │
│                                     │
│ [████████░░░░░░░░░░░░] 33%         │
│                                     │
│              [Cancel]               │
└─────────────────────────────────────┘
```

### 完成对话框
```
┌─────────────────────────────────────┐
│ Batch Process Complete              │
├─────────────────────────────────────┤
│ Batch processing complete!          │
│                                     │
│ Successfully processed: 14/15       │
│                                     │
│ Failed videos:                      │
│   - video_007.mp4: No audio stream  │
│                                     │
│              [OK]                   │
└─────────────────────────────────────┘
```

## 🔧 技术实现 (Implementation)

### 菜单和工具栏
```python
# 菜单
self.menus = types.SimpleNamespace(
    file=...,
    edit=...,
    view=...,
    batch=self.menuBar().addMenu(self.tr("&Batch Process")),  # ← 新增
    mode=...,
    ...
)

# 工具栏
self.batchProcessBtn = QtWidgets.QPushButton("⚡ Batch Process")
self.batchProcessBtn.clicked.connect(self._show_batch_process_dialog)
toolbar.addWidget(self.batchProcessBtn)
```

### Actions
```python
batch_caption_only = action(
    self.tr("📝 Caption Extraction Only"),
    lambda: self._batch_process(llm_analyze=False),
    tip=self.tr("Batch extract captions for all loaded videos"),
)

batch_caption_and_llm = action(
    self.tr("🤖 Caption + LLM Analysis"),
    lambda: self._batch_process(llm_analyze=True),
    tip=self.tr("Batch extract captions and analyze with LLM"),
)
```

### 批量处理逻辑
```python
def _batch_process(self, llm_analyze: bool = False) -> None:
    """Batch process all loaded videos."""
    
    # 1. 检查前提条件
    if not self._video_list:
        # 提示用户加载视频
        return
    
    if not self._whisper_transcriber:
        # 提示安装 Whisper
        return
    
    if llm_analyze:
        # 检查 LLM 可用性
        # 获取 LLM 设置
        pass
    
    # 2. 创建进度对话框
    progress = QtWidgets.QProgressDialog(...)
    
    # 3. 遍历所有视频
    for i, video_path in enumerate(self._video_list):
        if progress.wasCanceled():
            break
        
        # 加载视频
        self._load_video(video_path)
        
        # 检查是否已有 captions
        if not self._caption_segments:
            # 提取 captions
            self._extract_captions()
        
        # LLM 分析（如果需要）
        if llm_analyze and self._caption_segments:
            # 创建 LLM client
            # 分析 captions
            # 保存 JSON
            # 填充 clips
            pass
    
    # 4. 显示结果摘要
    QMessageBox.information(...)
```

### 智能跳过逻辑
```python
# 在 _load_video 中已有的逻辑
def _load_video(self, video_path):
    # ... 加载视频 ...
    
    # 自动加载 captions
    self._auto_load_captions()  # ← 已有功能
    
    # 如果 self._caption_segments 有内容，说明已加载
```

## 📊 处理流程 (Processing Flow)

### Caption Extraction Only
```
1. 遍历视频列表
   ↓
2. 加载视频
   ↓
3. 检查是否已有 captions
   ├─ 有 → 跳过提取
   └─ 无 → 提取 captions
   ↓
4. 保存 SRT 文件
   ↓
5. 下一个视频
```

### Caption + LLM Analysis
```
1. 遍历视频列表
   ↓
2. 加载视频
   ↓
3. 检查是否已有 captions
   ├─ 有 → 加载现有 captions
   └─ 无 → 提取 captions
   ↓
4. 保存 SRT 文件
   ↓
5. LLM 分析 captions
   ↓
6. 保存 JSON 结果
   ↓
7. 填充 clips
   ↓
8. 保存 clips.csv
   ↓
9. 下一个视频
```

## 📁 输出结构 (Output Structure)

### Caption Extraction Only
```
video_001/
├── captions/
│   └── video_001.srt

video_002/
├── captions/
│   └── video_002.srt

...
```

### Caption + LLM Analysis
```
video_001/
├── clips.csv
├── captions/
│   └── video_001.srt
└── llm_analysis/
    └── video_001_llm_detections.json

video_002/
├── clips.csv
├── captions/
│   └── video_002.srt
└── llm_analysis/
    └── video_002_llm_detections.json

...
```

## ⚡ 性能优化 (Performance)

### 1. 智能跳过
- ✅ 已有 captions 的视频不重复提取
- ✅ 节省 Whisper 处理时间

### 2. 进度显示
- ✅ 实时显示当前处理的视频
- ✅ 显示总体进度百分比
- ✅ 支持取消操作

### 3. 错误处理
- ✅ 单个视频失败不影响其他视频
- ✅ 记录所有失败的视频和原因
- ✅ 最后显示完整的处理摘要

## 🎯 用户体验 (UX)

### 优势
1. **一键处理**: 无需手动切换视频
2. **智能跳过**: 已有 captions 自动加载
3. **进度可视**: 清晰的进度显示
4. **错误容忍**: 单个失败不影响整体
5. **结果摘要**: 完整的处理报告

### 典型工作流
```
研究人员有 50 个实验视频需要分析:

1. 打开文件夹 (50 个视频)
2. 配置 LLM 设置 (一次性)
3. 点击 "⚡ Batch Process"
4. 选择 "Caption + LLM Analysis"
5. 等待 30-60 分钟
6. 完成！所有视频都有:
   - Captions (SRT)
   - LLM 分析结果 (JSON)
   - 自动标注的 Clips (CSV)
```

## 📝 代码变更总结 (Code Changes)

**`app.py`**:
- ✅ 添加 Batch Process 菜单
- ✅ 添加工具栏按钮
- ✅ 添加 batch process actions
- ✅ 实现 `_show_batch_process_dialog()`
- ✅ 实现 `_batch_process(llm_analyze)`
- ✅ 智能跳过已有 captions
- ✅ 错误处理和进度显示

**影响的功能**:
- ✅ 视频加载和切换
- ✅ Caption 提取
- ✅ LLM 分析
- ✅ Clip 管理

**不受影响的功能**:
- ✅ 单个视频的手动处理
- ✅ 图像标注模式
- ✅ 其他所有功能

## ✅ 测试建议 (Testing)

### 测试场景

1. **小批量测试** (3-5 个视频)
   - Caption Only
   - Caption + LLM

2. **混合测试** (部分有 captions，部分没有)
   - 验证智能跳过

3. **错误测试**
   - 无音频的视频
   - 损坏的视频文件

4. **取消测试**
   - 中途取消处理

5. **大批量测试** (20+ 视频)
   - 性能和稳定性

## 🎉 总结

**主要功能**:
- 🎯 批量 Caption 提取
- 🤖 批量 LLM 分析
- 🔍 智能跳过已有 captions
- 📊 详细的进度和结果报告

**用户价值**:
- ⏱️ 节省大量手动操作时间
- 🎯 一键处理多个视频
- 📈 提高研究效率
- ✅ 可靠的批量处理

现在可以批量处理大量视频了！🚀
