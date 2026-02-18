# Auto-Save Annotation Feature

## ✅ 新功能概述

在 Image Mode 下添加了**自动保存 annotation** 的功能，annotation 可以直接保存到当前图片所在的位置，无需弹出文件对话框。

## 📝 功能说明

### 1. 两种保存模式

#### 模式 1: Auto-Save（自动保存）✨
- **快捷键**: `Ctrl+S`
- **行为**: 直接保存到当前图片所在的位置
- **文件名**: 与图片同名（如 `chair_start_399.json`）
- **位置**: 与图片相同的目录
- **提示**: 状态栏显示 "Auto-saved annotation to ..."

#### 模式 2: Manual Save（手动保存）
- **快捷键**: `Ctrl+Shift+S`
- **行为**: 弹出文件对话框，用户选择保存位置
- **默认位置**: `<video_name>/annotations/` 文件夹
- **提示**: 状态栏显示 "Saved annotation to ..."

### 2. UI 控件

#### 复选框: "Auto-save to image location"
- **位置**: Image Mode 控制面板
- **默认状态**: ✅ 选中（启用自动保存）
- **功能**: 控制 "💾 Save" 按钮的行为

#### 按钮: "💾 Save"
- **行为**: 根据复选框状态决定使用哪种保存模式
- **Tooltip**: "Save annotation (Ctrl+S for auto-save, Ctrl+Shift+S for dialog)"

### 3. 菜单项

#### File > Auto Save Annotation
- **快捷键**: `Ctrl+S`
- **功能**: 强制使用自动保存模式

#### File > Save Annotation
- **快捷键**: `Ctrl+Shift+S`
- **功能**: 强制使用手动保存模式（弹出对话框）

#### Annotation > Auto Save Annotation
- **快捷键**: `Ctrl+S`
- **功能**: 强制使用自动保存模式

#### Annotation > Save Annotation
- **快捷键**: `Ctrl+Shift+S`
- **功能**: 强制使用手动保存模式

## 🎯 使用场景

### 场景 1: WST Mode 快速标注

**工作流**:
1. 切换到 Image Mode，选择 WST
2. 打开包含提取帧的文件夹（如 `frames/`）
3. 选择一张图片（如 `chair_start_399.jpg`）
4. 创建 annotation（polygon, rectangle, etc.）
5. 按 `Ctrl+S` 或点击 "💾 Save" 按钮
6. ✅ Annotation 自动保存为 `chair_start_399.json`（与图片同目录）

**优势**:
- 🚀 快速：无需每次选择保存位置
- 🎯 精准：annotation 和图片始终在同一位置
- 📂 整洁：所有相关文件都在一起

### 场景 2: 需要自定义保存位置

**工作流**:
1. 取消勾选 "Auto-save to image location" 复选框
2. 或直接按 `Ctrl+Shift+S`
3. 在文件对话框中选择保存位置
4. ✅ Annotation 保存到指定位置

**优势**:
- 🎛️ 灵活：可以保存到任意位置
- 📁 组织：可以集中保存到 `annotations/` 文件夹

### 场景 3: 单张图片标注

**工作流**:
1. Image Mode > 选择 "Open Image File"
2. 打开一张图片
3. 创建 annotation
4. 按 `Ctrl+S`
5. ✅ Annotation 保存到图片所在目录

## 📂 保存位置对比

### Auto-Save Mode

| 图片位置 | Annotation 保存位置 |
|---------|-------------------|
| `/path/to/frames/chair_start_399.jpg` | `/path/to/frames/chair_start_399.json` |
| `/path/to/images/photo.png` | `/path/to/images/photo.json` |
| `C:\Users\Name\Pictures\test.jpg` | `C:\Users\Name\Pictures\test.json` |

**特点**:
- ✅ Annotation 和图片**在同一目录**
- ✅ 文件名完全相同（除了扩展名）
- ✅ 如果图片已存在，不会重复保存图片

### Manual Save Mode

| 默认保存位置 |
|------------|
| `<video_name>/annotations/chair_start_399.json` |

**特点**:
- ✅ 所有 annotation 集中管理
- ✅ 用户可以自定义保存位置
- ✅ 会同时保存图片副本到选择的位置

## 🔧 技术实现

### 代码修改

#### 1. `_save_annotation()` 方法

添加了 `auto_save` 参数：

```python
def _save_annotation(self, auto_save: bool = False) -> None:
    """Save annotation to labelme JSON format.
    
    Args:
        auto_save: If True, save directly to current image location.
                  If False, show file dialog.
    """
```

**Auto-save 逻辑**:
- 如果在 WST 模式且有当前图片：保存到图片所在目录
- 如果在 Video 模式：保存到视频所在目录
- 文件名：与图片同名（`.json` 扩展名）
- 不重复保存图片（如果图片已存在）

**Manual save 逻辑**:
- 弹出文件对话框
- 默认位置：`<video_name>/annotations/`
- 同时保存图片副本

#### 2. 新增 UI 控件

```python
# Auto-save checkbox
self.autoSaveCheckbox = QtWidgets.QCheckBox("Auto-save to image location")
self.autoSaveCheckbox.setChecked(True)  # Default to auto-save

# Save button with new handler
self.saveAnnotationBtn.clicked.connect(self._on_save_annotation_clicked)
```

#### 3. 新增按钮处理方法

```python
def _on_save_annotation_clicked(self) -> None:
    """Handle save annotation button click, respecting auto-save checkbox."""
    auto_save = self.autoSaveCheckbox.isChecked()
    self._save_annotation(auto_save=auto_save)
```

#### 4. 新增 Actions

```python
# Auto-save action
auto_save_annotation = action(
    self.tr("Auto Save Annotation"),
    lambda: self._save_annotation(auto_save=True),
    "Ctrl+S",
    tip=self.tr("Auto save annotation to current image location"),
)

# Manual save action
save_annotation = action(
    self.tr("Save Annotation"),
    self._save_annotation,
    "Ctrl+Shift+S",
    tip=self.tr("Save annotation to JSON file"),
)
```

## ⌨️ 快捷键总结

| 快捷键 | 功能 | 行为 |
|-------|------|------|
| `Ctrl+S` | Auto Save | 直接保存到图片位置 |
| `Ctrl+Shift+S` | Manual Save | 弹出文件对话框 |

## 💡 使用建议

### 推荐使用 Auto-Save

✅ **适合场景**:
- 批量标注多张图片
- WST 模式下标注提取的帧
- 需要快速保存
- Annotation 和图片需要在同一位置

### 推荐使用 Manual Save

✅ **适合场景**:
- 需要集中管理所有 annotation
- 需要保存到特定位置
- 需要自定义文件名
- 需要保存图片副本到不同位置

### 最佳实践

1. **WST Mode 快速标注**: 使用 Auto-Save（默认设置）
2. **需要组织结构**: 取消 Auto-Save，使用 `annotations/` 文件夹
3. **混合使用**: 
   - 日常标注：`Ctrl+S` (Auto-Save)
   - 特殊情况：`Ctrl+Shift+S` (Manual Save)

## 🧪 测试

### 测试 1: Auto-Save 功能

1. 打开 Image Mode (WST)
2. 选择一张图片（如 `frames/chair_start_399.jpg`）
3. 创建一个 polygon
4. 确认 "Auto-save to image location" 复选框已选中
5. 点击 "💾 Save" 按钮
6. **验证**: 
   - `frames/chair_start_399.json` 文件存在
   - 文件内容正确
   - 状态栏显示 "Auto-saved annotation to ..."

### 测试 2: Manual Save 功能

1. 取消勾选 "Auto-save to image location"
2. 点击 "💾 Save" 按钮
3. **验证**: 文件对话框弹出
4. 选择保存位置并保存
5. **验证**: Annotation 保存到指定位置

### 测试 3: 快捷键

1. 按 `Ctrl+S`
2. **验证**: 使用 Auto-Save 模式
3. 按 `Ctrl+Shift+S`
4. **验证**: 弹出文件对话框（Manual Save 模式）

### 测试 4: 覆盖保存

1. 创建 annotation 并 Auto-Save
2. 修改 annotation
3. 再次 `Ctrl+S`
4. **验证**: 
   - 同一个 JSON 文件被更新
   - 图片没有重复保存

## 🎨 UI 展示

### Image Mode 控制面板

```
┌────────────────────────────────────────┐
│  [✓] Auto-save to image location       │
│  [💾 Save]                              │
└────────────────────────────────────────┘
```

### 状态栏提示

**Auto-Save**:
```
Auto-saved annotation to /path/to/frames/chair_start_399.json
```

**Manual Save**:
```
Saved annotation to /path/to/video/annotations/chair_start_399.json
```

## 🔮 未来改进

### v0.2.0
- [ ] 添加自动保存间隔（如每 5 分钟自动保存）
- [ ] 添加 "另存为" 功能
- [ ] 记住用户的保存偏好（QSettings）

### v0.3.0
- [ ] 支持批量保存多个 annotation
- [ ] 支持导出为其他格式（COCO, YOLO）
- [ ] 云端同步支持

## 📊 总结

| 特性 | Auto-Save | Manual Save |
|------|-----------|-------------|
| **快捷键** | `Ctrl+S` | `Ctrl+Shift+S` |
| **速度** | 🚀 快速 | 🐢 需要选择 |
| **位置** | 图片所在目录 | 用户指定 |
| **文件名** | 自动（与图片同名） | 用户指定 |
| **适用场景** | 批量快速标注 | 集中管理 |
| **默认状态** | ✅ 启用 | ❌ 需要取消复选框 |

---

**总结**: Auto-Save 功能显著提升了 Image Mode 下的标注效率，让用户可以专注于标注本身，而不是文件管理！
