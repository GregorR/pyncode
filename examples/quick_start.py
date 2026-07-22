#!/usr/bin/env python3
"""
Quick Start Example for PyNcode

This example demonstrates:
1. Creating a simple PDF with text
2. Generating fake Ncode pattern PNGs
3. Overlaying Ncode patterns on the PDF
4. Creating fake scribble PDFs
5. Overlaying scribbles with custom colors
"""

import os
import tempfile
from pathlib import Path

# For this example, we'll create fake Ncode PNGs and scribbles
# In real usage, you'd get these from the Ncode SDK and smartpen

import fitz  # PyMuPDF
from PIL import Image


def create_sample_pdf(num_pages=3):
    """Create a sample PDF with selectable text."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        # Add some text
        page.insert_text(
            (50, 50),
            f"This is sample page {i+1}.",
            fontsize=18
        )
        page.insert_text(
            (50, 80),
            "The text on this page should remain selectable after Ncode overlay.",
            fontsize=12
        )
        page.insert_text(
            (50, 120),
            f"Additional content for page {i+1} to make it more interesting.",
            fontsize=12
        )
    return doc


def create_fake_ncode_png(output_path, width=1276, height=1650):
    """
    Create a fake Ncode PNG pattern.
    
    In reality, you would generate these using the official Ncode SDK
    or the Go SDK. This function creates a simple dot pattern for demo purposes.
    
    Note: This is NOT a real Ncode pattern - the Neo smartpen won't recognize it!
    """
    img = Image.new('1', (width, height), 1)  # White background
    
    # Create a pattern of dots (similar to Ncode)
    # Real Ncode has a specific encoding pattern
    for y in range(0, height, 10):
        for x in range(0, width, 10):
            # Create a pattern with some dots
            if (x + y) % 20 == 0:
                img.putpixel((x, y), 0)  # Black dot
    
    img.save(output_path, 'PNG')
    return output_path


def create_scribble_pdf(num_pages=3):
    """
    Create a scribble PDF with fake handwriting.
    
    In reality, this would come from your Neo smartpen app.
    """
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        # Draw some fake handwriting (red lines)
        points = [
            (100, 200),
            (150, 210),
            (200, 200),
            (250, 210),
            (300, 200)
        ]
        page.draw_line(points[0], points[1], color=(0.5, 0.5, 0.5), width=3)
        page.draw_line(points[1], points[2], color=(0.5, 0.5, 0.5), width=3)
        page.draw_line(points[2], points[3], color=(0.5, 0.5, 0.5), width=3)
        page.draw_line(points[3], points[4], color=(0.5, 0.5, 0.5), width=3)
        
        # Add some more "handwritten" notes
        page.insert_text(
            (100, 250),
            f"Note from page {i+1}",
            fontsize=14,
            color=(0.3, 0.3, 0.3)
        )
    return doc


def main():
    """Run the quick start example."""
    print("=" * 60)
    print("PyNcode Quick Start Example")
    print("=" * 60)
    
    # Create a temporary directory for our files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        print(f"\nWorking in: {tmpdir}\n")
        
        # Step 1: Create a sample PDF
        print("1. Creating sample PDF...")
        sample_pdf = tmpdir / "sample.pdf"
        doc = create_sample_pdf(num_pages=3)
        doc.save(str(sample_pdf))
        doc.close()
        print(f"   Created: {sample_pdf}")
        
        # Step 2: Create fake Ncode PNGs
        print("\n2. Creating fake Ncode PNGs...")
        ncode_pngs = []
        for i in range(3):
            png_path = tmpdir / f"ncode_page{i+1}.png"
            create_fake_ncode_png(str(png_path))
            ncode_pngs.append(str(png_path))
            print(f"   Created: {png_path}")
        
        # Step 3: Overlay Ncode on the PDF
        print("\n3. Overlaying Ncode patterns...")
        from pyncode import create_ncoded_pdf
        
        ncoded_pdf = tmpdir / "ncoded.pdf"
        pages = create_ncoded_pdf(
            str(sample_pdf),
            ncode_pngs,
            str(ncoded_pdf)
        )
        print(f"   Created: {ncoded_pdf}")
        print(f"   Processed {pages} pages")
        
        # Step 4: Create scribble PDF
        print("\n4. Creating scribble PDF...")
        scribbles = tmpdir / "scribbles.pdf"
        scribble_doc = create_scribble_pdf(num_pages=3)
        scribble_doc.save(str(scribbles))
        scribble_doc.close()
        print(f"   Created: {scribbles}")
        
        # Step 5: Overlay scribbles with red color
        print("\n5. Overlaying scribbles (red)...")
        from pyncode import overlay_scribbles_with_color
        
        annotated_pdf = tmpdir / "annotated.pdf"
        pages = overlay_scribbles_with_color(
            str(sample_pdf),  # Use original, not ncoded
            str(scribbles),
            str(annotated_pdf),
            scribble_color=(1.0, 0.0, 0.0),  # Red
            scribble_opacity=0.8
        )
        print(f"   Created: {annotated_pdf}")
        print(f"   Processed {pages} pages")
        
        # Step 6: Create another version with blue scribbles
        print("\n6. Creating another version (blue scribbles)...")
        annotated_blue = tmpdir / "annotated_blue.pdf"
        pages = overlay_scribbles_with_color(
            str(sample_pdf),
            str(scribbles),
            str(annotated_blue),
            scribble_color=(0.0, 0.0, 1.0),  # Blue
            scribble_opacity=1.0
        )
        print(f"   Created: {annotated_blue}")
        
        # Summary
        print("\n" + "=" * 60)
        print("Files created:")
        for f in tmpdir.glob("*.pdf"):
            size = f.stat().st_size
            print(f"  - {f.name}: {size:,} bytes")
        print("\n" + "=" * 60)
        print("\nNote: The fake Ncode patterns in this example are NOT real.")
        print("The Neo smartpen won't recognize them. For real Ncode, use the")
        print("official Ncode SDK or the Go SDK (Ncode-SDK-for-Linux).")
        print("\nTo use with real Ncode patterns:")
        print("  pyncode ncode input.pdf output.pdf ncode_1.png ncode_2.png ...")
        print("\nTo overlay real scribbles:")
        print("  pyncode scribble document.pdf scribbles.pdf output.pdf --color red")


if __name__ == '__main__':
    main()
