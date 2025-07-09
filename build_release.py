#!/usr/bin/env python3
"""
Build script for flacterm distribution packages.
This script builds source and wheel distributions for PyPI upload.
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def clean_build_directories():
    """Clean build directories."""
    print("Cleaning build directories...")
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for dir_pattern in dirs_to_clean:
        if '*' in dir_pattern:
            # Handle glob patterns
            import glob
            for path in glob.glob(dir_pattern):
                if os.path.exists(path):
                    shutil.rmtree(path)
                    print(f"Removed: {path}")
        else:
            if os.path.exists(dir_pattern):
                shutil.rmtree(dir_pattern)
                print(f"Removed: {dir_pattern}")

def check_dependencies():
    """Check if required build dependencies are installed."""
    print("Checking build dependencies...")
    required_packages = ['setuptools', 'wheel', 'build']

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is not installed")
            print(f"Installing {package}...")
            run_command(f"{sys.executable} -m pip install {package}")

def build_source_distribution():
    """Build source distribution."""
    print("Building source distribution...")
    run_command(f"{sys.executable} setup.py sdist")
    print("✓ Source distribution built")

def build_wheel_distribution():
    """Build wheel distribution."""
    print("Building wheel distribution...")
    run_command(f"{sys.executable} setup.py bdist_wheel")
    print("✓ Wheel distribution built")

def build_with_build_module():
    """Build using the modern build module."""
    print("Building with python -m build...")
    run_command(f"{sys.executable} -m build")
    print("✓ Distributions built with build module")

def verify_distributions():
    """Verify the built distributions."""
    print("Verifying distributions...")

    dist_dir = Path('dist')
    if not dist_dir.exists():
        print("✗ No dist directory found")
        return False

    files = list(dist_dir.glob('*'))
    if not files:
        print("✗ No distribution files found")
        return False

    print("Found distribution files:")
    for file in files:
        print(f"  - {file.name} ({file.stat().st_size} bytes)")

    # Check for both source and wheel distributions
    has_source = any(file.suffix == '.gz' for file in files)
    has_wheel = any(file.suffix == '.whl' for file in files)

    if has_source and has_wheel:
        print("✓ Both source and wheel distributions found")
        return True
    else:
        print("✗ Missing distribution type")
        return False

def create_installation_scripts():
    """Create installation scripts."""
    print("Creating installation scripts...")

    # Create install.sh
    install_sh_content = '''#!/bin/bash
# Installation script for flacterm

set -e

echo "Installing flacterm..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Check if VLC is installed
if ! command -v vlc &> /dev/null; then
    echo "Warning: VLC is not installed. Installing VLC..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y vlc
    elif command -v yum &> /dev/null; then
        sudo yum install -y vlc
    elif command -v pacman &> /dev/null; then
        sudo pacman -S vlc
    else
        echo "Please install VLC manually before running flacterm"
        exit 1
    fi
fi

# Install flacterm
echo "Installing flacterm via pip..."
pip3 install --user flacterm

echo "Installation complete!"
echo "Run 'flacterm' to start the application"
'''

    with open('install.sh', 'w') as f:
        f.write(install_sh_content)

    os.chmod('install.sh', 0o755)
    print("✓ Created install.sh")

    # Create requirements-dev.txt for development
    dev_requirements = '''# Development requirements
build
wheel
setuptools>=45
twine
pytest
black
flake8
mypy
'''

    with open('requirements-dev.txt', 'w') as f:
        f.write(dev_requirements)

    print("✓ Created requirements-dev.txt")

def main():
    """Main build process."""
    print("=" * 50)
    print("Building flacterm distribution packages")
    print("=" * 50)

    # Ensure we're in the correct directory
    if not os.path.exists('main.py'):
        print("Error: This script must be run from the flacterm project root")
        sys.exit(1)

    # Clean previous builds
    clean_build_directories()

    # Check dependencies
    check_dependencies()

    # Create installation scripts
    create_installation_scripts()

    # Build distributions
    try:
        build_with_build_module()
    except:
        print("Modern build failed, falling back to setuptools...")
        build_source_distribution()
        build_wheel_distribution()

    # Verify distributions
    if verify_distributions():
        print("\n" + "=" * 50)
        print("✓ Build completed successfully!")
        print("Distribution files are in the 'dist' directory")
        print("\nTo upload to PyPI (test):")
        print("  python -m twine upload --repository testpypi dist/*")
        print("\nTo upload to PyPI (production):")
        print("  python -m twine upload dist/*")
        print("\nTo install locally:")
        print("  pip install dist/*.whl")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("✗ Build failed!")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
