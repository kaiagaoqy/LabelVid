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
    
    # Base command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=LabelVid',
        '--windowed',  # No console window
        '--noconfirm',  # Overwrite without asking
    ]
    
    # Single file or directory
    if onedir:
        cmd.append('--onedir')
    else:
        cmd.append('--onefile')
    
    # Debug mode
    if debug:
        cmd.append('--debug=all')
        cmd.remove('--windowed')
        cmd.append('--console')
    
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
    ]
    
    # Collect data files
    datas = []
    
    # Add optional imports and their data files if available
    try:
        import osam
        import os.path as osp
        hidden_imports.extend(['osam', 'imgviz'])
        
        # Add osam data files
        osam_path = osp.dirname(osam.__file__)
        osam_models = osp.join(osam_path, '_models')
        if osp.exists(osam_models):
            datas.append((osam_models, 'osam/_models'))
            print(f"  Adding osam data files from {osam_models}")
    except ImportError:
        pass
    
    try:
        import whisper
        import os.path as osp
        hidden_imports.append('whisper')
        
        # Add whisper data files
        whisper_path = osp.dirname(whisper.__file__)
        whisper_assets = osp.join(whisper_path, 'assets')
        if osp.exists(whisper_assets):
            datas.append((whisper_assets, 'whisper/assets'))
            print(f"  Adding whisper data files from {whisper_assets}")
    except ImportError:
        pass
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # Add data files
    for src, dst in datas:
        cmd.extend(['--add-data', f'{src}{os.pathsep}{dst}'])
    
    # Exclude unnecessary modules
    excludes = ['tkinter', 'matplotlib', 'IPython', 'jupyter', 'notebook']
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
