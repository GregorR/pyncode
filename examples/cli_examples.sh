#!/bin/bash
# CLI Examples for PyNcode
# Run these examples after installing pyncode

set -e

echo "========================================"
echo "PyNcode CLI Examples"
echo "========================================"

# Create test files directory
TEST_DIR="/tmp/pyncode_test"
mkdir -p "$TEST_DIR"

echo ""
echo "Setting up test files in $TEST_DIR"
echo ""

# Example 1: Ncode overlay
echo "1. Ncode Overlay Example"
echo "   Command: pyncode ncode input.pdf output.pdf ncode_1.png ncode_2.png"
echo "   (Requires actual Ncode PNG files from the SDK)"
echo ""

# Example 2: Scribble overlay with default red color
echo "2. Scribble Overlay (Red, default)"
echo "   Command: pyncode scribble document.pdf scribbles.pdf output.pdf"
echo ""

# Example 3: Scribble overlay with blue color
echo "3. Scribble Overlay (Blue)"
echo "   Command: pyncode scribble document.pdf scribbles.pdf output.pdf --color blue"
echo ""

# Example 4: Scribble overlay with custom RGB color
echo "4. Scribble Overlay (Custom Green)"
echo "   Command: pyncode scribble document.pdf scribbles.pdf output.pdf --color '0,128,0'"
echo ""

# Example 5: Scribble overlay with opacity
echo "5. Scribble Overlay (Semi-transparent)"
echo "   Command: pyncode scribble document.pdf scribbles.pdf output.pdf --color red --opacity 0.7"
echo ""

# Example 6: Simple scribble overlay (faster, no color transform)
echo "6. Simple Scribble Overlay"
echo "   Command: pyncode scribble-simple document.pdf scribbles.pdf output.pdf"
echo ""

echo "========================================"
echo "For more information, see:"
echo "  pyncode --help"
echo "  pyncode ncode --help"
echo "  pyncode scribble --help"
echo "========================================"
