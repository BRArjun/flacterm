#!/usr/bin/env python3
"""
Release script for flacterm.
Automates the release process including version bumping, building, and publishing.
"""

import os
import sys
import re
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def run_command(cmd, cwd=None, capture_output=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=capture_output, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        if capture_output:
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
        return None
    return result.stdout.strip() if capture_output else ""

def get_current_version():
    """Get the current version from setup.py."""
    try:
        with open('setup.py', 'r') as f:
            content = f.read()
            match = re.search(r"version='([^']+)'", content)
            if match:
                return match.group(1)
    except FileNotFoundError:
        pass

    try:
        with open('pyproject.toml', 'r') as f:
            content = f.read()
            match = re.search(r'version = "([^"]+)"', content)
            if match:
                return match.group(1)
    except FileNotFoundError:
        pass

    return None

def update_version(new_version):
    """Update version in all relevant files."""
    files_to_update = [
        ('setup.py', r"version='[^']+'", f"version='{new_version}'"),
        ('pyproject.toml', r'version = "[^"]+"', f'version = "{new_version}"'),
        ('setup.cfg', r'version = [^\n]+', f'version = {new_version}'),
    ]

    for filepath, pattern, replacement in files_to_update:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()

            updated_content = re.sub(pattern, replacement, content)

            with open(filepath, 'w') as f:
                f.write(updated_content)

            print(f"Updated version in {filepath}")

def increment_version(version, bump_type):
    """Increment version based on bump type."""
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")

    major, minor, patch = map(int, parts)

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"

def check_git_status():
    """Check if git working directory is clean."""
    result = run_command("git status --porcelain")
    if result is None:
        print("Warning: Git not available or not in a git repository")
        return False

    if result.strip():
        print("Git working directory is not clean. Please commit your changes first.")
        print("Uncommitted changes:")
        print(result)
        return False

    return True

def create_git_tag(version):
    """Create a git tag for the version."""
    tag_name = f"v{version}"

    # Check if tag already exists
    result = run_command(f"git tag -l {tag_name}")
    if result and result.strip():
        print(f"Tag {tag_name} already exists")
        return False

    # Create tag
    run_command(f"git tag -a {tag_name} -m 'Release {version}'")
    print(f"Created git tag: {tag_name}")
    return True

def update_changelog(version):
    """Update CHANGELOG.md with the new version."""
    changelog_path = Path('CHANGELOG.md')

    if not changelog_path.exists():
        # Create a new changelog
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

## [{version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- Initial release of flacterm
- Terminal-based FLAC music streaming
- Synchronized lyrics display
- Playlist management
- Queue functionality
- Download capabilities

### Changed
- N/A

### Fixed
- N/A

### Removed
- N/A
"""
    else:
        with open(changelog_path, 'r') as f:
            content = f.read()

        # Insert new version at the top
        new_entry = f"""## [{version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- Release {version}

### Changed
- N/A

### Fixed
- N/A

### Removed
- N/A

"""

        # Find the first ## heading and insert before it
        lines = content.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('## '):
                insert_index = i
                break

        lines.insert(insert_index, new_entry)
        changelog_content = '\n'.join(lines)

    with open(changelog_path, 'w') as f:
        f.write(changelog_content)

    print(f"Updated CHANGELOG.md for version {version}")

def build_package():
    """Build the package."""
    print("Building package...")

    # Clean previous builds
    for dir_name in ['build', 'dist', 'flacterm.egg-info']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name}")

    # Build using modern build module
    result = run_command("python -m build", capture_output=False)
    if result is None:
        print("Build failed")
        return False

    # Verify build artifacts
    if not os.path.exists('dist'):
        print("No dist directory created")
        return False

    dist_files = list(Path('dist').glob('*'))
    if not dist_files:
        print("No distribution files created")
        return False

    print("Build artifacts:")
    for file in dist_files:
        print(f"  - {file.name}")

    return True

def test_package():
    """Test the built package."""
    print("Testing package...")

    # Check with twine
    result = run_command("python -m twine check dist/*")
    if result is None:
        print("Package check failed")
        return False

    print("Package check passed")
    return True

def publish_package(test=False):
    """Publish the package to PyPI."""
    if test:
        print("Publishing to Test PyPI...")
        result = run_command("python -m twine upload --repository testpypi dist/*", capture_output=False)
    else:
        print("Publishing to PyPI...")
        result = run_command("python -m twine upload dist/*", capture_output=False)

    if result is None:
        print("Publishing failed")
        return False

    print("Package published successfully")
    return True

def main():
    """Main release process."""
    print("=" * 60)
    print("flacterm Release Script")
    print("=" * 60)

    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("Error: This script must be run from the flacterm project root")
        sys.exit(1)

    # Get current version
    current_version = get_current_version()
    if not current_version:
        print("Error: Could not determine current version")
        sys.exit(1)

    print(f"Current version: {current_version}")

    # Ask for bump type
    print("\nSelect version bump type:")
    print("1. Patch (x.x.X) - bug fixes")
    print("2. Minor (x.X.x) - new features")
    print("3. Major (X.x.x) - breaking changes")
    print("4. Custom version")

    choice = input("Enter your choice (1-4): ").strip()

    if choice == '1':
        new_version = increment_version(current_version, 'patch')
    elif choice == '2':
        new_version = increment_version(current_version, 'minor')
    elif choice == '3':
        new_version = increment_version(current_version, 'major')
    elif choice == '4':
        new_version = input("Enter custom version: ").strip()
    else:
        print("Invalid choice")
        sys.exit(1)

    print(f"New version: {new_version}")

    # Confirm
    confirm = input(f"Release version {new_version}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Release cancelled")
        sys.exit(0)

    # Check git status
    if not check_git_status():
        print("Please resolve git issues before releasing")
        sys.exit(1)

    # Update version in files
    update_version(new_version)

    # Update changelog
    update_changelog(new_version)

    # Commit version changes
    run_command("git add .")
    run_command(f"git commit -m 'Bump version to {new_version}'")

    # Create git tag
    if not create_git_tag(new_version):
        print("Failed to create git tag")
        sys.exit(1)

    # Build package
    if not build_package():
        print("Build failed")
        sys.exit(1)

    # Test package
    if not test_package():
        print("Package test failed")
        sys.exit(1)

    # Ask about publishing
    print("\nPublishing options:")
    print("1. Publish to Test PyPI (recommended first)")
    print("2. Publish to PyPI")
    print("3. Skip publishing")

    publish_choice = input("Enter your choice (1-3): ").strip()

    if publish_choice == '1':
        if publish_package(test=True):
            print(f"\nTest release successful!")
            print(f"Test with: pip install -i https://test.pypi.org/simple/ flacterm=={new_version}")
        else:
            print("Test publishing failed")
            sys.exit(1)
    elif publish_choice == '2':
        if publish_package(test=False):
            print(f"\nProduction release successful!")
            print(f"Install with: pip install flacterm=={new_version}")
        else:
            print("Publishing failed")
            sys.exit(1)
    elif publish_choice == '3':
        print("Skipping publishing")
    else:
        print("Invalid choice, skipping publishing")

    # Push to git
    push_git = input("Push changes and tags to git remote? (y/N): ").strip().lower()
    if push_git == 'y':
        run_command("git push")
        run_command("git push --tags")
        print("Pushed to git remote")

    print("\n" + "=" * 60)
    print(f"Release {new_version} completed successfully!")
    print("=" * 60)

    print("\nNext steps:")
    print("1. Create release notes on GitHub")
    print("2. Update documentation if needed")
    print("3. Announce the release")

if __name__ == "__main__":
    main()
