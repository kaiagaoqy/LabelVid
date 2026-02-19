#!/usr/bin/env python
"""
Build script for creating LabelVid executable.

Usage:
    python build_exe.py          # Build executable
    python build_exe.py --clean  # Clean build artifacts first
    python build_exe.py --onedir # Build as directory instead of single file

Requirements:
    pip install pyinstaller
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def clean_build():
    """Remove build artifacts."""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['*.spec.bak']
    
    for d in dirs_to_remove:
        if os.path.exists(d):
            print(f"Removing {d}/")
            shutil.rmtree(d)
    
    # Clean __pycache__ in subdirectories
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                path = os.path.join(root, d)
                print(f"Removing {path}/")
                shutil.rmtree(path)


def create_hooks():
    """Create PyInstaller hooks for problematic packages."""
    hooks_dir = Path('hooks')
    hooks_dir.mkdir(exist_ok=True)
    
    # Hook for cv2 to prevent recursion
    cv2_hook = hooks_dir / 'hook-cv2.py'
    cv2_hook.write_text("""# PyInstaller hook for cv2 (OpenCV)
# Fixes recursion error during import

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all cv2 submodules
hiddenimports = collect_submodules('cv2')

# Collect data files
datas = collect_data_files('cv2', include_py_files=True)

# Exclude problematic modules that cause recursion
excludedimports = ['cv2.cv2']
""")
    
    print(f"  ✓ Created PyInstaller hook: {cv2_hook}")
    return str(hooks_dir)


def check_dependencies():
    """Check if required dependencies are installed."""
    print(f"Python: {sys.executable}")
    print()
    
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Check optional dependencies
    optional = {
        'osam': 'AI annotation (SAM)',
        'whisper': 'Caption extraction (Whisper)',
    }
    
    for pkg, desc in optional.items():
        try:
            mod = __import__(pkg)
            version = getattr(mod, '__version__', 'unknown')
            print(f"✓ {pkg} {version} found ({desc})")
        except ImportError:
            print(f"○ {pkg} not found ({desc} - optional)")


def build_executable(onedir=False, debug=False):
    """Build the executable using PyInstaller."""
    import os
    
    print("\n" + "="*50)
    print("Building LabelVid executable...")
    print("="*50 + "\n")
    
    # Create hooks directory
    print("Creating PyInstaller hooks...")
    hooks_dir = create_hooks()
    print()
    
    # Base command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=LabelVid',
        # '--windowed',  # Temporarily disabled due to icon issue in PyInstaller 6.11
        '--noconfirm',  # Overwrite without asking
    ]
    
    # Single file or directory
    # For macOS .app bundles, always use onedir mode
    # (onefile is deprecated for .app and doesn't work well with binaries)
    if platform.system() == 'Darwin':
        onedir = True
    
    if onedir:
        cmd.append('--onedir')
    else:
        cmd.append('--onefile')
    
    # Debug mode
    if debug:
        cmd.append('--debug=all')
        cmd.remove('--windowed')
        cmd.append('--console')
    
    # Add hooks directory
    cmd.extend(['--additional-hooks-dir', hooks_dir])
    
    # Do NOT use --collect-all cv2 (causes duplication)
    # Instead, cv2 will be collected via hidden imports
    
    # Hidden imports
    hidden_imports = [
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtMultimedia',
        'PyQt5.sip',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'loguru',
        'natsort',
        # Fix for Python 3.14
        '_struct',
        'struct',
        '_socket',
        '_ssl',
        '_hashlib',
        # Fix for pkg_resources issue
        'backports',
        'backports.tarfile',
    ]
    
    # Collect data files
    datas = []
    
    # Collect binary files (FFmpeg, etc.)
    binaries = []
    
    # Add FFmpeg binaries if available
    arch = platform.machine()  # 'arm64' or 'x86_64'
    if platform.system() == 'Darwin':
        # macOS
        ffmpeg_src = f'resources/ffmpeg-macos-{arch}'
        ffprobe_src = f'resources/ffprobe-macos-{arch}'
        
        if os.path.exists(ffmpeg_src) and os.path.exists(ffprobe_src):
            binaries.append((ffmpeg_src, '.'))
            binaries.append((ffprobe_src, '.'))
            print(f"  ✓ Adding FFmpeg binaries for macOS {arch}")
            print(f"    - {ffmpeg_src}")
            print(f"    - {ffprobe_src}")
        else:
            print(f"  ○ FFmpeg binaries not found (optional)")
            print(f"    Expected: {ffmpeg_src}, {ffprobe_src}")
    
    # Add optional imports and their data files if available
    try:
        import osam
        import os.path as osp
        
        # Add osam and imgviz with all submodules and dependencies
        osam_imports = [
            'osam',
            'osam.apis',
            'osam.types',
            'osam._models',
            # osam dependencies
            'onnxruntime',
            'onnxruntime.capi',
            'onnxruntime.capi._pybind_state',
            'gdown',
            'pydantic',
            'pydantic_core',
            'click',
            # imgviz
            'imgviz',
            'imgviz.color',
            'imgviz.draw',
            'imgviz._io',
            'imgviz.label',
            'imgviz.utils',
        ]
        hidden_imports.extend(osam_imports)
        
        # Add osam data files
        osam_path = osp.dirname(osam.__file__)
        osam_models = osp.join(osam_path, '_models')
        if osp.exists(osam_models):
            datas.append((osam_models, 'osam/_models'))
        
        print(f"  ✓ Adding osam and imgviz with {len(osam_imports)} imports")
    except ImportError:
        print(f"  ○ OSAM not found (optional)")
        pass
    
    # Add Whisper (if available)
    try:
        import whisper
        import os.path as osp
        
        # Add whisper and ALL its dependencies
        whisper_imports = [
            'whisper',
            'whisper.model',
            'whisper.audio',
            'whisper.decoding',
            'whisper.tokenizer',
            'whisper.timing',
            'whisper.utils',
            'whisper.normalizers',
            'whisper.normalizers.english',
            'whisper.normalizers.basic',
            # Whisper dependencies
            'tiktoken',
            'tiktoken.core',
            'tiktoken.load',
            'tiktoken_ext',
            'tiktoken_ext.openai_public',
            'tqdm',
            'tqdm.auto',
            'more_itertools',
            'numba',
            'llvmlite',
            'soundfile',
            'librosa',
            'audioread',
            'resampy',
            'scipy',
            'scipy.fft',
            'scipy.signal',
            'torch',
            'torch.nn',
            'torch.nn.functional',
            'triton',
        ]
        hidden_imports.extend(whisper_imports)
        
        # Add whisper data files
        whisper_path = osp.dirname(whisper.__file__)
        whisper_assets = osp.join(whisper_path, 'assets')
        if osp.exists(whisper_assets):
            datas.append((whisper_assets, 'whisper/assets'))
        
        print(f"  ✓ Adding Whisper with {len(whisper_imports)} dependencies")
        print(f"    - Whisper assets: {whisper_assets}")
    except ImportError:
        print(f"  ○ Whisper not found (optional)")
        pass
    
    # Add LLM dependencies (if available)
    llm_packages = {
        'openai': ['openai', 'openai.types', 'openai.resources'],
        'anthropic': ['anthropic', 'anthropic.types'],
        'google.generativeai': ['google.generativeai', 'google.ai'],
    }
    
    llm_found = []
    for pkg_name, imports in llm_packages.items():
        try:
            __import__(pkg_name.split('.')[0])
            hidden_imports.extend(imports)
            llm_found.append(pkg_name.split('.')[0])
        except ImportError:
            pass
    
    if llm_found:
        print(f"  ✓ Adding LLM packages: {', '.join(llm_found)}")
    else:
        print(f"  ○ LLM packages not found (optional)")
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # Collect entire packages (for packages with complex structure)
    collect_all_packages = []
    try:
        import imgviz
        collect_all_packages.append('imgviz')
    except ImportError:
        pass
    
    for pkg in collect_all_packages:
        cmd.extend(['--collect-all', pkg])
    
    # Add binary files
    for src, dst in binaries:
        cmd.extend(['--add-binary', f'{src}{os.pathsep}{dst}'])
    
    # Add data files
    for src, dst in datas:
        cmd.extend(['--add-data', f'{src}{os.pathsep}{dst}'])
    
    # Exclude unnecessary modules
    # Note: matplotlib is required by imgviz, so we can't exclude it
    excludes = ['tkinter', 'IPython', 'jupyter', 'notebook']
    for exc in excludes:
        cmd.extend(['--exclude-module', exc])
    
    # Add paths
    cmd.extend(['--paths', '.'])
    
    # Entry point
    cmd.append('run.py')
    
    print("Running:", ' '.join(cmd[:10]) + ' ...')
    print()
    
    # Run PyInstaller
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "="*50)
        print("Build successful!")
        print("="*50)
        
        # Show output location
        if platform.system() == 'Windows':
            exe_name = 'LabelVid.exe'
        elif platform.system() == 'Darwin':
            exe_name = 'LabelVid.app' if not onedir else 'LabelVid'
        else:
            exe_name = 'LabelVid'
        
        if onedir:
            output_path = Path('dist') / 'LabelVid'
        else:
            output_path = Path('dist') / exe_name
        
        print(f"\nOutput: {output_path.absolute()}")
        
        if output_path.exists():
            if output_path.is_file():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"Size: {size_mb:.1f} MB")
        
        return True
    else:
        print("\n" + "="*50)
        print("Build failed!")
        print("="*50)
        return False


def main():
    parser = argparse.ArgumentParser(description='Build LabelVid executable')
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts first')
    parser.add_argument('--onedir', action='store_true', help='Build as directory instead of single file')
    parser.add_argument('--debug', action='store_true', help='Build with debug mode (shows console)')
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("LabelVid Build Script")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    print()
    
    if args.clean:
        print("Cleaning build artifacts...")
        clean_build()
        print()
    
    print("Checking dependencies...")
    check_dependencies()
    
    success = build_executable(onedir=args.onedir, debug=args.debug)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
