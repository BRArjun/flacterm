#!/bin/bash
# Installation script for flacterm - A terminal-based FLAC music streaming player

set -e

echo "=========================================="
echo "Installing flacterm..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}Error: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

print_info() {
    echo -e "$1"
}

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "This application is designed for Linux systems only"
    exit 1
fi

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    print_info "Please install Python 3.8 or higher:"
    print_info "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    print_info "  CentOS/RHEL: sudo yum install python3 python3-pip"
    print_info "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    print_info "Please upgrade Python to version 3.8 or higher"
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed"
    print_info "Please install pip3:"
    print_info "  Ubuntu/Debian: sudo apt-get install python3-pip"
    print_info "  CentOS/RHEL: sudo yum install python3-pip"
    print_info "  Arch: sudo pacman -S python-pip"
    exit 1
fi

print_success "pip3 is available"

# Check if VLC is installed
if ! command -v vlc &> /dev/null; then
    print_warning "VLC is not installed. VLC is required for audio playback."
    print_info "Attempting to install VLC..."

    if command -v apt-get &> /dev/null; then
        print_info "Detected Debian/Ubuntu system"
        sudo apt-get update
        sudo apt-get install -y vlc
    elif command -v yum &> /dev/null; then
        print_info "Detected CentOS/RHEL system"
        sudo yum install -y vlc
    elif command -v dnf &> /dev/null; then
        print_info "Detected Fedora system"
        sudo dnf install -y vlc
    elif command -v pacman &> /dev/null; then
        print_info "Detected Arch system"
        sudo pacman -S vlc
    elif command -v zypper &> /dev/null; then
        print_info "Detected openSUSE system"
        sudo zypper install -y vlc
    else
        print_error "Could not detect package manager"
        print_info "Please install VLC manually before running flacterm:"
        print_info "  https://www.videolan.org/vlc/download-linux.html"
        exit 1
    fi

    if command -v vlc &> /dev/null; then
        print_success "VLC installed successfully"
    else
        print_error "VLC installation failed"
        exit 1
    fi
else
    print_success "VLC is already installed"
fi

# Check if git is available (optional, for development install)
if command -v git &> /dev/null; then
    print_success "Git is available"
    GIT_AVAILABLE=true
else
    print_warning "Git is not available. Development installation will not be possible."
    GIT_AVAILABLE=false
fi

# Ask user for installation method
echo ""
print_info "Choose installation method:"
print_info "1) Install from PyPI (recommended)"
if [ "$GIT_AVAILABLE" = true ]; then
    print_info "2) Install from GitHub repository (development version)"
fi
print_info "3) Install from local directory (if you have the source)"

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        print_info "Installing flacterm from PyPI..."
        pip3 install --user flacterm
        ;;
    2)
        if [ "$GIT_AVAILABLE" = false ]; then
            print_error "Git is not available. Please choose option 1 or 3."
            exit 1
        fi
        print_info "Installing flacterm from GitHub repository..."
        # Create temporary directory
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"

        # Clone the repository
        git clone https://github.com/BRArjun/flacterm.git
        cd flacterm

        # Install
        pip3 install --user .

        # Clean up
        cd "$HOME"
        rm -rf "$TEMP_DIR"
        ;;
    3)
        print_info "Installing from local directory..."
        if [ ! -f "setup.py" ] && [ ! -f "pyproject.toml" ]; then
            print_error "setup.py or pyproject.toml not found in current directory"
            print_info "Please run this script from the flacterm source directory"
            exit 1
        fi
        pip3 install --user .
        ;;
    *)
        print_error "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

# Check if installation was successful
if command -v flacterm &> /dev/null; then
    print_success "flacterm installed successfully!"
else
    # Check if it's in the user's local bin directory
    if [ -f "$HOME/.local/bin/flacterm" ]; then
        print_success "flacterm installed successfully!"
        print_warning "The executable is in $HOME/.local/bin/flacterm"

        # Check if ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            print_warning "~/.local/bin is not in your PATH"
            print_info "Add the following line to your ~/.bashrc or ~/.zshrc:"
            print_info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
            print_info "Then run: source ~/.bashrc (or restart your terminal)"
        fi
    else
        print_error "Installation may have failed. Please check the output above."
        exit 1
    fi
fi

echo ""
print_info "=========================================="
print_success "Installation completed successfully!"
print_info "=========================================="
print_info ""
print_info "To run flacterm:"
print_info "  flacterm"
print_info ""
print_info "If the command is not found, try:"
print_info "  ~/.local/bin/flacterm"
print_info ""
print_info "For help and documentation:"
print_info "  https://github.com/BRArjun/flacterm"
print_info ""
print_info "Enjoy your music! 🎵"
