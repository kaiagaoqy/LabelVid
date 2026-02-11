# Testing Guide for LabelVid Release

## Pre-Release Testing Checklist

Before releasing, test the following features:

### ✅ Video Mode

#### Basic Playback
- [ ] Open video file
- [ ] Play/pause with spacebar
- [ ] Seek with slider
- [ ] Adjust playback speed (0.25x - 4x)
- [ ] Navigate with arrow keys
- [ ] Quick jump buttons (1s, 5s, 10s, 30s, 1min, 5min)

#### Audio
- [ ] Audio plays synchronized with video
- [ ] Volume control works
- [ ] Audio checkbox enables/disables audio
- [ ] Audio works with different video codecs

#### Clip Marking
- [ ] Mark start with `[` key
- [ ] Mark end with `]` key
- [ ] Enter clip label
- [ ] Clips appear in list
- [ ] Right-click clip menu (Edit, Delete, Go to Start/End)
- [ ] Delete clip with Delete key
- [ ] Drag timeline markers to adjust clip boundaries

#### Frame Extraction
- [ ] Extract frames button works
- [ ] First and last frames saved correctly
- [ ] clips.csv generated with correct data
- [ ] Files organized in video-named folder structure

#### Caption Extraction (Whisper)
- [ ] Enable Whisper checkbox
- [ ] Select model (tiny, base, small, etc.)
- [ ] Extract captions button works
- [ ] Captions display in real-time during playback
- [ ] Auto-load existing SRT files
- [ ] Export SRT/WebVTT works

### ✅ Image Mode

#### Mode Switching
- [ ] Switch to Image mode with Ctrl+M
- [ ] Current frame loads correctly
- [ ] WST mode loads extracted frames
- [ ] Auto-extract creates frames

#### Drawing Tools
- [ ] Polygon tool works
- [ ] Rectangle tool works
- [ ] Circle tool works
- [ ] Line tool works
- [ ] Point tool works

#### AI Annotation (SAM)
- [ ] AI Polygon button works
- [ ] Select SAM model (sam2:tiny/small/base/large)
- [ ] Click to add positive points
- [ ] Shift+Click to add negative points
- [ ] Polygon generated correctly
- [ ] Press Enter/Space to finalize

#### Shape Editing
- [ ] Edit/Move mode (E key)
- [ ] Move shapes
- [ ] Resize shapes
- [ ] Edit shape points
- [ ] Right-click shape for menu
- [ ] Delete point from polygon
- [ ] Delete entire shape

#### Shape Management
- [ ] Shape list shows all shapes
- [ ] Click shape in list to select
- [ ] Right-click shape in list for menu
- [ ] Edit label works
- [ ] Delete shape works

#### Save/Load
- [ ] Save annotation to JSON
- [ ] JSON format compatible with Labelme
- [ ] Files saved in video-named/annotations/ folder

### ✅ Packaged Executable Tests

#### FFmpeg Detection
- [ ] App finds ffmpeg in /opt/homebrew/bin (Apple Silicon)
- [ ] App finds ffmpeg in /usr/local/bin (Intel)
- [ ] Friendly error if ffmpeg not found
- [ ] Audio extraction works with system ffmpeg
- [ ] Whisper audio extraction works

#### Data Files
- [ ] Whisper mel_filters.npz loads correctly
- [ ] OSAM model files load correctly
- [ ] No "file not found" errors for bundled data

#### Performance
- [ ] App starts in < 5 seconds
- [ ] Video playback smooth
- [ ] No memory leaks during long sessions
- [ ] Large videos (>1GB) work correctly

### ✅ Cross-Platform Tests

#### macOS
- [ ] Intel Mac (x86_64)
- [ ] Apple Silicon (arm64)
- [ ] macOS 12+
- [ ] .app bundle opens correctly
- [ ] No Gatekeeper issues

#### Windows
- [ ] Windows 10 (x64)
- [ ] Windows 11 (x64)
- [ ] .exe runs without admin
- [ ] No antivirus false positives

#### Linux
- [ ] Ubuntu 20.04+
- [ ] Debian 11+
- [ ] Executable has correct permissions

### 🐛 Known Issues

Document any known issues here:

1. **macOS Code Signing**: App is not signed, users need to right-click > Open
2. **Windows Defender**: May flag as unknown publisher
3. **Large Videos**: Videos > 4GB may be slow to load

### 📊 Test Results

| Feature | macOS Intel | macOS ARM | Windows | Linux | Notes |
|---------|-------------|-----------|---------|-------|-------|
| Video Playback | ⏳ | ✅ | ⏳ | ⏳ | |
| Audio | ⏳ | ✅ | ⏳ | ⏳ | Requires ffmpeg |
| Whisper | ⏳ | ✅ | ⏳ | ⏳ | Requires ffmpeg |
| SAM | ⏳ | ✅ | ⏳ | ⏳ | |
| Clip Timeline | ⏳ | ✅ | ⏳ | ⏳ | |

Legend:
- ✅ Tested, working
- ❌ Tested, broken
- ⏳ Not yet tested
- N/A Not applicable

### 🔍 Regression Tests

After each update, verify:

1. **No Breaking Changes**
   - [ ] Old clips.csv files still load
   - [ ] Old annotation JSON files still load
   - [ ] Keyboard shortcuts unchanged

2. **Performance**
   - [ ] App startup time < 5s
   - [ ] Video load time < 2s for 1GB file
   - [ ] No memory leaks after 1 hour use

3. **Data Integrity**
   - [ ] Extracted frames match video
   - [ ] Clip timestamps accurate
   - [ ] Annotations save/load correctly

### 📝 Testing Notes

Add any observations or issues found during testing:

```
Date: 2026-02-10
Tester: 
Platform: macOS arm64
Version: 0.1.0

Issues Found:
- None so far

Suggestions:
- Consider adding batch processing for multiple videos
```

### 🚀 Release Approval

- [ ] All critical features tested
- [ ] No blocking bugs
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] README accurate

**Approved by**: ___________
**Date**: ___________
