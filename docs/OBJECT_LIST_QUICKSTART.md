# Object List Quick Start Guide

## 快速开始 (Quick Start)

### 1. 准备对象列表 JSON

创建一个 JSON 文件，格式如下：

```json
[
  {
    "category_id": 1,
    "instance_id": 1,
    "label_name": "backpack"
  },
  {
    "category_id": 2,
    "instance_id": 1,
    "label_name": "person"
  }
]
```

**提示**: 可以使用 `example_object_list.json` 作为模板

### 2. 导入对象列表

1. 打开 LabelVid
2. 菜单: **File > 📋 Manage Object List**
3. 点击 **📂 Import JSON**
4. 选择你的 JSON 文件
5. 点击 **OK**

### 3. 使用下拉列表选择标签

现在创建或编辑 clip 时：
- Label 字段会显示下拉列表
- 选择标签后，Category ID 和 Instance ID 会自动填充
- 你仍然可以手动输入不在列表中的标签

### 4. CSV 导出

导出的 CSV 会包含 `category_id` 和 `instance_id` 列：

```csv
label,start_frame,end_frame,...,category_id,instance_id
backpack,0,150,...,1,1
person,151,300,...,2,1
```

## 常见问题 (FAQ)

### Q: 如果不导入对象列表会怎样？
A: 应用会正常工作，Label 字段会显示为普通输入框，category_id 和 instance_id 默认为 0。

### Q: 可以修改已导入的对象列表吗？
A: 可以！再次打开 Manage Object List，可以添加、删除或清空对象。

### Q: LLM 自动创建的 clips 会有 ID 吗？
A: LLM 创建的 clips 的 category_id 和 instance_id 默认为 0。你可以右键编辑，从下拉列表选择正确的标签来更新 ID。

### Q: 旧的 CSV 文件还能读取吗？
A: 可以！旧的 CSV 文件会正常读取，缺失的 ID 字段会默认为 0。

## 示例工作流程 (Example Workflow)

```
1. 准备 objects.json
   └─ 定义所有可能的对象及其 ID

2. 导入对象列表
   └─ File > Manage Object List > Import JSON

3. 标注视频
   ├─ Mark Start / Mark End
   ├─ 从下拉列表选择标签
   └─ ID 自动填充

4. 导出结果
   └─ CSV 包含完整的 ID 信息

5. 批量处理（可选）
   ├─ LLM 自动创建 clips（ID = 0）
   └─ 手动编辑，从下拉列表选择正确标签
```

## 提示 (Tips)

- ✅ 使用有意义的 category_id 分组相似对象
- ✅ instance_id 可以用于区分同类别的不同变体
- ✅ 下拉列表支持输入搜索，快速找到标签
- ✅ 可以随时修改对象列表，立即生效

---

**更多信息**: 查看 `OBJECT_LIST_FEATURE.md` 了解详细功能说明
