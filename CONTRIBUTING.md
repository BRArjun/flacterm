# Contributing to flacterm

Thank you for your interest in contributing to flacterm! This document provides guidelines and information for contributors.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contributing Process](#contributing-process)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Issue Reporting](#issue-reporting)
9. [Feature Requests](#feature-requests)
10. [Pull Request Guidelines](#pull-request-guidelines)
11. [Release Process](#release-process)
12. [Community](#community)

## Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment for all contributors. By participating, you are expected to uphold this code.

### Our Standards

- **Be respectful**: Treat all community members with respect and kindness
- **Be inclusive**: Welcome newcomers and help them get started
- **Be collaborative**: Work together constructively and share knowledge
- **Be constructive**: Provide helpful feedback and suggestions
- **Be patient**: Remember that everyone has different skill levels and backgrounds

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Spamming or excessive self-promotion
- Sharing private information without consent
- Any behavior that creates an unwelcoming environment

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8 or higher
- Git installed and configured
- VLC media player installed
- A GitHub account
- Basic familiarity with Python and terminal applications

### Areas for Contribution

We welcome contributions in these areas:

- **Bug fixes**: Resolve issues and improve stability
- **New features**: Add functionality that enhances the user experience
- **Documentation**: Improve README, add tutorials, or API documentation
- **Testing**: Add unit tests, integration tests, or manual testing
- **UI/UX improvements**: Enhance the terminal interface
- **Performance optimizations**: Make the application faster and more efficient
- **Platform support**: Add support for additional operating systems
- **Code quality**: Refactor code, improve maintainability

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/yourusername/flacterm.git
cd flacterm
```

### 2. Create Development Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

### 3. Verify Installation

```bash
# Test that the application runs
python main.py

# Test imports
python -c "import main; print('Import successful')"
python -c "from components.audio_player import AudioPlayer; print('AudioPlayer works')"
```

### 4. Set Up Pre-commit Hooks (Optional)

```bash
# Install pre-commit hooks for code quality
pre-commit install
```

## Contributing Process

### 1. Choose an Issue

- Look for issues labeled `good first issue` for beginners
- Check issues labeled `help wanted` for areas needing assistance
- Comment on issues you'd like to work on to avoid duplication

### 2. Create a Branch

```bash
# Create a new branch for your feature/fix
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Write clear, concise code
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes

```bash
# Run basic tests
python -c "import main"
python main.py

# Run code quality checks
black --check .
flake8 .
isort --check-only .
```

### 5. Commit Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add feature: description of what you added"
```

### 6. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a pull request on GitHub
```

## Coding Standards

### Python Code Style

We follow PEP 8 with some modifications:

- **Line length**: Maximum 88 characters (Black's default)
- **Indentation**: 4 spaces
- **Imports**: Sorted with isort
- **Formatting**: Automated with Black
- **Type hints**: Encouraged for new code

### Code Organization

```python
# File structure
"""
Module docstring describing the purpose.
"""

# Standard library imports
import os
import sys
from typing import Optional, List

# Third-party imports
import requests
from rich.console import Console

# Local imports
from components.audio_player import AudioPlayer
from utils.api import fetch_results

# Constants
CONSTANT_NAME = "value"

# Classes and functions
class ExampleClass:
    """Class docstring."""
    
    def __init__(self):
        """Initialize the class."""
        pass
    
    def method_name(self, param: str) -> bool:
        """Method docstring."""
        return True
```

### Documentation Standards

- **Docstrings**: Use Google-style docstrings
- **Comments**: Explain complex logic, not obvious code
- **Type hints**: Add type hints for function parameters and return values
- **README updates**: Update documentation for new features

Example docstring:
```python
def search_tracks(query: str, limit: int = 10) -> List[dict]:
    """
    Search for tracks using the provided query.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of track dictionaries containing metadata
        
    Raises:
        APIError: If the API request fails
        ValueError: If query is empty
    """
```

### Error Handling

```python
# Use specific exceptions
try:
    result = api_call()
except requests.RequestException as e:
    console.print(f"API request failed: {e}")
    return None
except ValueError as e:
    console.print(f"Invalid input: {e}")
    raise
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=components --cov=utils

# Run specific test file
pytest tests/test_audio_player.py
```

### Writing Tests

Create test files in the `tests/` directory:

```python
# tests/test_component.py
import pytest
from components.audio_player import AudioPlayer


class TestAudioPlayer:
    """Test cases for AudioPlayer class."""
    
    def test_initialization(self):
        """Test that AudioPlayer initializes correctly."""
        player = AudioPlayer()
        assert player is not None
        assert not player.is_playing
    
    def test_play_invalid_url(self):
        """Test error handling for invalid URLs."""
        player = AudioPlayer()
        with pytest.raises(ValueError):
            player.play("invalid-url")
```

### Test Coverage

- Aim for at least 80% code coverage
- Test both success and failure cases
- Mock external dependencies (API calls, file system)
- Test edge cases and error conditions

## Documentation

### README Updates

When adding features, update the README.md:

- Add to the features list
- Update installation instructions if needed
- Add new keyboard shortcuts to the keybindings section
- Update screenshots if UI changes significantly

### Code Documentation

- Add docstrings to all public functions and classes
- Update existing docstrings when changing function signatures
- Add inline comments for complex logic
- Keep documentation up to date with code changes

### API Documentation

If you add new API endpoints or modify existing ones:

- Document the API in the relevant module
- Update the API usage examples
- Add any new error codes or responses

## Issue Reporting

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Try the latest version** to see if the issue is already fixed
3. **Check the documentation** to ensure it's actually a bug

### Bug Reports

Include this information:

- **OS and version** (e.g., Ubuntu 22.04)
- **Python version** (e.g., Python 3.10.12)
- **flacterm version** (e.g., 1.0.0)
- **VLC version** (e.g., VLC 3.0.16)
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Error messages** or logs if available
- **Screenshots** if applicable

### Example Bug Report

```markdown
**Bug Description**
Application crashes when trying to play a track.

**Environment**
- OS: Ubuntu 22.04
- Python: 3.10.12
- flacterm: 1.0.0
- VLC: 3.0.16

**Steps to Reproduce**
1. Search for a track
2. Press space to play
3. Application crashes with traceback

**Expected Behavior**
Track should start playing.

**Actual Behavior**
Application crashes with error message: [paste error here]

**Additional Context**
This happens with all tracks, not just specific ones.
```

## Feature Requests

### Guidelines

- **Check existing requests** to avoid duplicates
- **Explain the use case** and why it's valuable
- **Provide examples** of how it would work
- **Consider implementation complexity**

### Feature Request Template

```markdown
**Feature Description**
Brief description of the feature.

**Use Case**
Why would this feature be useful?

**Proposed Implementation**
How could this feature work?

**Alternatives Considered**
What other approaches could solve this problem?

**Additional Context**
Any other relevant information.
```

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

### Pull Request Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Testing
- [ ] Existing tests pass
- [ ] New tests added (if applicable)
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

### Review Process

1. **Automated checks**: GitHub Actions will run tests and code quality checks
2. **Code review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

### After Approval

- Your changes will be merged into the main branch
- You'll be credited in the release notes
- The feature will be included in the next release

## Release Process

### Version Numbers

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Create release notes
- [ ] Tag the release
- [ ] Build and publish packages
- [ ] Update documentation

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussions
- **GitHub Pull Requests**: Code contributions and reviews

### Getting Help

- **Documentation**: Check README.md and DEPLOYMENT.md
- **Issues**: Search existing issues for solutions
- **Discussions**: Ask questions in GitHub Discussions
- **Code**: Look at existing code for examples

### Recognition

Contributors are recognized in:

- **Release notes**: Major contributors mentioned
- **README**: Contributors section
- **Git history**: All commits are preserved
- **GitHub**: Contributor statistics

## Project Maintainers

Current maintainers:

- **BRArjun** - Project creator and lead maintainer

### Becoming a Maintainer

Active contributors who demonstrate:

- Consistent high-quality contributions
- Good understanding of the codebase
- Helpful community participation
- Reliability and responsibility

May be invited to become maintainers.

## License

By contributing to flacterm, you agree that your contributions will be licensed under the same GPL-3.0 license as the project.

## Questions?

If you have questions about contributing, please:

1. Check this document first
2. Search existing issues and discussions
3. Create a new discussion or issue
4. Reach out to the maintainers

Thank you for contributing to flacterm! 🎵