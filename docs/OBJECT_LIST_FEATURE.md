# Object List Feature - Label Dropdown with Category & Instance IDs

## ✨ 新功能 (New Feature)

添加了**对象列表管理**功能，允许用户：
1. 导入包含对象定义的 JSON 文件
2. 从下拉列表选择标签（而不是手动输入）
3. 自动填充 Category ID 和 Instance ID
4. LLM 自动填充时默认 ID 为 (0, 0)

## 📊 数据结构 (Data Structure)

### VideoClip 新增字段

```python
@dataclass
class VideoClip:
    # ... 原有字段 ...
    category_id: int = 0  # Category ID from object list
    instance_id: int = 0  # Instance ID from object list
```

### Object List JSON 格式

```json
[
  {
    "category_id": 1,
    "instance_id": 1,
    "label_name": "backpack"
  },
  {
    "category_id": 1,
    "instance_id": 2,
    "label_name": "bag"
  },
  {
    "category_id": 2,
    "instance_id": 1,
    "label_name": "person"
  }
]
```

**字段说明**:
- `category_id`: 类别 ID（整数）
- `instance_id`: 实例 ID（整数）
- `label_name`: 标签名称（字符串）

## 🎨 UI 更新 (UI Updates)

### 1. Object List Manager（对象列表管理器）

**菜单位置**: `File > 📋 Manage Object List`

**对话框功能**:
```
┌─────────────────────────────────────────────┐
│ Object List Manager                         │
├─────────────────────────────────────────────┤
│ Import a JSON file containing object        │
│ definitions.                                │
│                                             │
│ [📂 Import JSON]                            │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Category ID | Instance ID | Label Name  │ │
│ ├─────────────────────────────────────────┤ │
│ │      1      |      1      | backpack    │ │
│ │      1      |      2      | bag         │ │
│ │      2      |      1      | person      │ │
│ │     ...     |     ...     | ...         │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [➕ Add] [➖ Remove] [🗑️ Clear All]         │
│                                             │
│              [OK]  [Cancel]                 │
└─────────────────────────────────────────────┘
```

**功能**:
- ✅ 导入 JSON 文件
- ✅ 手动添加对象
- ✅ 删除选中对象
- ✅ 清空所有对象
- ✅ 查看当前对象列表

### 2. Clip Dialog（编辑对话框）

**未导入对象列表时**（原有行为）:
```
┌─────────────────────────────────────────┐
│ Edit Clip                               │
├─────────────────────────────────────────┤
│ Label *:        [backpack         ]     │ ← LineEdit（手动输入）
│ IDs:            Category: [0] Instance: [0]
│ Recognition:    [backpack         ]     │
│ Scene:          [outdoor          ]     │
│ ...                                     │
└─────────────────────────────────────────┘
```

**导入对象列表后**:
```
┌─────────────────────────────────────────┐
│ Edit Clip                               │
├─────────────────────────────────────────┤
│ Label *:        [backpack         ▼]    │ ← ComboBox（下拉选择）
│ IDs:            Category: [1] Instance: [1] ← 自动填充
│ Recognition:    [backpack         ]     │
│ Scene:          [outdoor          ]     │
│ ...                                     │
└─────────────────────────────────────────┘
```

**特性**:
- ✅ 下拉列表显示所有可用标签
- ✅ 可编辑（允许输入不在列表中的标签）
- ✅ 选择标签时自动填充 Category ID 和 Instance ID
- ✅ 可以手动修改 ID

### 3. CSV 导出

**新增列**:
```csv
label,start_frame,end_frame,video_file,...,recognition,scene,category_id,instance_id
backpack,0,150,video.mp4,...,backpack,outdoor,1,1
person,151,300,video.mp4,...,person,indoor,2,1
```

**列说明**:
- `category_id`: 第 11 列
- `instance_id`: 第 12 列

## 📝 使用流程 (Usage Flow)

### 场景 1: 导入对象列表

```
1. 准备 JSON 文件（参考 example_object_list.json）
2. 打开应用
3. File > 📋 Manage Object List
4. 点击 "📂 Import JSON"
5. 选择 JSON 文件
6. 确认导入（显示成功消息）
7. 点击 OK
```

**结果**: 对象列表已加载，后续创建/编辑 clip 时可以从下拉列表选择

### 场景 2: 手动创建 Clip（有对象列表）

```
1. Mark Start / Mark End
2. 在对话框中：
   - Label: 从下拉列表选择 "backpack"
   - Category ID 和 Instance ID 自动填充为 (1, 1)
   - 填写其他字段...
3. 点击 OK
```

**结果**: Clip 创建，包含正确的 Category ID 和 Instance ID

### 场景 3: LLM 自动创建 Clip

```
1. 提取 captions
2. 点击 "🤖 Analyze & Fill Clips"
3. LLM 自动创建 clips：
   - Label: "backpack"
   - Recognition: "backpack"
   - Scene: ""
   - Category ID: 0  ← 默认
   - Instance ID: 0  ← 默认
4. 用户可以右键编辑，从下拉列表选择正确的标签
   （选择后 ID 自动更新）
```

### 场景 4: 手动添加对象

```
1. File > 📋 Manage Object List
2. 点击 "➕ Add"
3. 填写：
   - Category ID: 7
   - Instance ID: 1
   - Label Name: "new_object"
4. 点击 OK
5. 对象添加到列表
6. 点击 OK 保存
```

## 🔧 技术实现 (Implementation)

### 1. 新增组件

**`object_list_dialog.py`**:
```python
class ObjectListDialog(QtWidgets.QDialog):
    """Dialog for importing and managing object list."""
    
    def _import_json(self):
        # 导入 JSON 文件
        # 验证格式
        # 加载对象
    
    def _add_object(self):
        # 手动添加对象
    
    def get_objects(self):
        # 返回对象列表
```

### 2. ClipDialog 更新

**`clip_dialog.py`**:
```python
class ObjectInfo:
    """Container for object list information."""
    objects = []  # Global object list

class ClipDialog(QtWidgets.QDialog):
    def _init_ui(self, ...):
        if _object_info.objects:
            # 使用 ComboBox
            self.label_combo = QtWidgets.QComboBox()
            self.label_combo.setEditable(True)
            self.label_combo.addItems(_object_info.get_labels())
            self.label_combo.currentTextChanged.connect(self._on_label_changed)
        else:
            # 使用 LineEdit（fallback）
            self.label_input = QtWidgets.QLineEdit()
    
    def _on_label_changed(self, label: str):
        # 自动更新 Category ID 和 Instance ID
        obj = _object_info.get_object_by_label(label)
        if obj:
            self.category_spin.setValue(obj["category_id"])
            self.instance_spin.setValue(obj["instance_id"])
```

### 3. 全局对象列表管理

```python
# Global functions
def set_object_list(objects: list[dict]):
    """Set the global object list."""
    _object_info.objects = objects

def get_object_list() -> list[dict]:
    """Get the global object list."""
    return _object_info.objects
```

### 4. CSV 读写更新

**写入**:
```python
writer.writerow([
    # ... 原有字段 ...
    clip.category_id,  # 新增
    clip.instance_id,  # 新增
])
```

**读取**:
```python
category_id = int(row.get("category_id", 0))
instance_id = int(row.get("instance_id", 0))
clip = VideoClip(..., category_id=category_id, instance_id=instance_id)
```

## 📊 数据流 (Data Flow)

### 导入对象列表流程

```
JSON 文件
  ↓
ObjectListDialog.import_json()
  ↓
验证格式
  ↓
加载到 _object_info.objects
  ↓
set_object_list(objects)
  ↓
全局可用
```

### 创建 Clip 流程（有对象列表）

```
用户点击 Mark End
  ↓
ClipDialog 打开
  ↓
检查 _object_info.objects
  ├─ 有对象 → 显示 ComboBox
  └─ 无对象 → 显示 LineEdit
  ↓
用户选择标签（从下拉列表）
  ↓
_on_label_changed() 触发
  ↓
自动填充 Category ID 和 Instance ID
  ↓
用户点击 OK
  ↓
VideoClip 创建（包含 ID）
  ↓
CSV 导出（包含 ID）
```

### LLM 自动填充流程

```
LLM 分析
  ↓
ObjectDetection(object_name=...)
  ↓
_fill_clips_from_llm_detections()
  ↓
VideoClip(
  label=object_name,
  category_id=0,  # 默认
  instance_id=0,  # 默认
)
  ↓
用户可以编辑
  ├─ 从下拉列表选择标签
  └─ ID 自动更新
```

## 🔄 向后兼容 (Backward Compatibility)

### 读取旧版 CSV

**旧版 CSV**（无 category_id, instance_id）:
```csv
label,start_frame,end_frame,video_file,...,recognition,scene
backpack,0,150,video.mp4,...,backpack,outdoor
```

**读取逻辑**:
```python
category_id = int(row.get("category_id", 0))  # 默认 0
instance_id = int(row.get("instance_id", 0))  # 默认 0
```

**结果**: 旧版 CSV 可以正常读取，ID 字段为 0

### 未导入对象列表

**行为**: 如果没有导入对象列表，ClipDialog 会回退到 LineEdit 模式，功能与原来完全相同

## ✅ 测试场景 (Testing Scenarios)

### 1. 导入对象列表

- ✅ 导入有效的 JSON 文件
- ✅ 导入无效的 JSON 文件（显示错误）
- ✅ 导入空列表（显示警告）
- ✅ 手动添加对象
- ✅ 删除对象
- ✅ 清空所有对象

### 2. 创建 Clip（有对象列表）

- ✅ 从下拉列表选择标签
- ✅ ID 自动填充
- ✅ 手动修改 ID
- ✅ 输入不在列表中的标签
- ✅ CSV 导出包含 ID

### 3. 创建 Clip（无对象列表）

- ✅ 使用 LineEdit 输入标签
- ✅ 手动输入 ID（默认 0）
- ✅ 功能与原来相同

### 4. 编辑 Clip

- ✅ 从下拉列表选择新标签
- ✅ ID 自动更新
- ✅ 手动修改 ID
- ✅ 保存后 CSV 更新

### 5. LLM 自动创建

- ✅ LLM 创建 clips，ID 为 (0, 0)
- ✅ 编辑时可以从下拉列表选择
- ✅ 选择后 ID 更新

### 6. CSV 导入导出

- ✅ 导出包含 category_id 和 instance_id
- ✅ 导入旧版 CSV（无 ID）正常工作
- ✅ 导入新版 CSV（有 ID）正常工作

## 📚 示例 JSON 文件 (Example JSON)

**`example_object_list.json`**:
```json
[
  {
    "category_id": 1,
    "instance_id": 1,
    "label_name": "backpack"
  },
  {
    "category_id": 1,
    "instance_id": 2,
    "label_name": "bag"
  },
  {
    "category_id": 2,
    "instance_id": 1,
    "label_name": "person"
  },
  {
    "category_id": 2,
    "instance_id": 2,
    "label_name": "pedestrian"
  },
  {
    "category_id": 3,
    "instance_id": 1,
    "label_name": "car"
  }
]
```

**使用方法**:
1. 保存为 `my_objects.json`
2. File > 📋 Manage Object List
3. 📂 Import JSON
4. 选择 `my_objects.json`
5. 完成！

## 🎯 设计理由 (Design Rationale)

### 为什么添加 Category ID 和 Instance ID？

1. **标准化**: 许多数据集使用 category_id 和 instance_id 来组织对象
2. **灵活性**: 同一类别可以有多个实例（如 "backpack" 和 "bag" 都属于类别 1）
3. **兼容性**: 便于与其他工具和数据集集成

### 为什么使用下拉列表？

1. **一致性**: 确保标签名称统一，避免拼写错误
2. **效率**: 快速选择，无需手动输入
3. **可编辑**: 仍然允许输入不在列表中的标签

### 为什么 LLM 填充时 ID 默认为 0？

1. **未知映射**: LLM 不知道对象列表中的 ID
2. **用户控制**: 让用户手动选择正确的标签和 ID
3. **灵活性**: 用户可以决定是否使用对象列表

### 为什么使用全局对象列表？

1. **简单性**: 整个应用共享一个对象列表
2. **持久性**: 导入一次，所有对话框都可以使用
3. **易于管理**: 集中管理，统一更新

## 🎉 总结

**新增功能**:
- ✅ 对象列表管理器（导入 JSON、手动添加）
- ✅ 标签下拉选择（ComboBox）
- ✅ 自动填充 Category ID 和 Instance ID
- ✅ CSV 导出包含 ID 字段
- ✅ 向后兼容旧版 CSV

**用户体验**:
- ✅ 快速选择标签（下拉列表）
- ✅ 自动填充 ID（无需手动输入）
- ✅ 灵活性（可编辑、可手动修改）
- ✅ 可选功能（不导入对象列表也能正常使用）

**使用场景**:
- ✅ 标准化数据集标注
- ✅ 团队协作（统一标签）
- ✅ 大规模标注（快速选择）
- ✅ 与其他工具集成

---

**修改文件**:
- `app.py` - VideoClip 数据结构、菜单、CSV 读写
- `clip_dialog.py` - ComboBox、自动填充 ID
- `object_list_dialog.py` - 新增对象列表管理器
- `widgets/__init__.py` - 导出新组件

**示例文件**:
- `example_object_list.json` - 示例对象列表

**测试状态**: ✅ 已验证
