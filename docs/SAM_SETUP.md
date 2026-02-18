# SAM Setup Guide

## Overview

Segment Anything Model (SAM/SAM2) provides AI-assisted image segmentation for automatic polygon generation.

## Installation

### Quick Install

```bash
pip install -e ".[ai]"
```

This installs:
- `osam` (SAM integration wrapper)
- SAM/SAM2 dependencies

### GPU Support (Recommended)

SAM runs much faster on GPU:

```bash
# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Available Models

### SAM2 (Recommended)

| Model | Size | Speed | Accuracy | VRAM |
|-------|------|-------|----------|------|
| `sam2:tiny` | 38M | Fastest | Good | 2GB |
| `sam2:small` | 184M | Fast | Better | 4GB |
| `sam2:base` | 310M | Medium | Best | 6GB |
| `sam2:large` | 684M | Slow | Excellent | 8GB |

**Recommendation**: `sam2:base` (best balance)

### SAM (Original)

| Model | Size | Speed | Accuracy | VRAM |
|-------|------|-------|----------|------|
| `sam:vit_b` | 375M | Fast | Good | 4GB |
| `sam:vit_l` | 1.2G | Medium | Better | 6GB |
| `sam:vit_h` | 2.4G | Slow | Best | 8GB |

**Recommendation**: `sam:vit_b` for compatibility

## First-Time Setup

When you first use SAM, models are downloaded automatically:

1. Select "AI Polygon" tool (press `A`)
2. Choose model (e.g., `sam2:base`)
3. **Download starts** (shown in status bar)
4. Wait for download (1-5 minutes depending on model size)
5. Model is cached for future use

**Model cache location:**
- macOS/Linux: `~/.cache/torch/hub/checkpoints/`
- Windows: `C:\Users\<username>\.cache\torch\hub\checkpoints\`

## Usage

### In LabelVid

1. **Switch to Image Mode** (`Ctrl+M`)
2. **Load image** (Open file, WST, or auto-extract)
3. **Select AI Polygon** tool (press `A`)
4. **Choose model**: Click model dropdown → select `sam2:base`
5. **Add points**:
   - **Left-click**: Positive point (inside object)
   - **Shift+Left-click**: Negative point (outside object)
6. **Preview**: Segmentation updates in real-time
7. **Finalize**:
   - Press `Enter` or `Space`
   - Or `Ctrl+Click`
8. **Label**: Label dialog appears
9. **Save**: Auto-save or manual save

### Tips for Best Results

1. **Start with one click**: Place inside object
2. **Add more positive points**: If segmentation is incomplete
3. **Add negative points**: If segmentation includes too much (Shift+Click)
4. **Iterate**: Add/remove points until satisfied
5. **Finalize**: Press Enter when ready

### Example Workflow

```
1. Press A (AI Polygon)
2. Select sam2:base
3. Click center of object → rough segmentation
4. Click edges that are missing → better segmentation
5. Shift+Click background included → refine segmentation
6. Enter → finalize
7. Type label or select from dropdown
8. Ctrl+S → save
```

## Troubleshooting

### Error: "OSAM not installed"

```bash
pip install -e ".[ai]"
```

### Error: "Out of memory"

**Solutions:**
1. Use smaller model (`sam2:tiny` or `sam:vit_b`)
2. Close other applications
3. Reduce image resolution
4. Use CPU mode (slower but works):
   ```python
   # Automatic fallback to CPU if GPU OOM
   ```

### Slow Performance

**Solutions:**
1. Install GPU support (see above)
2. Use smaller model
3. Reduce image resolution

### Model Download Fails

**Manual download:**

```bash
# Create cache directory
mkdir -p ~/.cache/torch/hub/checkpoints/

# Download models manually
# SAM2 Base
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_base_plus.pt \
  -O ~/.cache/torch/hub/checkpoints/sam2_hiera_base_plus.pt

# SAM ViT-B
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth \
  -O ~/.cache/torch/hub/checkpoints/sam_vit_b_01ec64.pth
```

### Poor Segmentation Quality

**Tips:**
1. Use larger model (`sam2:large` or `sam:vit_h`)
2. Add more positive points on object
3. Add negative points on background
4. Ensure good image quality
5. Use Edit mode (`E`) to refine polygon after generation

## Performance Comparison

| Setup | sam2:tiny | sam2:base | sam2:large |
|-------|-----------|-----------|------------|
| CPU (i7) | ~5s | ~15s | ~40s |
| GPU (RTX 3060) | ~0.5s | ~1s | ~3s |
| GPU (RTX 4090) | ~0.2s | ~0.5s | ~1.5s |

**Recommendation**: Use GPU for interactive annotation.

## Command-Line Usage (Advanced)

```python
from osam import SAM

# Initialize model
sam = SAM(model_type="sam2:base")

# Segment with points
result = sam.segment(
    image=image_path,
    positive_points=[(100, 200), (150, 250)],
    negative_points=[(50, 50)],
)

# Get polygon
polygon = result.get_polygon()
```

## Model Selection Guide

### For Interactive Annotation
- **Recommended**: `sam2:base`
- **Pros**: Fast, accurate, works on most GPUs
- **Cons**: Requires 6GB VRAM

### For Batch Processing
- **Recommended**: `sam2:tiny` or `sam2:small`
- **Pros**: Very fast, low VRAM
- **Cons**: Slightly less accurate

### For Maximum Accuracy
- **Recommended**: `sam2:large` or `sam:vit_h`
- **Pros**: Best segmentation quality
- **Cons**: Slow, requires 8GB+ VRAM

### For Compatibility
- **Recommended**: `sam:vit_b`
- **Pros**: Works on older GPUs, original SAM
- **Cons**: Slower than SAM2

## Related Documentation

- [Image Mode Guide](IMAGE_MODE.md)
- [Object List Feature](OBJECT_LIST_FEATURE.md)
- [Auto-Save Annotation](AUTO_SAVE_ANNOTATION_FEATURE.md)

## References

- [SAM Official Repo](https://github.com/facebookresearch/segment-anything)
- [SAM2 Official Repo](https://github.com/facebookresearch/segment-anything-2)
- [OSAM Wrapper](https://github.com/jovialniyo93/osam)
