# Image Mode Guide

## Overview

Image Mode provides polygon and bounding box annotation tools, with AI-assisted segmentation (SAM) and automatic label management from video clips.

## Features

### Annotation Tools

| Tool | Shortcut | Description |
|------|----------|-------------|
| **Polygon** | `P` | Draw multi-point polygons |
| **Rectangle** | `R` | Draw bounding boxes |
| **Circle** | `O` | Draw circles |
| **Line** | `L` | Draw lines |
| **Point** | `T` | Place points |
| **AI Polygon** | `A` | SAM-based auto-segmentation |
| **Edit/Move** | `E` | Modify existing shapes |

### Image Sources

Three ways to load images:

#### 1. Open Image File
- Single image annotation
- Manual file selection

#### 2. WST (Work with Saved Thumbnails)
- Load folders of images
- **Auto-load**: When switching from Video Mode, automatically loads `<video_name>/frames/` folder
- Perfect for annotating extracted video frames
- **Label hints**: Shows corresponding clip label in status bar

#### 3. Auto-extract
- Automatically extract frames from video
- User specifies interval (e.g., every 30 frames)

## Object List Integration

Same object list as Video Mode:

1. **File → Manage Object List**
2. Import JSON or add manually
3. When creating shapes, labels appear as dropdown
4. Category/Instance IDs auto-fill

**Label Dialog with Object List:**
```
┌─────────────────────────────────────────┐
│ [chair [cat:30, inst:0] ▼]  [Group: _] │
│ Cat: [30]          Inst: [0]           │
│ ☐ Flag 1  ☐ Flag 2                    │
│ Description...                          │
│           [OK]  [Cancel]               │
└─────────────────────────────────────────┘
```

See [Image Mode Object List Feature](IMAGE_MODE_OBJECT_LIST_FEATURE.md) for details.

## Shape Management

### Creating Shapes

1. **Select tool** (e.g., press `P` for polygon)
2. **Click** to place points
3. **Finalize**: Press `Enter`, `Space`, or close polygon
4. **Label Dialog** appears:
   - Select label from dropdown (if object list loaded)
   - Category/Instance IDs auto-fill
   - Add flags, description (optional)
5. **Confirm**: Click OK

### Editing Shapes

- **Edit Mode** (`E`): Click and drag vertices
- **Right-click shape**: Context menu
  - Edit label/properties
  - Delete shape
  - Remove individual points
- **Double-click** in shape list: Edit all properties
- **Select + Delete**: Remove shape

### Shape List

Sidebar shows all shapes:
- Label and shape type
- Right-click for context menu
- Double-click to edit
- Color-coded for visual reference

## Auto-Save Feature

Two save modes:

### Auto-Save Mode (Default)

**Enable**: Check **"Auto-save to image location"**

**Shortcut**: `Ctrl+S`

**Behavior**:
- Saves directly to image directory (e.g., `image.jpg` → `image.json`)
- No file dialog
- Fast and seamless

**Triggers**:
- Manual: Press `Ctrl+S` or click "💾 Save"
- Automatic: When switching images, switching modes, or closing app

**Perfect for**: Batch annotation, quick workflows

### Manual Save Mode

**Shortcut**: `Ctrl+Shift+S`

**Behavior**:
- File dialog appears
- Choose custom location
- Default: `<video_name>/annotations/`

**Perfect for**: Centralized annotation management

See [Auto-Save Feature Guide](AUTO_SAVE_ANNOTATION_FEATURE.md) for details.

## AI-Assisted Annotation (SAM)

Use Segment Anything Model for automatic segmentation:

### Setup

```bash
pip install -e ".[ai]"
```

### Usage

1. Press `A` or select "AI Polygon"
2. **Choose model**: sam2:base (recommended)
3. **Click** to add positive points (inside object)
4. **Shift+Click** to add negative points (outside object)
5. **Preview** updates in real-time
6. **Finalize**: Press `Enter`, `Space`, or `Ctrl+Click`

**Available models:**
- `sam2:tiny/small/base/large` - SAM2 variants (faster, recommended)
- `sam:vit_h/l/b` - Original SAM variants

See [SAM Setup Guide](SAM_SETUP.md) for model downloads.

## Label Hints from Video Clips

When in WST mode with video frames:

1. Open image (e.g., `chair_start_399.jpg`)
2. **Status bar** shows: `"Label hint: chair"`
3. Hint comes from corresponding clip in `clips.json`
4. Helps maintain consistency between video and image annotations

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `P` | Polygon mode |
| `R` | Rectangle mode |
| `O` | Circle mode |
| `A` | AI Polygon (SAM) |
| `E` | Edit/Move mode |
| `Ctrl+S` | Auto-save (to image location) |
| `Ctrl+Shift+S` | Manual save (file dialog) |
| `Enter` / `Space` | Finalize current shape |
| `Escape` | Cancel current drawing |
| `Delete` | Delete selected shape or point |
| `Ctrl+Z` | Undo (in drawing) |

## Output Format

### Annotation JSON (Labelme-compatible)

```json
{
  "version": "5.0.1",
  "flags": {},
  "shapes": [
    {
      "label": "chair",
      "points": [[100, 200], [150, 200], [150, 250], [100, 250]],
      "group_id": 1,
      "category_id": 30,
      "instance_id": 0,
      "shape_type": "polygon",
      "flags": {}
    }
  ],
  "imagePath": "chair_start_399.jpg",
  "imageData": null,
  "imageHeight": 720,
  "imageWidth": 1280
}
```

**New fields** (v0.1.0):
- `category_id`: Dataset category identifier
- `instance_id`: Instance number within category

## Workflow Examples

### Example 1: Annotating Extracted Video Frames

```
Video Mode:
1. Mark clips → Extract frames → frames saved to video_name/frames/

Image Mode:
2. Toggle to Image Mode (Ctrl+M)
3. Select "WST"
4. Frames folder auto-loads
5. For each frame:
   - View label hint in status bar
   - Draw polygon/rectangle
   - Label auto-suggests from clip
   - Ctrl+S to auto-save
6. Switch to next frame → previous annotation auto-saves
```

### Example 2: Single Image Annotation

```
1. Toggle to Image Mode
2. Open Image File
3. Select annotation tool (P/R/A)
4. Draw shapes
5. Label each shape
6. Ctrl+S to save
```

### Example 3: AI-Assisted Batch Annotation

```
1. Load image folder (WST)
2. Press A for AI Polygon
3. For each image:
   - Click inside object (positive point)
   - Shift+Click outside (negative point if needed)
   - Enter to finalize
   - Label appears (with object list dropdown)
   - Next image → auto-save
```

## Tips & Best Practices

1. **Use Object Lists**: Maintain consistency with video clips
2. **Enable Auto-Save**: Speed up batch annotation
3. **WST Mode**: Automatically loads video frames
4. **Label Hints**: Pay attention to status bar hints
5. **SAM**: Use AI for complex polygons
6. **Edit Mode**: Fine-tune AI-generated polygons
7. **Group ID**: Group related shapes (e.g., chair parts)
8. **Flags**: Mark special cases (e.g., occluded, truncated)

## Related Documentation

- [Auto-Save Annotation Feature](AUTO_SAVE_ANNOTATION_FEATURE.md)
- [Auto-Save on Switch Feature](AUTO_SAVE_ON_SWITCH_FEATURE.md)
- [Image Mode Object List Feature](IMAGE_MODE_OBJECT_LIST_FEATURE.md)
- [Auto-Load Frames Feature](AUTO_LOAD_FRAMES_FEATURE.md)
- [SAM Setup Guide](SAM_SETUP.md)
- [Object List Feature](OBJECT_LIST_FEATURE.md)
