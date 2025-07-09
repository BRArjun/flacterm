"""
flacterm - A terminal-based FLAC music streaming player.

Stream FLAC music from the comfort of your Linux terminal with synchronized lyrics,
queue management, playlist support, and download capabilities.
"""

__version__ = "1.0.0"
__author__ = "BRArjun"
__email__ = ""
__license__ = "GPL-3.0"
__description__ = "Stream FLAC music from the comfort of your Linux terminal"
__url__ = "https://github.com/BRArjun/flacterm"

# Import main components for easier access
from .main import main

# Make main function available at package level
__all__ = ["main", "__version__", "__author__", "__license__", "__description__", "__url__"]
