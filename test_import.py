#!/usr/bin/env python3
"""
Simple test to verify pyncode module imports correctly.
"""

import sys

def test_imports():
    """Test that all required modules can be imported."""
    errors = []
    
    # Test PyMuPDF
    try:
        import fitz
        print(f"✓ PyMuPDF imported (version: {fitz.version})")
    except ImportError as e:
        errors.append(f"PyMuPDF: {e}")
        print(f"✗ PyMuPDF import failed: {e}")
    
    # Test Pillow
    try:
        from PIL import Image
        print(f"✓ Pillow imported (version: {Image.__version__})")
    except ImportError as e:
        errors.append(f"Pillow: {e}")
        print(f"✗ Pillow import failed: {e}")
    
    # Test Click
    try:
        import click
        print(f"✓ Click imported (version: {click.__version__})")
    except ImportError as e:
        errors.append(f"Click: {e}")
        print(f"✗ Click import failed: {e}")
    
    # Test pyncode module
    try:
        from pyncode.pyncode import (
            load_ncode_png,
            create_ncoded_pdf,
            overlay_scribbles_simple,
            overlay_scribbles_with_color,
        )
        print("✓ pyncode module imported successfully")
        print("  Available functions:")
        print("    - load_ncode_png")
        print("    - create_ncoded_pdf")
        print("    - overlay_scribbles_simple")
        print("    - overlay_scribbles_with_color")
    except ImportError as e:
        errors.append(f"pyncode: {e}")
        print(f"✗ pyncode import failed: {e}")
    
    # Test CLI
    try:
        from pyncode.pyncode import cli
        print("✓ CLI imported successfully")
    except ImportError as e:
        errors.append(f"CLI: {e}")
        print(f"✗ CLI import failed: {e}")
    
    print()
    if errors:
        print("Summary:")
        for error in errors:
            print(f"  ✗ {error}")
        sys.exit(1)
    else:
        print("All imports successful!")
        sys.exit(0)


if __name__ == '__main__':
    test_imports()
