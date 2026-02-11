# LabelVid Release Guide

## 发布步骤 / Release Steps

### 1. 构建可执行文件 / Build Executable

#### macOS
```bash
cd labelvid
python build_exe.py
```

输出：`dist/LabelVid.app` 和 `dist/LabelVid`

#### Windows
在 Windows 系统上运行：
```bash
cd labelvid
python build_exe.py
```

输出：`dist/LabelVid.exe`

#### Linux
在 Linux 系统上运行：
```bash
cd labelvid
python build_exe.py
```

输出：`dist/LabelVid`

### 2. 创建发布包 / Create Release Package

运行打包脚本：
```bash
python create_release.py
```

这会自动创建：
- `releases/LabelVid-v{version}-{platform}-{arch}.zip`
- 包含可执行文件、README、LICENSE 和示例文件

### 3. GitHub Release 发布

#### 方法 1: 使用 GitHub Web 界面
1. 访问 GitHub 仓库页面
2. 点击 "Releases" → "Create a new release"
3. 创建新标签，如 `v0.1.0`
4. 填写 Release 标题和说明
5. 上传生成的 `.zip` 文件
6. 点击 "Publish release"

#### 方法 2: 使用 GitHub CLI (推荐)
```bash
# 安装 GitHub CLI (首次使用)
# macOS: brew install gh
# Windows: scoop install gh
# Linux: 参考 https://cli.github.com/

# 登录
gh auth login

# 创建 release
cd labelvid
python create_release.py --github
```

### 4. 手动打包（可选）

如果不使用脚本，可以手动创建：

```bash
cd labelvid

# macOS
zip -r LabelVid-v0.1.0-macOS-arm64.zip dist/LabelVid.app README.md LICENSE

# Windows (PowerShell)
Compress-Archive -Path dist/LabelVid.exe,README.md,LICENSE -DestinationPath LabelVid-v0.1.0-Windows-x64.zip

# Linux
zip -r LabelVid-v0.1.0-Linux-x64.zip dist/LabelVid README.md LICENSE
```

## Release 包内容

每个 release 包应包含：
- ✅ 可执行文件 (`.exe` / `.app` / binary)
- ✅ README.md (使用说明)
- ✅ LICENSE (许可证)
- ✅ CHANGELOG.md (更新日志)
- ✅ 示例文件 (可选)

## 版本号规范

使用语义化版本号：`v{major}.{minor}.{patch}`

- **Major**: 重大功能更新或不兼容的 API 变更
- **Minor**: 向后兼容的功能新增
- **Patch**: 向后兼容的问题修复

示例：
- `v0.1.0` - 初始版本
- `v0.1.1` - Bug 修复
- `v0.2.0` - 新增功能
- `v1.0.0` - 正式版本

## Release Notes 模板

```markdown
# LabelVid v0.1.0

## ✨ 新功能 / New Features
- 视频剪辑和片段标记
- AI 辅助图像标注 (SAM)
- Whisper 语音识别字幕提取
- 可视化片段时间轴

## 🐛 Bug 修复 / Bug Fixes
- 修复音视频同步问题
- 修复长视频播放性能问题

## 📦 下载 / Downloads
- **Windows**: [LabelVid-v0.1.0-Windows-x64.zip](...)
- **macOS**: [LabelVid-v0.1.0-macOS-arm64.zip](...)
- **Linux**: [LabelVid-v0.1.0-Linux-x64.zip](...)

## 📋 系统要求 / System Requirements
- Windows 10/11 (x64)
- macOS 10.15+ (Intel/Apple Silicon)
- Linux (x64)

## 🚀 快速开始 / Quick Start
1. 下载对应平台的压缩包
2. 解压文件
3. 运行可执行文件
4. 打开视频文件开始使用

详细文档请查看 [README.md](README.md)
```

## 自动化发布（GitHub Actions）

创建 `.github/workflows/release.yml` 实现自动构建和发布。

## 注意事项

1. **代码签名**：
   - Windows: 需要代码签名证书 (推荐)
   - macOS: 需要 Apple Developer 账号签名和公证
   
2. **文件大小**：
   - 单文件模式：~250-300 MB
   - 目录模式：~200-250 MB (解压后)
   
3. **测试**：
   - 在目标平台上测试可执行文件
   - 确保所有功能正常工作
   - 检查依赖项是否完整

4. **用户反馈**：
   - 提供问题反馈渠道 (GitHub Issues)
   - 收集用户使用数据
   - 持续改进和更新
