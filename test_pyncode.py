#!/usr/bin/env python3
"""Tests for pyncode module."""

import os
import tempfile
import pytest
from pathlib import Path

import fitz
from PIL import Image

from pyncode import (
    load_ncode_png,
    create_ncoded_pdf,
    overlay_scribbles_simple,
    overlay_scribbles_with_color,
)


def create_test_pdf(num_pages=3, size=(595, 842)):
    """Create a simple test PDF with text content."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=size[0], height=size[1])
        # Add some text that should remain selectable
        page.insert_text(
            (50, 50 + i * 50),
            f"This is page {i+1} of the test PDF. Text should be selectable.",
            fontsize=12
        )
        # Add a title
        page.insert_text(
            (50, 30),
            f"Test Page {i+1}",
            fontsize=16,
            fontname="helv",
            color=(0, 0, 0)
        )
    return doc


def create_test_ncode_png(path, size=(100, 100)):
    """Create a simple test Ncode PNG (black dots on white)."""
    img = Image.new('1', size, 1)  # 1 = white (background)
    
    # Add some black dots (0 = dot)
    for y in range(0, size[1], 20):
        for x in range(0, size[0], 20):
            img.putpixel((x, y), 0)
    
    img.save(path, 'PNG')
    return path


def create_test_scribble_pdf(num_pages=3, size=(595, 842)):
    """Create a test scribble PDF with some 'handwriting' (rectangles)."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=size[0], height=size[1])
        # Draw some rectangles to simulate handwriting
        page.draw_rect(
            fitz.Rect(100 + i * 10, 100 + i * 10, 300 + i * 10, 200 + i * 10),
            color=(0, 0, 0),  # Black
            fill=(0, 0, 0),
            width=2
        )
    return doc


class TestLoadNcodePng:
    """Tests for load_ncode_png function."""
    
    def test_load_basic_png(self, tmp_path):
        """Test loading a basic PNG file."""
        png_path = tmp_path / "test.png"
        create_test_ncode_png(str(png_path))
        
        tiff_data, width, height = load_ncode_png(str(png_path))
        
        assert len(tiff_data) > 0
        assert width == 100
        assert height == 100
        assert isinstance(tiff_data, bytes)
    
    def test_load_conversion_to_1bit(self, tmp_path):
        """Test that grayscale PNG is converted to 1-bit."""
        png_path = tmp_path / "test_gray.png"
        
        # Create grayscale PNG
        img = Image.new('L', (50, 50), 128)
        img.save(png_path)
        
        tiff_data, width, height = load_ncode_png(str(png_path))
        
        assert len(tiff_data) > 0
        assert width == 50
        assert height == 50


class TestCreateNcodedPdf:
    """Tests for create_ncoded_pdf function."""
    
    def test_basic_ncode_overlay(self, tmp_path):
        """Test basic Ncode overlay on a PDF."""
        # Create test PDF
        doc = create_test_pdf(num_pages=2)
        pdf_path = tmp_path / "test.pdf"
        doc.save(str(pdf_path))
        doc.close()
        
        # Create Ncode PNGs
        ncode_pdfs = []
        for i in range(2):
            png_path = tmp_path / f"ncode_{i}.png"
            create_test_ncode_png(str(png_path), size=(200, 200))
            ncode_pdfs.append(str(png_path))
        
        # Overlay Ncode
        output_path = tmp_path / "output.pdf"
        pages = create_ncoded_pdf(str(pdf_path), ncode_pdfs, str(output_path))
        
        assert pages == 2
        assert output_path.exists()
        
        # Verify output PDF has content
        output_doc = fitz.open(str(output_path))
        assert len(output_doc) == 2
        # Check that original text is still there
        page_text = output_doc[0].get_text()
        assert "page 1" in page_text.lower()
        output_doc.close()
    
    def test_page_count_mismatch(self, tmp_path):
        """Test that page count mismatch raises ValueError."""
        doc = create_test_pdf(num_pages=3)
        pdf_path = tmp_path / "test.pdf"
        doc.save(str(pdf_path))
        doc.close()
        
        # Create only 2 Ncode PNGs
        ncode_pdfs = []
        for i in range(2):
            png_path = tmp_path / f"ncode_{i}.png"
            create_test_ncode_png(str(png_path))
            ncode_pdfs.append(str(png_path))
        
        output_path = tmp_path / "output.pdf"
        
        with pytest.raises(ValueError, match="Page count mismatch"):
            create_ncoded_pdf(str(pdf_path), ncode_pdfs, str(output_path))
    
    def test_missing_input_pdf(self, tmp_path):
        """Test that missing input PDF raises FileNotFoundError."""
        ncode_pdfs = [str(tmp_path / "ncode.png")]
        
        with pytest.raises(FileNotFoundError):
            create_ncoded_pdf(
                str(tmp_path / "nonexistent.pdf"),
                ncode_pdfs,
                str(tmp_path / "output.pdf")
            )


class TestOverlayScribblesSimple:
    """Tests for overlay_scribbles_simple function."""
    
    def test_basic_scribble_overlay(self, tmp_path):
        """Test basic scribble overlay."""
        # Create background PDF
        bg_doc = create_test_pdf(num_pages=2)
        bg_path = tmp_path / "background.pdf"
        bg_doc.save(str(bg_path))
        bg_doc.close()
        
        # Create scribble PDF
        scribble_doc = create_test_scribble_pdf(num_pages=2)
        scribble_path = tmp_path / "scribbles.pdf"
        scribble_doc.save(str(scribble_path))
        scribble_doc.close()
        
        # Overlay scribbles
        output_path = tmp_path / "output.pdf"
        pages = overlay_scribbles_simple(
            str(bg_path),
            str(scribble_path),
            str(output_path)
        )
        
        assert pages == 2
        assert output_path.exists()
        
        # Verify background text is still selectable
        output_doc = fitz.open(str(output_path))
        page_text = output_doc[0].get_text()
        assert "page 1" in page_text.lower()
        output_doc.close()
    
    def test_opacity_parameter(self, tmp_path):
        """Test that opacity parameter is accepted."""
        bg_doc = create_test_pdf(num_pages=1)
        bg_path = tmp_path / "background.pdf"
        bg_doc.save(str(bg_path))
        bg_doc.close()
        
        scribble_doc = create_test_scribble_pdf(num_pages=1)
        scribble_path = tmp_path / "scribbles.pdf"
        scribble_doc.save(str(scribble_path))
        scribble_doc.close()
        
        output_path = tmp_path / "output.pdf"
        pages = overlay_scribbles_simple(
            str(bg_path),
            str(scribble_path),
            str(output_path),
            scribble_opacity=0.5
        )
        
        assert pages == 1
        assert output_path.exists()


class TestOverlayScribblesWithColor:
    """Tests for overlay_scribbles_with_color function."""
    
    def test_color_red(self, tmp_path):
        """Test scribble overlay with red color."""
        bg_doc = create_test_pdf(num_pages=1)
        bg_path = tmp_path / "background.pdf"
        bg_doc.save(str(bg_path))
        bg_doc.close()
        
        scribble_doc = create_test_scribble_pdf(num_pages=1)
        scribble_path = tmp_path / "scribbles.pdf"
        scribble_doc.save(str(scribble_path))
        scribble_doc.close()
        
        output_path = tmp_path / "output.pdf"
        pages = overlay_scribbles_with_color(
            str(bg_path),
            str(scribble_path),
            str(output_path),
            scribble_color=(1.0, 0.0, 0.0)  # Red
        )
        
        assert pages == 1
        assert output_path.exists()
    
    def test_color_blue(self, tmp_path):
        """Test scribble overlay with blue color."""
        bg_doc = create_test_pdf(num_pages=1)
        bg_path = tmp_path / "background.pdf"
        bg_doc.save(str(bg_path))
        bg_doc.close()
        
        scribble_doc = create_test_scribble_pdf(num_pages=1)
        scribble_path = tmp_path / "scribbles.pdf"
        scribble_doc.save(str(scribble_path))
        scribble_doc.close()
        
        output_path = tmp_path / "output.pdf"
        pages = overlay_scribbles_with_color(
            str(bg_path),
            str(scribble_path),
            str(output_path),
            scribble_color=(0.0, 0.0, 1.0)  # Blue
        )
        
        assert pages == 1
        assert output_path.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
