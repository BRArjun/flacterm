#!/usr/bin/env python3
"""
Setup script for flacterm - A terminal-based FLAC music streaming player.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='flacterm',
    version='1.0.0',
    description='Stream FLAC music from the comfort of your Linux terminal',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='BRArjun',
    author_email='',
    url='https://github.com/BRArjun/flacterm',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'flacterm': ['*.txt', '*.md', '*.json'],
    },
    install_requires=requirements,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'flacterm=flacterm.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Multimedia :: Sound/Audio :: Players',
        'Topic :: Terminals',
    ],
    keywords='music flac terminal tui streaming audio player',
    project_urls={
        'Bug Reports': 'https://github.com/BRArjun/flacterm/issues',
        'Source': 'https://github.com/BRArjun/flacterm',
        'Documentation': 'https://github.com/BRArjun/flacterm#readme',
    },
    zip_safe=False,
)
