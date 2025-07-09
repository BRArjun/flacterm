# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [1.0.0] - 2025-01-27

### Added
- Initial release of flacterm
- Terminal-based FLAC music streaming player
- Search functionality for tracks using DAB API
- High-quality audio playback using VLC
- Synchronized lyrics display with real-time highlighting
- Comprehensive keyboard shortcuts for navigation
- Track information display with metadata
- Playback controls (play, pause, stop, seek)
- Queue management system
- Playlist creation and management
- Track download functionality
- Repeat mode support
- Cross-platform packaging for easy distribution
- Automated installation script
- PyPI package distribution
- GitHub Actions CI/CD pipeline
- Comprehensive documentation

### Features
- **Audio Streaming**: Stream FLAC files directly from the terminal
- **Lyrics Support**: Real-time synchronized lyrics display
- **Queue System**: Add tracks to queue, manage playback order
- **Playlists**: Create, manage, and play custom playlists
- **Downloads**: Download tracks for offline listening
- **Keyboard Navigation**: Intuitive keyboard shortcuts
- **Track Info**: Detailed track metadata and information
- **Search**: Powerful search functionality
- **Repeat Mode**: Loop tracks or playlists

### Technical
- Python 3.8+ compatibility
- VLC media player integration
- Textual TUI framework
- Rich text rendering
- RESTful API integration
- Modular component architecture
- Comprehensive error handling
- Thread-safe audio playback
- Memory-efficient streaming

### Documentation
- Comprehensive README with installation instructions
- Detailed deployment guide
- Contributing guidelines
- API documentation
- Keyboard shortcuts reference
- Troubleshooting guide

### Packaging
- PyPI distribution
- Automated build scripts
- GitHub Actions workflows
- Installation scripts for multiple Linux distributions
- Source and wheel distributions
- Dependency management

## [0.1.0] - Development

### Added
- Basic project structure
- Core components development
- Initial API integration
- Basic UI implementation
- Audio playback functionality
- Search capabilities

---

## Release Notes

### Version 1.0.0

This is the initial stable release of flacterm, a terminal-based FLAC music streaming player. The application provides a complete music streaming experience from the command line with high-quality audio playback, synchronized lyrics, and comprehensive music management features.

**Key Highlights:**
- Stream FLAC music directly in your terminal
- Real-time synchronized lyrics
- Queue and playlist management
- Download functionality
- Intuitive keyboard navigation
- Cross-platform Linux support

**Installation:**
```bash
pip install flacterm
```

**Quick Start:**
```bash
flacterm
```

**System Requirements:**
- Python 3.8 or higher
- VLC media player
- Linux operating system

**Known Issues:**
- Windows compatibility not tested
- macOS compatibility not tested
- Some VLC error messages may appear during abrupt song stops

**Future Plans:**
- UI improvements
- Performance optimizations
- Additional platform support
- Enhanced playlist features
- YouTube Music playlist import

For detailed installation instructions, usage guide, and troubleshooting, please refer to the [README.md](README.md) and [DEPLOYMENT.md](DEPLOYMENT.md) files.