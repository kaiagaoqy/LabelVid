# 快速发布指南 / Quick Release Guide

## 🚀 快速发布 3 步骤

### 1. 构建可执行文件

#### 方法 A: 一键构建脚本（最简单，推荐）
```bash
cd labelvid
./build_release.sh
```
这个脚本会自动：
- 激活 conda 环境
- 检查依赖（Whisper, SAM）
- 构建可执行文件
- 创建 release 包

#### 方法 B: 手动构建（如果使用 Conda 环境）
```bash
cd labelvid
conda activate labelvid
python build_exe.py
```

#### 方法 C: 手动构建（如果使用普通 Python 环境）
```bash
cd labelvid
python build_exe.py
```

**重要**: 
- ⚠️ 必须在安装了所有依赖的环境中运行
- ✅ Whisper 和 SAM 会自动包含（如果已安装）
- 📦 包含 Whisper 的安装包会增加约 6-10 MB

### 2. 创建 Release 包（如果使用方法 B/C）
```bash
python create_release.py
```

这会在 `releases/` 文件夹创建一个 `.zip` 文件，包含：
- ✅ 可执行文件
- ✅ README.md
- ✅ CHANGELOG.md

### 3. 上传到 GitHub

#### 方式 A: 使用 Web 界面（推荐新手）
1. 打开 https://github.com/你的用户名/你的仓库/releases
2. 点击 "Create a new release"
3. 填写：
   - **Tag**: `v0.1.0` (版本号)
   - **Title**: `LabelVid v0.1.0`
   - **Description**: 从 CHANGELOG.md 复制相应版本的说明
4. 拖拽上传 `releases/LabelVid-v0.1.0-*.zip`
5. 点击 "Publish release"

#### 方式 B: 使用 GitHub CLI (推荐高级用户)
```bash
# 首次使用需要安装和登录
brew install gh  # macOS
gh auth login

# 创建 release
python create_release.py --github
```

## 📋 完整 Release 流程

### Windows 用户
```bash
cd labelvid
python build_exe.py          # 生成 LabelVid.exe
python create_release.py      # 打包为 .zip
```

### macOS 用户
```bash
cd labelvid
python build_exe.py          # 生成 LabelVid.app
python create_release.py      # 打包为 .zip
```

### Linux 用户
```bash
cd labelvid
python build_exe.py          # 生成 LabelVid
python create_release.py      # 打包为 .zip
```

## 🔧 高级选项

### 构建 + 打包一键完成
```bash
python create_release.py --build
```

### 指定版本号
```bash
python create_release.py --version 0.2.0
```

### 自动上传到 GitHub
```bash
python create_release.py --github
```

### 全自动发布
```bash
python create_release.py --build --github
```

## 📦 输出文件

运行后会生成：

```
labelvid/
├── dist/                              # 构建输出
│   ├── LabelVid.app (macOS)
│   ├── LabelVid.exe (Windows)
│   └── LabelVid (Linux)
├── releases/                          # Release 包
│   └── LabelVid-v0.1.0-macOS-arm64.zip
├── CHANGELOG.md                       # 自动生成
└── build/, *.spec (临时文件，可删除)
```

## 🌐 GitHub 自动构建

### 设置自动化 (首次配置)

1. 将代码推送到 GitHub
2. 确保 `.github/workflows/release.yml` 存在
3. 创建 tag 触发自动构建：

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions 会自动：
- ✅ 在 Windows、macOS、Linux 上构建
- ✅ 创建 Release
- ✅ 上传所有平台的安装包

### 查看构建进度
访问：https://github.com/你的用户名/你的仓库/actions

## ❓ 常见问题

### Q: 为什么构建时提示 "Whisper not found"？
A: 你可能没有在正确的环境中运行构建脚本。

**解决方法**：
```bash
# 确认 Whisper 已安装
conda activate labelvid
python -c "import whisper; print(whisper.__version__)"

# 使用正确的 Python 构建
conda activate labelvid
python build_exe.py
```

或者直接使用一键脚本：
```bash
./build_release.sh
```

### Q: 如何确认 Whisper 被包含在可执行文件中？
A: 构建时会显示检测到的依赖：
```
✓ osam 0.3.1 found (AI annotation (SAM))
✓ whisper 20250625 found (Caption extraction (Whisper))
```

如果显示 `○ whisper not found`，说明当前环境没有安装 Whisper。

### Q: 生成的文件很大 (250MB+)？
A: 这是正常的。PyInstaller 会打包 Python 解释器和所有依赖。
   - 不含 Whisper：~245MB
   - 含 Whisper：~252MB
   - 目录模式 (更快): `python build_exe.py --onedir`

### Q: macOS 提示"无法打开，因为无法验证开发者"？
A: 用户需要右键点击 → 选择"打开"，或在系统设置中允许。
   生产环境建议进行代码签名和公证。

### Q: Windows Defender 拦截？
A: PyInstaller 打包的程序可能被误报。建议：
   - 使用代码签名证书
   - 联系微软添加白名单
   - 在 README 中说明

### Q: 如何更新版本号？
A: 编辑 `pyproject.toml`：
```toml
version = "0.2.0"
```

## 📝 Release Notes 模板

每次发布时在 GitHub Release 中使用：

```markdown
# LabelVid v0.1.0

## ✨ 新功能
- 视频剪辑和标记
- AI 图像标注 (SAM)
- 语音识别字幕提取 (Whisper)

## 🐛 修复
- 修复音视频同步问题
- 优化长视频性能

## 💾 下载
选择你的操作系统：
- [Windows (x64)](链接)
- [macOS (Intel)](链接)
- [macOS (Apple Silicon)](链接)
- [Linux (x64)](链接)

## 📖 使用文档
查看 [README.md](README.md) 了解详细使用说明。
```

## 🎯 发布检查清单

发布前确认：
- [ ] 代码已测试，功能正常
- [ ] 更新了 `CHANGELOG.md`
- [ ] 更新了 `README.md`（如有新功能）
- [ ] 版本号已更新
- [ ] 构建成功，可执行文件能运行
- [ ] 在目标平台测试过安装包
- [ ] 准备好 Release Notes
- [ ] LICENSE 文件存在
