# LLM Caption Analysis - Usage Example

This document provides a step-by-step example of using the LLM caption analysis feature.

## Example Scenario

You have a navigation video where a participant describes objects they detect while navigating. You want to extract structured information about:
- What objects were detected
- Detection and recognition confidence scores (0-5 scale)
- Whether objects are hazards
- Descriptions of why objects are hazardous

## Step-by-Step Guide

### 1. Prepare Your Video

Load your video in LabelVid:
```
File → Open Video → Select "navigation_test.mp4"
```

### 2. Extract Captions

Extract captions using Whisper:
1. Click "🎤 Extract Captions"
2. Select model: `medium` (good balance of speed/accuracy)
3. Language: `auto` or `en`
4. Click "Extract"
5. Wait for extraction to complete

**Example extracted captions:**
```srt
1
00:00:00,000 --> 00:00:03,800
I see a backpack on the ground. Detection score: 4. Recognition: 3. It's a hazard because I might trip over it.

2
00:00:05,200 --> 00:00:08,100
There's a parked car on the right. Detection: 5. Recognition: 5. Not a hazard.

3
00:00:10,500 --> 00:00:14,200
I detect a pedestrian ahead. Detection: 4. Recognition: 4. Potential hazard if they move into my path.
```

### 3. Configure LLM Analysis

In the "LLM Caption Analysis" section:

**Provider:** OpenAI (GPT)
**Model:** gpt-4o-mini (fast and cost-effective)
**API Key:** 
- Enter your OpenAI API key: `sk-proj-...`
- ✓ Check "Save API key for future use"

### 4. Run Analysis

Click **🔬 Analyze Captions**

Progress dialog will show:
```
Preparing captions for analysis... (0%)
Sending to LLM for analysis... (20%)
Parsing LLM response... (80%)
Analysis complete! Found 3 detections (100%)
```

### 5. Review Results

A dialog will show the extracted detections:

```
Found 3 object detections:

⚠️ backpack (0.0s - 3.8s)
   Detection: 4.00, Recognition: 3.00
   Hazard because participant might trip over it

✓ vehicle (5.2s - 8.1s)
   Detection: 5.00, Recognition: 5.00
   Parked car on the right side, not obstructing path

⚠️ pedestrian (10.5s - 14.2s)
   Detection: 4.00, Recognition: 4.00
   Potential hazard if they move into path

Export results to JSON?
```

Click **Yes** to export.

### 6. Export to JSON

Save location dialog appears with default path:
```
navigation_test/detections/navigation_test_detections.json
```

Click **Save**.

### 7. View Exported JSON

Open `navigation_test_detections.json`:

```json
[
  {
    "timestamp_start": 0.0,
    "timestamp_end": 3.8,
    "object_name": "backpack",
    "detection_score": 4.0,
    "recognition_score": 3.0,
    "is_hazard": true,
    "description": "Hazard because participant might trip over it",
    "raw_caption": "I see a backpack on the ground. Detection score: 4. Recognition: 3. It's a hazard because I might trip over it."
  },
  {
    "timestamp_start": 5.2,
    "timestamp_end": 8.1,
    "object_name": "vehicle",
    "detection_score": 5.0,
    "recognition_score": 5.0,
    "is_hazard": false,
    "description": "Parked car on the right side, not obstructing path",
    "raw_caption": "There's a parked car on the right. Detection: 5. Recognition: 5. Not a hazard."
  },
  {
    "timestamp_start": 10.5,
    "timestamp_end": 14.2,
    "object_name": "pedestrian",
    "detection_score": 4.0,
    "recognition_score": 4.0,
    "is_hazard": true,
    "description": "Potential hazard if they move into path",
    "raw_caption": "I detect a pedestrian ahead. Detection: 4. Recognition: 4. Potential hazard if they move into my path."
  }
]
```

### 8. Use the Data

Now you can use this structured data for:

**Statistical Analysis:**
```python
import json

with open('navigation_test_detections.json') as f:
    detections = json.load(f)

# Count hazards
hazards = [d for d in detections if d['is_hazard']]
print(f"Found {len(hazards)} hazards out of {len(detections)} detections")

# Average detection score
avg_detection = sum(d['detection_score'] for d in detections) / len(detections)
print(f"Average detection score: {avg_detection:.2f}")
```

**Visualization:**
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame(detections)

# Plot detection vs recognition scores
plt.scatter(df['detection_score'], df['recognition_score'], 
            c=df['is_hazard'].map({True: 'red', False: 'green'}))
plt.xlabel('Detection Score')
plt.ylabel('Recognition Score')
plt.title('Object Detection Analysis')
plt.show()
```

**Database Storage:**
```python
import sqlite3

conn = sqlite3.connect('navigation_data.db')
df = pd.DataFrame(detections)
df.to_sql('detections', conn, if_exists='append', index=False)
```

## Tips for Better Results

### 1. Clear Caption Instructions

Train participants to speak clearly:
- "I detect [object name]"
- "Detection score: [0-5]"
- "Recognition score: [0-5]"
- "This is/is not a hazard because..."

### 2. Model Selection

| Use Case | Recommended Model | Cost | Quality |
|----------|------------------|------|---------|
| Quick test | gpt-4o-mini | $ | Good |
| Production | gpt-5 | $$$ | Best |
| Budget-conscious | gemini-3-flash-preview | $ | Good |

### 3. Handling Errors

If LLM returns unexpected results:
1. Check the raw captions for clarity
2. Try a different model (e.g., gpt-5 instead of gpt-4o-mini)
3. Manually edit captions to be more explicit
4. Check logs for LLM response

### 4. Batch Processing

For multiple videos:
```python
from labelvid.agent import CaptionAnalyzer, LLMClient, LLMProvider

client = LLMClient(provider=LLMProvider.OPENAI, api_key="sk-...")
analyzer = CaptionAnalyzer(llm_client=client)

for video_captions in all_video_captions:
    detections = analyzer.analyze_captions(video_captions)
    analyzer.export_to_json(detections, f"{video_name}_detections.json")
```

## Common Issues

### Issue: "No results found"

**Cause:** Captions don't mention any objects explicitly.

**Solution:** 
- Check caption quality
- Ensure participants are describing objects
- Try a more powerful model

### Issue: "Invalid JSON response"

**Cause:** LLM returned malformed JSON.

**Solution:**
- Try again (sometimes transient)
- Use a different model
- Check API key validity

### Issue: Scores are all null

**Cause:** Participants didn't mention scores explicitly.

**Solution:**
- This is expected if scores aren't in captions
- LLM will set to `null` when not mentioned
- Update your protocol to include explicit scores

## Cost Example

For a 5-minute video with ~50 caption segments:

| Provider | Model | Estimated Cost |
|----------|-------|---------------|
| OpenAI | gpt-4o-mini | $0.02 |
| OpenAI | gpt-5 | $0.25 |
| Google | gemini-3-flash-preview | $0.01 |
| Anthropic | claude-sonnet-4-6 | $0.20 |

**Recommendation:** Start with gpt-4o-mini or gemini-3-flash-preview for testing, then upgrade to gpt-5 or claude-sonnet-4-6 for production if needed.

## Next Steps

- [Full LLM Analysis Documentation](LLM_ANALYSIS.md)
- [Chinese Documentation (中文文档)](LLM_ANALYSIS_zh.md)
- [Main README](../README.md)
