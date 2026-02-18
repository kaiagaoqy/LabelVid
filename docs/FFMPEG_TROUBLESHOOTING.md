# FFmpeg Troubleshooting Guide

## 🔍 问题诊断 (Problem Diagnosis)

如果在其他电脑上即使安装了 FFmpeg 仍然报错，可能是以下几个原因：

### 常见问题 (Common Issues)

#### 1. **PATH 环境变量未生效**

**症状**: 安装了 FFmpeg，但应用找不到

**原因**:
- macOS 上 Homebrew 安装后，PATH 可能没有更新
- 应用启动时读取的 PATH 和终端中的 PATH 不同
- 从 Finder/Dock 启动的应用使用的是系统默认 PATH

**解决方法**:

```bash
# 1. 验证 FFmpeg 安装
which ffmpeg
# 应该显示：/opt/homebrew/bin/ffmpeg (Apple Silicon)
# 或：/usr/local/bin/ffmpeg (Intel Mac)

# 2. 如果找不到，检查 Homebrew 安装
brew list ffmpeg

# 3. 确保 PATH 正确配置
# 编辑 ~/.zshrc（macOS Catalina 及更高版本）
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc  # Apple Silicon
# 或
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc     # Intel Mac

# 4. 重新加载配置
source ~/.zshrc

# 5. 验证
echo $PATH | grep homebrew
```

#### 2. **应用沙盒限制**

**症状**: 从终端运行正常，双击应用图标运行失败

**原因**:
- macOS 打包的 .app 文件使用不同的环境变量
- 系统 PATH 和用户 PATH 可能不同

**解决方法**:

```bash
# 方法 1: 创建系统级别的符号链接
sudo ln -sf /opt/homebrew/bin/ffmpeg /usr/local/bin/ffmpeg
sudo ln -sf /opt/homebrew/bin/ffprobe /usr/local/bin/ffprobe

# 方法 2: 从终端启动应用
open /Applications/LabelVid.app

# 方法 3: 添加 launchd 环境变量（永久解决）
sudo launchctl config user path /opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
# 然后重启电脑
```

#### 3. **Homebrew 架构不匹配**

**症状**: Intel Mac 安装了 Apple Silicon 版本（或反之）

**原因**:
- Apple Silicon Mac 上运行 Intel 应用
- Homebrew 安装在错误的架构下

**解决方法**:

```bash
# 检查 Homebrew 架构
brew config | grep "CPU"

# Apple Silicon Mac 应该显示：
# CPU: arm64

# 检查 FFmpeg 架构
file /opt/homebrew/bin/ffmpeg
# 应该显示：Mach-O 64-bit executable arm64

# 如果不匹配，重新安装正确版本的 Homebrew
```

#### 4. **权限问题**

**症状**: FFmpeg 存在但没有执行权限

**解决方法**:

```bash
# 检查权限
ls -l /opt/homebrew/bin/ffmpeg

# 应该显示：-rwxr-xr-x（包含 x 执行权限）

# 如果没有执行权限，添加：
chmod +x /opt/homebrew/bin/ffmpeg
chmod +x /opt/homebrew/bin/ffprobe
```

#### 5. **Gatekeeper 阻止**

**症状**: 第一次运行应用时被 macOS 阻止

**解决方法**:

```bash
# 移除隔离属性
sudo xattr -rd com.apple.quarantine /Applications/LabelVid.app

# 或者右键点击应用 > 打开（而不是双击）
```

## 📋 完整诊断步骤 (Complete Diagnostic Steps)

### 步骤 1: 验证 FFmpeg 安装

```bash
# 1.1 检查是否安装
which ffmpeg
which ffprobe

# 1.2 检查版本
ffmpeg -version
ffprobe -version

# 1.3 检查路径
echo $PATH | tr ':' '\n' | grep -E '(homebrew|local)'
```

**期望输出**:
```
/opt/homebrew/bin/ffmpeg
/opt/homebrew/bin/ffprobe
ffmpeg version 6.x.x ...
ffprobe version 6.x.x ...
/opt/homebrew/bin
/usr/local/bin
```

### 步骤 2: 测试应用查找逻辑

应用会按以下顺序查找 FFmpeg：

1. 系统 PATH（通过 `shutil.which()`）
2. `/usr/local/bin/ffmpeg`
3. `/opt/homebrew/bin/ffmpeg`（Apple Silicon）
4. `/usr/bin/ffmpeg`
5. `/opt/local/bin/ffmpeg`（MacPorts）
6. `~/bin/ffmpeg`

**测试每个位置**:

```bash
# 测试 shutil.which
python3 -c "import shutil; print(shutil.which('ffmpeg'))"

# 检查常见路径
ls -la /usr/local/bin/ffmpeg 2>/dev/null || echo "Not found"
ls -la /opt/homebrew/bin/ffmpeg 2>/dev/null || echo "Not found"
ls -la /usr/bin/ffmpeg 2>/dev/null || echo "Not found"
```

### 步骤 3: 测试从应用内查找

```bash
# 创建测试脚本
cat > test_ffmpeg.py << 'PYTHON'
import shutil
import os

def find_ffmpeg():
    # Method 1: shutil.which
    path = shutil.which("ffmpeg")
    if path:
        print(f"✓ Found via shutil.which: {path}")
        return path
    
    # Method 2: Common paths
    common_paths = [
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
        "/usr/bin/ffmpeg",
        "/opt/local/bin/ffmpeg",
        os.path.expanduser("~/bin/ffmpeg"),
    ]
    
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            print(f"✓ Found at: {path}")
            return path
        else:
            status = "exists" if os.path.exists(path) else "not found"
            executable = "executable" if os.path.isfile(path) and os.access(path, os.X_OK) else "not executable"
            print(f"✗ {path}: {status}, {executable}")
    
    print("✗ FFmpeg not found!")
    return None

# Print environment
print("Environment PATH:")
print(os.environ.get('PATH', '').replace(':', '\n'))
print("\nSearching for FFmpeg...")
find_ffmpeg()
PYTHON

# 运行测试
python3 test_ffmpeg.py

# 清理
rm test_ffmpeg.py
```

### 步骤 4: 确认应用启动环境

```bash
# 从终端启动应用（会继承终端的 PATH）
open -a LabelVid

# 或直接运行可执行文件
/Applications/LabelVid.app/Contents/MacOS/LabelVid
```

如果从终端启动正常，但双击图标失败，说明是 PATH 问题。

## 🔧 永久解决方案 (Permanent Solutions)

### 方案 1: 系统级符号链接（推荐）

```bash
# 创建符号链接到 /usr/local/bin（macOS 默认系统 PATH）
sudo mkdir -p /usr/local/bin
sudo ln -sf /opt/homebrew/bin/ffmpeg /usr/local/bin/ffmpeg
sudo ln -sf /opt/homebrew/bin/ffprobe /usr/local/bin/ffprobe

# 验证
ls -la /usr/local/bin/ffmpeg
/usr/local/bin/ffmpeg -version
```

**优点**: 
- 对所有应用生效
- 不需要修改环境变量
- 不需要重启

### 方案 2: launchd PATH（系统级）

```bash
# 设置系统级 PATH（需要管理员权限）
sudo launchctl config user path /opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

# 重启电脑生效
sudo reboot
```

**优点**:
- macOS 系统级设置
- 所有应用和用户都能访问
- 最彻底的解决方案

**缺点**:
- 需要重启
- 需要管理员权限

### 方案 3: Shell 配置（用户级）

```bash
# 编辑 shell 配置文件
# macOS Catalina+ 使用 zsh
nano ~/.zshrc

# 添加以下内容：
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 保存并重新加载
source ~/.zshrc

# 注意：这只对从终端启动的应用有效
```

## 🧪 测试清单 (Testing Checklist)

使用这个清单来诊断问题：

```bash
# ========================================
# FFmpeg 诊断清单
# ========================================

echo "1. 检查 FFmpeg 是否安装..."
if which ffmpeg > /dev/null 2>&1; then
    echo "✓ FFmpeg 已安装: $(which ffmpeg)"
    ffmpeg -version | head -1
else
    echo "✗ FFmpeg 未找到"
fi

echo ""
echo "2. 检查 Homebrew..."
if which brew > /dev/null 2>&1; then
    echo "✓ Homebrew 已安装: $(which brew)"
    brew list ffmpeg > /dev/null 2>&1 && echo "✓ FFmpeg 通过 Homebrew 安装" || echo "✗ FFmpeg 未通过 Homebrew 安装"
else
    echo "✗ Homebrew 未安装"
fi

echo ""
echo "3. 检查常见 FFmpeg 路径..."
for path in /opt/homebrew/bin/ffmpeg /usr/local/bin/ffmpeg /usr/bin/ffmpeg; do
    if [ -f "$path" ]; then
        echo "✓ 找到: $path"
        ls -l "$path"
    else
        echo "✗ 未找到: $path"
    fi
done

echo ""
echo "4. 检查 PATH 环境变量..."
echo $PATH | tr ':' '\n' | grep -E '(homebrew|local)' | while read p; do
    echo "  - $p"
done

echo ""
echo "5. 检查 Python shutil.which..."
python3 -c "import shutil; path = shutil.which('ffmpeg'); print(f'✓ shutil.which 找到: {path}' if path else '✗ shutil.which 未找到')"

echo ""
echo "6. 检查应用是否需要权限修复..."
if [ -d "/Applications/LabelVid.app" ]; then
    echo "✓ 应用已安装"
    xattr /Applications/LabelVid.app | grep -q quarantine && echo "⚠ 应用被隔离，运行: sudo xattr -rd com.apple.quarantine /Applications/LabelVid.app" || echo "✓ 应用无隔离属性"
else
    echo "✗ 应用未安装到 /Applications"
fi

echo ""
echo "诊断完成！"
```

**保存并运行**:

```bash
# 保存上面的脚本为 diagnose_ffmpeg.sh
chmod +x diagnose_ffmpeg.sh
./diagnose_ffmpeg.sh
```

## 💡 给用户的建议 (User Instructions)

创建一个简单的用户指南：

### 如果看到 "FFmpeg Not Found" 错误

**方法 1: 快速修复（推荐）**

```bash
# 1. 安装 FFmpeg（如果还没安装）
brew install ffmpeg

# 2. 创建符号链接
sudo ln -sf /opt/homebrew/bin/ffmpeg /usr/local/bin/ffmpeg
sudo ln -sf /opt/homebrew/bin/ffprobe /usr/local/bin/ffprobe

# 3. 重启应用
```

**方法 2: 从终端启动**

```bash
# 直接从终端打开应用
open /Applications/LabelVid.app
```

**方法 3: 完整配置（一劳永逸）**

```bash
# 1. 配置系统 PATH
sudo launchctl config user path /opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin

# 2. 重启电脑
sudo reboot
```

## 📝 收集错误信息 (Collecting Error Information)

如果问题仍然存在，请收集以下信息：

```bash
# 创建诊断报告
cat > ffmpeg_diagnostic_report.txt << 'REPORT'
=== FFmpeg Diagnostic Report ===
Generated: $(date)

System Info:
$(uname -a)
$(sw_vers)

Homebrew Info:
$(which brew)
$(brew --version 2>&1)
$(brew list ffmpeg 2>&1)

FFmpeg Info:
$(which ffmpeg)
$(which ffprobe)
$(ffmpeg -version 2>&1 | head -5)

PATH:
$PATH

Common Paths Check:
$(ls -la /opt/homebrew/bin/ffmpeg 2>&1)
$(ls -la /usr/local/bin/ffmpeg 2>&1)
$(ls -la /usr/bin/ffmpeg 2>&1)

Python Check:
$(python3 -c "import shutil; print('shutil.which:', shutil.which('ffmpeg'))" 2>&1)

Application Info:
$(ls -la /Applications/LabelVid.app 2>&1)
$(xattr /Applications/LabelVid.app 2>&1)
REPORT

# 查看报告
cat ffmpeg_diagnostic_report.txt
```

将此报告连同错误信息一起提供，可以帮助快速定位问题。

## ✅ 常见场景解决方案总结

| 场景 | 症状 | 解决方案 |
|------|------|---------|
| 刚安装 FFmpeg | 终端中 `which ffmpeg` 正常，但应用找不到 | `sudo ln -sf /opt/homebrew/bin/ffmpeg /usr/local/bin/ffmpeg` |
| 从终端启动正常 | 双击图标启动失败 | PATH 问题，使用符号链接方案 |
| Apple Silicon Mac | 安装了但找不到 | 确认安装在 `/opt/homebrew/bin/`，创建符号链接 |
| Intel Mac | 安装了但找不到 | 确认安装在 `/usr/local/bin/`，应该能直接找到 |
| Gatekeeper 阻止 | 应用无法打开 | `sudo xattr -rd com.apple.quarantine /Applications/LabelVid.app` |
| 权限问题 | FFmpeg 没有执行权限 | `chmod +x /opt/homebrew/bin/ffmpeg` |

---

**最推荐的解决方案**:
```bash
# 一行命令解决（需要管理员密码）
sudo ln -sf /opt/homebrew/bin/ffmpeg /usr/local/bin/ffmpeg && sudo ln -sf /opt/homebrew/bin/ffprobe /usr/local/bin/ffprobe && echo "✓ 完成！重启应用即可使用。"
```
