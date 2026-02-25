#!/usr/bin/env python
"""
Create release package for LabelVid.

Usage:
    python create_release.py                    # Create local release package
    python create_release.py --github          # Create and upload to GitHub
    python create_release.py --version 0.2.0   # Specify version
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path


def get_version():
    """Get version from pyproject.toml."""
    # Read version manually (works without tomli)
    with open('pyproject.toml', 'r') as f:
        for line in f:
            if line.strip().startswith('version'):
                # Extract version: version = "0.1.0"
                version = line.split('=')[1].strip().strip('"\'')
                return version
    return '0.1.0'


def get_platform_info():
    """Get platform and architecture info."""
    system = platform.system()
    machine = platform.machine()
    
    # Normalize platform names
    platform_map = {
        'Darwin': 'macOS',
        'Windows': 'Windows',
        'Linux': 'Linux',
    }
    
    # Normalize architecture names
    arch_map = {
        'x86_64': 'x64',
        'AMD64': 'x64',
        'arm64': 'arm64',
        'aarch64': 'arm64',
    }
    
    return platform_map.get(system, system), arch_map.get(machine, machine)


def create_changelog():
    """Create or update CHANGELOG.md."""
    changelog_path = Path('CHANGELOG.md')
    
    if not changelog_path.exists():
        version = get_version()
        date = datetime.now().strftime('%Y-%m-%d')
        
        content = f"""# Changelog

All notable changes to LabelVid will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [{version}] - {date}

### Added
- Video clipping with clip marking and timeline visualization
- Audio playback synchronized with video
- AI-assisted image annotation using SAM/SAM2
- Whisper speech recognition for caption extraction
- Real-time caption display during video playback
- Auto-save and auto-load for clips and captions
- Quick jump buttons (1s, 5s, 10s, 30s, 1min, 5min)
- Shape editing with right-click context menus
- Organized output folder structure

### Fixed
- Video-audio synchronization issues
- Performance optimization for long videos
- Canvas shape editing stability

### Changed
- Updated UI button labels for better clarity
- Improved caption auto-loading behavior
"""
        
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created {changelog_path}")
    
    return changelog_path


def create_release_package(version=None, output_dir='releases', suffix=None):
    """Create a release package.
    
    Args:
        version: Version string (e.g., "0.1.0")
        output_dir: Output directory for the release package
        suffix: Optional suffix for the package name (e.g., "Full", "Lite")
    """
    if version is None:
        version = get_version()
    
    platform_name, arch = get_platform_info()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Package name with optional suffix
    if suffix:
        package_name = f"LabelVid-v{version}-{platform_name}-{arch}-{suffix}"
    else:
        package_name = f"LabelVid-v{version}-{platform_name}-{arch}"
    package_path = output_path / f"{package_name}.zip"
    
    print(f"\nCreating release package: {package_name}")
    print("=" * 60)
    
    # Check if executable exists
    dist_path = Path('dist')
    if not dist_path.exists():
        print("❌ Error: dist/ folder not found. Please build the executable first:")
        print("   python build_exe.py")
        return None
    
    # Find executable
    executable = None
    if platform_name == 'macOS':
        app_bundle = dist_path / 'LabelVid.app'
        if app_bundle.exists():
            executable = app_bundle
        else:
            executable = dist_path / 'LabelVid'
    elif platform_name == 'Windows':
        executable = dist_path / 'LabelVid.exe'
    else:  # Linux
        executable = dist_path / 'LabelVid'
    
    if not executable or not executable.exists():
        print(f"❌ Error: Executable not found at {executable}")
        return None
    
    print(f"✓ Found executable: {executable}")
    
    # Create changelog if it doesn't exist
    changelog = create_changelog()
    
    # Files to include
    files_to_include = [
        ('README.md', 'README.md'),
        ('LICENSE', 'LICENSE'),
        (changelog, 'CHANGELOG.md'),
    ]
    
    # Create zip package
    print(f"\nCreating {package_path}...")
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add executable
        if executable.is_dir():  # macOS .app bundle
            for root, dirs, files in os.walk(executable):
                for file in files:
                    file_path = Path(root) / file
                    arcname = str(file_path.relative_to(dist_path.parent))
                    zipf.write(file_path, arcname)
                    print(f"  + {arcname}")
        else:
            arcname = f"{package_name}/{executable.name}"
            zipf.write(executable, arcname)
            print(f"  + {arcname}")
        
        # Add documentation
        for src, dst in files_to_include:
            src_path = Path(src)
            if src_path.exists():
                arcname = f"{package_name}/{dst}"
                zipf.write(src_path, arcname)
                print(f"  + {arcname}")
    
    # Get package size
    size_mb = package_path.stat().st_size / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print(f"✅ Release package created successfully!")
    print(f"   Location: {package_path.absolute()}")
    print(f"   Size: {size_mb:.1f} MB")
    print("=" * 60)
    
    return package_path


def create_github_release(version=None, package_path=None):
    """Create a GitHub release using gh CLI."""
    if version is None:
        version = get_version()
    
    tag = f"v{version}"
    
    # Check if gh CLI is installed
    try:
        subprocess.run(['gh', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ GitHub CLI (gh) is not installed.")
        print("   Install it from: https://cli.github.com/")
        print("\n   macOS:   brew install gh")
        print("   Windows: scoop install gh")
        print("   Linux:   See https://github.com/cli/cli/blob/trunk/docs/install_linux.md")
        return False
    
    # Check if authenticated
    try:
        subprocess.run(['gh', 'auth', 'status'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("\n❌ Not authenticated with GitHub.")
        print("   Run: gh auth login")
        return False
    
    # Create release notes
    changelog_path = Path('CHANGELOG.md')
    release_notes = f"Release {tag}"
    
    if changelog_path.exists():
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract current version section
            lines = content.split('\n')
            capturing = False
            notes = []
            for line in lines:
                if f"[{version}]" in line:
                    capturing = True
                    continue
                if capturing:
                    if line.startswith('## [') and version not in line:
                        break
                    notes.append(line)
            if notes:
                release_notes = '\n'.join(notes).strip()
    
    print(f"\nCreating GitHub release {tag}...")
    print("=" * 60)
    
    # Create release
    cmd = [
        'gh', 'release', 'create', tag,
        '--title', f"LabelVid {tag}",
        '--notes', release_notes,
    ]
    
    # Add package if available
    if package_path and Path(package_path).exists():
        cmd.append(str(package_path))
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("\n✅ GitHub release created successfully!")
        print("=" * 60)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to create GitHub release:")
        print(e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description='Create LabelVid release package')
    parser.add_argument('--version', help='Version number (default: from pyproject.toml)')
    parser.add_argument('--output', default='releases', help='Output directory for packages')
    parser.add_argument('--suffix', help='Package name suffix (e.g., "Full", "Lite")')
    parser.add_argument('--github', action='store_true', help='Create GitHub release')
    parser.add_argument('--build', action='store_true', help='Build executable before packaging')
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    print("LabelVid Release Creator")
    print("=" * 60)
    
    # Build if requested
    if args.build:
        print("\nBuilding executable...")
        result = subprocess.run([sys.executable, 'build_exe.py'])
        if result.returncode != 0:
            print("❌ Build failed!")
            return 1
        print()
    
    # Create package
    package_path = create_release_package(
        version=args.version,
        output_dir=args.output,
        suffix=args.suffix
    )
    
    if not package_path:
        return 1
    
    # Create GitHub release if requested
    if args.github:
        success = create_github_release(
            version=args.version,
            package_path=package_path
        )
        if not success:
            return 1
    
    print("\n📦 Release package ready for distribution!")
    print("\nNext steps:")
    print("  1. Test the package on target platform")
    print("  2. Upload to GitHub Releases")
    print("  3. Update documentation with download links")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
