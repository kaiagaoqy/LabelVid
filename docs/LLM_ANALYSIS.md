# LLM Caption Analysis

Use AI language models to automatically extract structured object detection information from video captions.

## Features

Analyze captions to extract:
- **Object names**: What objects are mentioned
- **Detection scores**: Confidence in object detection (0-1)
- **Recognition scores**: Confidence in object recognition (0-1)
- **Hazard identification**: Whether objects are hazards/dangers
- **Descriptions**: Context about each detection

## Supported LLM Providers

| Provider | Models | API Key Required |
|----------|--------|------------------|
| **OpenAI (GPT)** | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo | OPENAI_API_KEY |
| **Google (Gemini)** | gemini-1.5-pro, gemini-1.5-flash, gemini-1.0-pro | GEMINI_API_KEY |
| **Anthropic (Claude)** | claude-3-5-sonnet, claude-3-5-haiku, claude-3-opus | ANTHROPIC_API_KEY |

## Installation

### Install LLM Dependencies

```bash
# Install all LLM providers
pip install -e ".[llm]"

# Or install specific providers
pip install openai              # For GPT
pip install google-generativeai # For Gemini
pip install anthropic           # For Claude
```

### Set API Keys

You have three options for providing API keys:

#### Option 1: Save in Application (Recommended for Personal Use)
1. Enter your API key in the application
2. Check "Save API key for future use"
3. Click "Analyze Captions"
4. The key will be saved securely and auto-loaded next time

**Note**: Saved keys are stored in your system's application settings:
- macOS: `~/Library/Preferences/com.LabelVid.LLMAnalysis.plist`
- Linux: `~/.config/LabelVid/LLMAnalysis.conf`
- Windows: Registry under `HKEY_CURRENT_USER\Software\LabelVid\LLMAnalysis`

To clear a saved key: Uncheck "Save API key" and analyze again.

#### Option 2: Environment Variables (Recommended for Shared Systems)
```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Gemini
export GEMINI_API_KEY="AI..."

# Claude
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### Option 3: Enter Each Time
Simply enter your API key without checking "Save API key".

## Usage

### Step 1: Extract or Load Captions

First, you need captions:
- **Extract**: Use Whisper to extract captions from video
- **Load**: Open a video that already has a `.srt` file

### Step 2: Configure LLM

In the "LLM Caption Analysis" section:
1. Select **Provider** (OpenAI, Gemini, or Claude)
2. Select **Model** (e.g., gpt-4o-mini for fast/cheap, gpt-4o for best quality)
3. Enter **API Key** (or leave blank if set in environment)

### Step 3: Analyze

Click **🔬 Analyze Captions**

The LLM will:
1. Read all caption segments
2. Identify object detections mentioned
3. Extract structured information
4. Show results in a dialog

### Step 4: Export

Click **Yes** to export results to JSON format.

Output location: `<video_name>/detections/<video_name>_detections.json`

## Output Format

```json
[
  {
    "timestamp_start": 0.0,
    "timestamp_end": 3.8,
    "object_name": "pedestrian",
    "detection_score": 0.95,
    "recognition_score": 0.92,
    "is_hazard": true,
    "description": "Pedestrian crossing the road",
    "raw_caption": "Oh yeah, here comes the hard part where we push you into traffic."
  },
  {
    "timestamp_start": 5.2,
    "timestamp_end": 8.1,
    "object_name": "vehicle",
    "detection_score": 0.88,
    "recognition_score": 0.85,
    "is_hazard": false,
    "description": "Parked vehicle on the side",
    "raw_caption": "There's a car parked on the right side."
  }
]
```

## Example Workflow

```
1. Load video: navigation_test.mp4
2. Extract captions with Whisper
3. Configure LLM:
   - Provider: OpenAI (GPT)
   - Model: gpt-4o-mini
   - API Key: (from environment)
4. Click "Analyze Captions"
5. Review results:
   - Found 5 object detections
   - 2 marked as hazards
6. Export to JSON
7. Use JSON for downstream processing
```

## Cost Estimates

Approximate API costs per video (3-5 minute video):

| Provider | Model | Cost per Analysis |
|----------|-------|-------------------|
| OpenAI | gpt-4o-mini | ~$0.01-0.05 |
| OpenAI | gpt-4o | ~$0.10-0.30 |
| Google | gemini-1.5-flash | ~$0.01-0.03 |
| Google | gemini-1.5-pro | ~$0.05-0.15 |
| Anthropic | claude-3-5-haiku | ~$0.02-0.08 |
| Anthropic | claude-3-5-sonnet | ~$0.10-0.30 |

**Recommendation**: Start with `gpt-4o-mini` or `gemini-1.5-flash` for cost-effective results.

## Tips

1. **Better Captions = Better Analysis**
   - Use higher quality Whisper models (medium, large)
   - Ensure captions are accurate

2. **Model Selection**
   - **Fast & Cheap**: gpt-4o-mini, gemini-1.5-flash
   - **Best Quality**: gpt-4o, claude-3-5-sonnet
   - **Balanced**: gemini-1.5-pro

3. **API Key Security**
   - For personal use: Save in application for convenience
   - For shared systems: Use environment variables
   - Don't commit API keys to git
   - Rotate keys regularly
   - Saved keys are stored locally on your machine only

4. **Error Handling**
   - Check API key is valid
   - Ensure internet connection
   - Review LLM response if results seem wrong

## Troubleshooting

### "API key not found"
Set environment variable or enter key in UI.

### "Failed to import LLM modules"
Install dependencies: `pip install -e ".[llm]"`

### "Invalid JSON response from LLM"
The LLM returned malformed JSON. Try:
- Using a different model
- Simplifying the captions
- Checking the logs for the raw response

### "Analysis failed: Rate limit exceeded"
You've hit the API rate limit. Wait a few minutes or upgrade your API plan.

## Advanced Usage

### Custom Prompts

To customize the analysis prompt, modify `_caption_analyzer.py`:

```python
system_prompt = """Your custom prompt here..."""
```

### Batch Processing

Analyze multiple videos programmatically:

```python
from labelvid.agent import CaptionAnalyzer, LLMClient, LLMProvider

# Create client
client = LLMClient(provider=LLMProvider.OPENAI, api_key="sk-...")
analyzer = CaptionAnalyzer(llm_client=client)

# Analyze
detections = analyzer.analyze_captions(caption_segments)

# Export
analyzer.export_to_json(detections, "output.json")
```

## Privacy & Data

- Captions are sent to the selected LLM provider's API
- Review provider's privacy policy before use
- For sensitive content, consider:
  - Self-hosted LLMs (not currently supported)
  - Manual annotation instead of LLM
  - Redacting sensitive information from captions

## Future Enhancements

Planned features:
- [ ] Support for local LLMs (Ollama, LLaMA)
- [ ] Batch analysis for multiple videos
- [ ] Custom prompt templates
- [ ] Detection visualization on timeline
- [ ] Export to other formats (CSV, XML)
