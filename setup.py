#!/usr/bin/env python3
"""Setup script for pyncode."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pyncode",
    version="1.0.0",
    author="PyNcode Contributors",
    description="Tool for overlaying Ncode patterns and scribbles on PDFs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pyncode",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Printing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pyncode=pyncode.pyncode:main",
        ],
    },
)
