#!/usr/bin/env python3
"""
PyNcode - A Python tool for overlaying Ncode patterns and scribbles on PDFs.

This tool provides two main functions:
1. Overlay Ncode patterns (as PNG images) on PDFs - uses full CMYK conversion with K=0
2. Overlay scribble PDFs (smartpen handwriting) on original PDFs with color control

Based on the NeoLAB Ncode SDK principles:
- Ncode overlay: Rasterizes PDF to CMYK, sets K=0 everywhere except Ncode dots (K=255)
- Scribble overlay: Preserves PDF structure, adds image overlays
"""

import os
import sys
import tempfile
import shutil
import glob
from pathlib import Path
from typing import Optional, Tuple, Union, List
import io

import fitz  # PyMuPDF
from PIL import Image
import click


def find_ncode_pngs(prefix: str, num_pages: int) -> List[str]:
    """
    Find Ncode PNG files matching a prefix pattern.
    
    Looks for files named like: prefix0.png, prefix1.png, prefix2.png, etc.
    
    Args:
        prefix: The file prefix (e.g., 'ncode_3_28_10_' for ncode_3_28_10_0.png)
        num_pages: Number of pages to find PNGs for
        
    Returns:
        List of PNG file paths in order
    """
    png_files = []
    for i in range(num_pages):
        png_path = f"{prefix}{i}.png"
        if os.path.exists(png_path):
            png_files.append(png_path)
        else:
            # Try with different extensions
            for ext in ['.png', '.PNG']:
                alt_path = f"{prefix}{i}{ext}"
                if os.path.exists(alt_path):
                    png_files.append(alt_path)
                    break
    
    return png_files


def create_ncoded_pdf(
    input_pdf: str,
    ncode_pngs: Union[List[str], str],
    output_pdf: str,
    dpi: int = 600,
    ncode_dpi: int = 600,
    auto_detect: bool = True
) -> int:
    """
    Overlay Ncode patterns (PNG images) on a PDF using the full CMYK K-removal approach.
    
    This follows the original NeoLAB Ncode SDK approach:
    1. Rasterize each PDF page to a CMYK pixmap at the specified DPI
    2. For each pixel:
       - If Ncode dot: Set CMYK = (0, 0, 0, 255) - pure black (K only)
       - If not dot: Set CMYK = (255-R, 255-G, 255-Y, 0) - no K component
    3. Save as PDF with the Ncode dots clearly distinguishable for the pen
    
    IMPORTANT: This process rasterizes the PDF, so text will NOT remain selectable.
    This is required for proper Ncode pen detection - the pen needs to distinguish
    the Ncode dots (K=255) from the background (K=0).
    
    Args:
        input_pdf: Path to the input PDF
        ncode_pngs: Either a list of PNG paths OR a prefix string for auto-detection
                   If a prefix, looks for prefix0.png, prefix1.png, etc.
        output_pdf: Path to the output PDF
        dpi: DPI for rendering (default: 600, matches Ncode standard)
        ncode_dpi: DPI of the Ncode PNG images (default: 600)
        auto_detect: If True and ncode_pngs is a string, auto-detect PNG files
        
    Returns:
        Number of pages processed
        
    Raises:
        ValueError: If page counts don't match
        FileNotFoundError: If input files don't exist
    """
    input_path = Path(input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")
    
    # Open the input PDF to get page count
    doc = fitz.open(input_pdf)
    page_count = len(doc)
    doc.close()
    
    # Handle ncode_pngs parameter
    if isinstance(ncode_pngs, str):
        # It's a prefix - auto-detect PNG files
        if auto_detect:
            ncode_pngs_list = find_ncode_pngs(ncode_pngs, page_count)
            if len(ncode_pngs_list) < page_count:
                raise ValueError(
                    f"Only found {len(ncode_pngs_list)} Ncode PNGs for {page_count} pages. "
                    f"Looking for: {ncode_pngs}0.png, {ncode_pngs}1.png, ..."
                )
        else:
            raise ValueError("ncode_pngs must be a list when auto_detect=False")
    else:
        ncode_pngs_list = list(ncode_pngs)
    
    # Verify all Ncode PNGs exist
    for png_path in ncode_pngs_list:
        if not Path(png_path).exists():
            raise FileNotFoundError(f"Ncode PNG not found: {png_path}")
    
    if len(ncode_pngs_list) != page_count:
        raise ValueError(
            f"Page count mismatch: PDF has {page_count} pages, "
            f"but {len(ncode_pngs_list)} Ncode PNGs provided"
        )
    
    # Open MuPDF context and create output document
    ctx = fitz.open()
    
    for page_num in range(page_count):
        print(f"{page_num+1}/{page_count}")

        # Load source page
        src_doc = fitz.open(input_pdf)
        src_page = src_doc[page_num]
        
        # Get page dimensions in points
        page_rect = src_page.rect
        page_width_pt = page_rect.width
        page_height_pt = page_rect.height
        
        # Calculate scale: dpi / 72 (PDF is 72 DPI, we render at specified DPI)
        scale = dpi / 72.0
        
        # Render page to RGB pixmap at the specified DPI
        mat = fitz.Matrix(scale, scale)
        pix_rgb = src_page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        
        width = pix_rgb.width
        height = pix_rgb.height
        
        # Load the Ncode PNG
        png_path = ncode_pngs_list[page_num]
        ncode_img = Image.open(png_path)
        
        # Convert Ncode to 1-bit if needed
        if ncode_img.mode != '1':
            ncode_img = ncode_img.convert('L')
            ncode_img = ncode_img.point(lambda x: 0 if x < 128 else 255, mode='1')
        
        ncode_width, ncode_height = ncode_img.size
        
        # Convert RGB pixmap to CMYK by creating new Pixmap with CMYK colorspace
        pix_cmyk = fitz.Pixmap(fitz.csCMYK, pix_rgb)
        
        # Now modify the CMYK pixmap: set K=255 for dots, K=0 for background
        # Access the raw samples data
        samples = bytearray(pix_cmyk.samples)
        
        for y in range(height):
            for x in range(width):
                # Check if this pixel is an Ncode dot
                # Scale coordinates to match Ncode image size
                nx = int(x * ncode_width / width) if width > 0 else 0
                ny = int(y * ncode_height / height) if height > 0 else 0
                
                # Check Ncode image (0 = dot, 255 = background)
                is_dot = False
                if nx < ncode_width and ny < ncode_height:
                    ncode_pixel = ncode_img.getpixel((nx, ny))
                    is_dot = (ncode_pixel == 0)
                
                if is_dot:
                    # Ncode dot: pure black (K only) - C=0, M=0, Y=0, K=255
                    idx = (y * width + x) * 4
                    samples[idx] = 0     # C
                    samples[idx + 1] = 0  # M
                    samples[idx + 2] = 0  # Y
                    samples[idx + 3] = 255  # K
                else:
                    # Background: set K=0 (inverted RGB is already in C, M, Y)
                    idx = (y * width + x) * 4
                    samples[idx + 3] = 0  # K = 0
        
        # Create new pixmap from modified samples
        # Copy the modified samples back to a new pixmap
        # We need to create a new pixmap with the same dimensions and copy samples
        
        # Create a new CMYK pixmap from modified samples
        # Constructor: Pixmap(colorspace, width, height, samples, alpha)
        pix_final = fitz.Pixmap(fitz.csCMYK, width, height, bytes(samples), False)
        
        # Save as PAM bytes (lossless format that supports CMYK)
        # PAM is supported by PDF and preserves the exact CMYK values
        img_data = pix_final.tobytes("pam")
        
        # Create a new page with the same dimensions
        new_page = ctx.new_page(width=page_width_pt, height=page_height_pt)
        
        # Insert the CMYK image to fill the page
        rect = fitz.Rect(0, 0, page_width_pt, page_height_pt)
        new_page.insert_image(rect, stream=img_data)
        
        src_doc.close()
    
    # Save the output PDF
    ctx.save(output_pdf, garbage=4, deflate=True, clean=True)
    ctx.close()
    
    return page_count


def overlay_scribbles_simple(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    scribble_color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
    scribble_opacity: float = 1.0,
    page_map: Optional[str] = None,
    all_pages: bool = False
) -> int:
    """
    Simple scribble overlay using image insertion.
    
    This is a more reliable approach that works well for smartpen scribbles,
    which are typically already rasterized.
    
    Args:
        background_pdf: Path to the background PDF
        scribble_pdf: Path to the scribble PDF
        output_pdf: Path to the output PDF
        scribble_color: Target RGB color (0.0-1.0 range)
        scribble_opacity: Opacity (0.0-1.0)
        page_map: Optional string specifying which original pages to overlay.
                 Format: "1,3-5,7" - same as overlay_scribbles_with_color
        
    Returns:
        Number of pages processed
    """
    bg_doc = fitz.open(background_pdf)
    scribble_doc = fitz.open(scribble_pdf)
    
    bg_page_count = len(bg_doc)
    scribble_page_count = len(scribble_doc)
    
    # Determine page mapping and what to export
    if page_map is not None:
        # Use explicit page mapping
        target_pages = parse_page_list(page_map, bg_page_count)
        if len(target_pages) != scribble_page_count:
            raise ValueError(
                f"Page map specifies {len(target_pages)} pages but scribble PDF has {scribble_page_count} pages"
            )
        export_pages = target_pages
    elif all_pages:
        # Export all pages from background PDF
        export_pages = list(range(bg_page_count))
        if scribble_page_count > bg_page_count:
            raise ValueError(
                f"Scribble PDF has {scribble_page_count} pages but background has {bg_page_count} pages"
            )
    else:
        # Default: only export pages that have scribbles (trimmed output)
        export_pages = list(range(scribble_page_count))
        if scribble_page_count > bg_page_count:
            raise ValueError(
                f"Scribble PDF has {scribble_page_count} pages but background has {bg_page_count} pages"
            )
    
    if len(export_pages) == 0:
        raise ValueError("No pages to process")
    
    # Create output document
    output_doc = fitz.open()
    
    for scribble_idx, bg_page_num in enumerate(export_pages):
        bg_page = bg_doc[bg_page_num]
        
        # Get the corresponding scribble page (if it exists)
        if scribble_idx < scribble_page_count:
            scribble_page = scribble_doc[scribble_idx]
        else:
            scribble_page = None  # No scribble for this page
        
        # Copy background page to output
        output_doc.insert_pdf(bg_doc, from_page=bg_page_num, to_page=bg_page_num)
        output_page = output_doc[-1]
        
        # Only overlay if we have a scribble page
        if scribble_page is not None:
            # Render scribble page to pixmap (preserves alpha channel)
            zoom = 2.0
            pix = scribble_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
            
            # Apply opacity to alpha channel
            if scribble_opacity < 1.0:
                samples = bytearray(pix.samples)
                # For RGBA pixmap, alpha is at indices 3, 7, 11, ...
                if pix.n == 4:  # RGBA
                    for i in range(3, len(samples), 4):
                        samples[i] = int(samples[i] * scribble_opacity)
                pix = fitz.Pixmap(pix.colorspace, pix.width, pix.height, bytes(samples), True)
            
            # Convert to bytes
            img_bytes = pix.tobytes("png")
            
            # Create image insertion rectangle
            scribble_rect = scribble_page.rect
            rect = fitz.Rect(0, 0, scribble_rect.width, scribble_rect.height)
            
            # Insert image as overlay (opacity handled in pixmap)
            output_page.insert_image(
                rect,
                stream=img_bytes,
                overlay=True
            )
    
    # Save output document
    output_doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    output_doc.close()
    bg_doc.close()
    scribble_doc.close()
    
    return len(export_pages)


def parse_page_list(page_list_str: str, max_pages: int) -> List[int]:
    """
    Parse a page list string into a list of page numbers.
    
    Args:
        page_list_str: String like "1,3-5,7,11,48-" representing page ranges
                      - Single numbers: "1", "7", "11"
                      - Ranges: "3-5" means 3, 4, 5
                      - Open-ended: "48-" means 48 to max_pages
        max_pages: Maximum page number (for open-ended ranges)
    
    Returns:
        List of 0-indexed page numbers in order
    
    Examples:
        parse_page_list("1,3-5,7", 10) -> [0, 2, 3, 4, 6]
        parse_page_list("1,3-5,7,11,48-", 100) -> [0, 2, 3, 4, 6, 10, 47, 48, ..., 99]
    """
    pages = []
    parts = page_list_str.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if '-' in part:
            # Range
            range_parts = part.split('-', 1)
            start_str = range_parts[0].strip()
            end_str = range_parts[1].strip() if len(range_parts) > 1 else None
            
            if not start_str:
                raise ValueError(f"Invalid range: '{part}'")
            
            start = int(start_str)
            if start < 1:
                raise ValueError(f"Page numbers must be >= 1, got {start}")
            
            if end_str is None or end_str == '':
                # Open-ended range (e.g., "48-")
                end = max_pages
            else:
                end = int(end_str)
            
            if end < start:
                raise ValueError(f"Invalid range: {start}-{end}")
            if end > max_pages:
                end = max_pages
            
            pages.extend(range(start, end + 1))
        else:
            # Single page
            page_num = int(part)
            if page_num < 1:
                raise ValueError(f"Page numbers must be >= 1, got {page_num}")
            pages.append(page_num)
    
    # Convert to 0-indexed
    return [p - 1 for p in pages]


def overlay_scribbles_with_color(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    scribble_color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
    scribble_opacity: float = 1.0,
    page_map: Optional[str] = None,
    all_pages: bool = False
) -> int:
    """
    Overlay scribbles with color transformation.
    
    This function converts the scribbles to the specified color during rendering.
    It works by rendering the scribble page, applying a color matrix, and then
    overlaying the result on the background PDF.
    
    Args:
        background_pdf: Path to the background PDF
        scribble_pdf: Path to the scribble PDF
        output_pdf: Path to the output PDF
        scribble_color: Target RGB color (0.0-1.0 range, default: red)
        scribble_opacity: Opacity (0.0-1.0, default: 1.0)
        page_map: Optional string specifying which original pages to overlay.
                 Format: "1,3-5,7,11,48-" where numbers are 1-indexed original page numbers.
                 Scribble pages are mapped in order to these original pages.
                 Example: "1,3-5,7" with 5 scribble pages means:
                 - Scribble page 1 -> Original page 1
                 - Scribble page 2 -> Original page 3
                 - Scribble page 3 -> Original page 4
                 - Scribble page 4 -> Original page 5
                 - Scribble page 5 -> Original page 7
        
    Returns:
        Number of pages processed
    """
    bg_doc = fitz.open(background_pdf)
    scribble_doc = fitz.open(scribble_pdf)
    
    bg_page_count = len(bg_doc)
    scribble_page_count = len(scribble_doc)
    
    # Determine page mapping and what to export
    if page_map is not None:
        # Use explicit page mapping
        target_pages = parse_page_list(page_map, bg_page_count)
        if len(target_pages) != scribble_page_count:
            raise ValueError(
                f"Page map specifies {len(target_pages)} pages but scribble PDF has {scribble_page_count} pages"
            )
        # With explicit mapping, we know exactly which pages to export
        export_pages = target_pages
    elif all_pages:
        # Export all pages from background PDF
        export_pages = list(range(bg_page_count))
        if scribble_page_count > bg_page_count:
            raise ValueError(
                f"Scribble PDF has {scribble_page_count} pages but background has {bg_page_count} pages"
            )
    else:
        # Default: only export pages that have scribbles (trimmed output)
        export_pages = list(range(scribble_page_count))
        if scribble_page_count > bg_page_count:
            raise ValueError(
                f"Scribble PDF has {scribble_page_count} pages but background has {bg_page_count} pages"
            )
    
    if len(export_pages) == 0:
        bg_doc.close()
        scribble_doc.close()
        raise ValueError("No pages to process")
    
    # Create output document
    output_doc = fitz.open()
    
    for scribble_idx, bg_page_num in enumerate(export_pages):
        bg_page = bg_doc[bg_page_num]
        
        # Get the corresponding scribble page (if it exists)
        if scribble_idx < scribble_page_count:
            scribble_page = scribble_doc[scribble_idx]
        else:
            scribble_page = None  # No scribble for this page
        
        # Copy background page to output
        output_doc.insert_pdf(bg_doc, from_page=bg_page_num, to_page=bg_page_num)
        output_page = output_doc[-1]
        
        # Only overlay if we have a scribble page
        if scribble_page is not None:
            # Render scribble page with alpha channel
            zoom = 2.0
            pix = scribble_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
            
            # Convert to PIL Image for proper alpha handling
            pil_img = pix.pil_image()
            
            # Convert to RGBA to ensure we have an alpha channel
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
            
            # Replace RGB values with target color while preserving alpha
            target_r = int(scribble_color[0] * 255)
            target_g = int(scribble_color[1] * 255)
            target_b = int(scribble_color[2] * 255)
            
            # Modify pixels using PIL (proper alpha handling)
            pixels = pil_img.load()
            width, height = pil_img.size
            
            for y in range(height):
                for x in range(width):
                    r, g, b, a = pixels[x, y]
                    if a > 0:  # Only modify non-transparent pixels
                        pixels[x, y] = (target_r, target_g, target_b, a)
            
            # Apply opacity to alpha channel
            if scribble_opacity < 1.0:
                pixels = pil_img.load()
                for y in range(height):
                    for x in range(width):
                        r, g, b, a = pixels[x, y]
                        a = int(a * scribble_opacity)
                        pixels[x, y] = (r, g, b, a)
            
            # Convert to PNG bytes using PIL (proper alpha preservation)
            img_buffer = io.BytesIO()
            pil_img.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            # Insert on output page
            scribble_rect = scribble_page.rect
            rect = fitz.Rect(0, 0, scribble_rect.width, scribble_rect.height)
            
            output_page.insert_image(
                rect,
                stream=img_bytes,
                overlay=True
            )
    
    # Save the output document
    output_doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    output_doc.close()
    bg_doc.close()
    scribble_doc.close()
    
    return len(export_pages)


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """PyNcode - Tool for overlaying Ncode patterns and scribbles on PDFs."""
    pass


@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True))
@click.argument('output_pdf', type=click.Path())
@click.argument('ncode_prefix', type=str, default='')
@click.option('--pngs', '-p', multiple=True, type=click.Path(exists=True),
              help='Explicit PNG file paths (overrides prefix)')
@click.option('--dpi', '-d', default=600, help='DPI for rendering (default: 600)')
@click.option('--ncode-dpi', default=600, help='DPI of Ncode PNG images (default: 600)')
@click.option('--num-pages', '-n', type=int, default=None,
              help='Number of pages (defaults to PDF page count)')
def ncode(
    input_pdf: str,
    output_pdf: str,
    ncode_prefix: str,
    pngs: Tuple[str, ...],
    dpi: int,
    ncode_dpi: int,
    num_pages: int
):
    """Overlay Ncode PNG patterns on a PDF using CMYK K-removal.
    
    INPUT_PDF: Path to the input PDF
    
    OUTPUT_PDF: Path to the output PDF with Ncode overlay
    
    NCODE_PREFIX: Optional prefix for auto-detecting PNG files.
                  Looks for prefix0.png, prefix1.png, etc.
    
    IMPORTANT: This process rasterizes the PDF. Text will NOT remain selectable.
    This is REQUIRED for proper Ncode pen detection.
    
    Examples:
        # Auto-detect with prefix
        pyncode ncode input.pdf output.pdf ncode_3_28_10_
        
        # Explicit PNG files
        pyncode ncode input.pdf output.pdf --pngs page0.png page1.png
    """
    # Determine which PNG files to use
    if pngs:
        ncode_pngs_list = list(pngs)
    elif ncode_prefix:
        if num_pages is None:
            doc = fitz.open(input_pdf)
            num_pages = len(doc)
            doc.close()
        
        ncode_pngs_list = find_ncode_pngs(ncode_prefix, num_pages)
        if len(ncode_pngs_list) < num_pages:
            click.echo(
                f"Error: Only found {len(ncode_pngs_list)} Ncode PNGs for {num_pages} pages.",
                err=True
            )
            click.echo(f"Looking for: {ncode_prefix}0.png, {ncode_prefix}1.png, ...", err=True)
            raise click.Abort()
    else:
        click.echo(
            "Error: Either provide NCODE_PREFIX or use --pngs to specify PNG files",
            err=True
        )
        raise click.Abort()
    
    try:
        pages = create_ncoded_pdf(
            input_pdf,
            ncode_pngs_list,
            output_pdf,
            dpi=dpi,
            ncode_dpi=ncode_dpi
        )
        click.echo(f"Successfully created Ncoded PDF with {pages} pages → {output_pdf}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('background_pdf', type=click.Path(exists=True))
@click.argument('scribble_pdf', type=click.Path(exists=True))
@click.argument('output_pdf', type=click.Path())
@click.option('--color', '-c', default='red',
              help='Scribble color: red, blue, green, black, or RGB triplet')
@click.option('--opacity', '-o', default=1.0, type=float,
              help='Scribble opacity (0.0-1.0, default: 1.0)')
@click.option('--pages', '-p', type=str, default=None,
              help='Page mapping: comma-separated list of original page numbers. '
                   'Format: "1,3-5,7,11,48-" where 48- means 48 to end. '
                   'Scribble pages are mapped in order to these pages.')
@click.option('--all-pages', '-a', is_flag=True,
              help='Export all pages from background PDF (default: only pages with scribbles).')
def scribble(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    color: str,
    opacity: float,
    pages: str,
    all_pages: bool
):
    """Overlay scribble PDF on background PDF (preserves text selectability).
    
    BACKGROUND_PDF: Path to the original/background PDF
    
    SCRIBBLE_PDF: Path to the scribble PDF containing handwriting
    
    OUTPUT_PDF: Path to the output merged PDF
    
    The background PDF structure is preserved - text remains selectable!
    
    The --pages option lets you specify which original pages to overlay.
    This is useful when the scribble PDF doesn't have all pages (e.g., you
    only wrote on pages 1, 3, 5, 7). Format: "1,3-5,7,11,48-"
    where 48- means page 48 to the end. Scribble pages are mapped in order.
    """
    scribble_color = (1.0, 0.0, 0.0)
    
    color_lower = color.lower()
    if color_lower == 'red':
        scribble_color = (1.0, 0.0, 0.0)
    elif color_lower == 'blue':
        scribble_color = (0.0, 0.0, 1.0)
    elif color_lower == 'green':
        scribble_color = (0.0, 1.0, 0.0)
    elif color_lower == 'black':
        scribble_color = (0.0, 0.0, 0.0)
    elif ',' in color:
        try:
            parts = color.split(',')
            if len(parts) == 3:
                scribble_color = (
                    float(parts[0]) / 255.0,
                    float(parts[1]) / 255.0,
                    float(parts[2]) / 255.0
                )
            else:
                click.echo("Error: RGB triplet must have 3 values", err=True)
                raise click.Abort()
        except ValueError:
            click.echo("Error: Invalid RGB values", err=True)
            raise click.Abort()
    else:
        click.echo(f"Error: Unknown color '{color}'", err=True)
        raise click.Abort()
    
    if opacity < 0.0 or opacity > 1.0:
        click.echo("Error: Opacity must be between 0.0 and 1.0", err=True)
        raise click.Abort()
    
    try:
        page_count = overlay_scribbles_with_color(
            background_pdf,
            scribble_pdf,
            output_pdf,
            scribble_color=scribble_color,
            scribble_opacity=opacity,
            page_map=pages,
            all_pages=all_pages
        )
        color_str = f"{int(scribble_color[0]*255)},{int(scribble_color[1]*255)},{int(scribble_color[2]*255)}"
        click.echo(f"Successfully overlaid scribbles on {page_count} pages → {output_pdf}")
        click.echo(f"  Color: {color_str}, Opacity: {opacity}")
        if pages is not None:
            click.echo(f"  Page mapping: {pages}")
        if all_pages:
            click.echo("  All pages exported (including pages without scribbles)")
        else:
            click.echo("  Only pages with scribbles exported")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('background_pdf', type=click.Path(exists=True))
@click.argument('scribble_pdf', type=click.Path(exists=True))
@click.argument('output_pdf', type=click.Path())
@click.option('--opacity', '-o', default=1.0, type=float,
              help='Scribble opacity (0.0-1.0, default: 1.0)')
@click.option('--pages', '-p', type=str, default=None,
              help='Page mapping: comma-separated list of original page numbers. '
                   'Format: "1,3-5,7" - same as scribble command.')
@click.option('--all-pages', '-a', is_flag=True,
              help='Export all pages from background PDF (default: only pages with scribbles).')
def scribble_simple(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    opacity: float,
    pages: str,
    all_pages: bool
):
    """Simple scribble overlay (no color transformation, faster).
    
    Same page mapping syntax as the scribble command: --pages "1,3-5,7"
    
    By default, only exports pages with scribbles. Use --all-pages to export all pages.
    """
    if opacity < 0.0 or opacity > 1.0:
        click.echo("Error: Opacity must be between 0.0 and 1.0", err=True)
        raise click.Abort()
    
    try:
        page_count = overlay_scribbles_simple(
            background_pdf,
            scribble_pdf,
            output_pdf,
            scribble_opacity=opacity,
            page_map=pages,
            all_pages=all_pages
        )
        click.echo(f"Successfully overlaid scribbles on {page_count} pages → {output_pdf}")
        if pages is not None:
            click.echo(f"  Page mapping: {pages}")
        if all_pages:
            click.echo("  All pages exported (including pages without scribbles)")
        else:
            click.echo("  Only pages with scribbles exported")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
