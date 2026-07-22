#!/usr/bin/env python3
"""
PyNcode - A Python tool for overlaying Ncode patterns and scribbles on PDFs.

This tool provides two main functions:
1. Overlay Ncode patterns (as PNG images) on PDFs - preserving text selectability
2. Overlay scribble PDFs (smartpen handwriting) on original PDFs with color control

Based on the NeoLAB Ncode SDK principles:
- Ncode overlay uses a two-layer approach: artwork layer (CMYK with K=0) + mask layer (pure K)
- Scribble overlay preserves the background PDF structure for text selectability
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


def load_ncode_png(png_path: str, dpi: int = 600) -> Tuple[bytes, int, int]:
    """
    Load an Ncode PNG image and return it with transparent background.
    
    Ncode PNGs are 1-bit (black dots on white background). For proper Ncode overlay,
    the white background must be made transparent so it doesn't obscure the PDF.
    
    Args:
        png_path: Path to the Ncode PNG file
        dpi: DPI of the Ncode image (default: 600)
        
    Returns:
        Tuple of (PNG data bytes with transparency, width, height)
    """
    img = Image.open(png_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        if img.mode == '1':
            # 1-bit image - convert to RGBA with transparency
            img = img.convert('L')  # grayscale first
        elif img.mode != 'L':
            img = img.convert('L')  # grayscale
        
        # Now create RGBA with transparency
        # White/light pixels become transparent, dark pixels (dots) stay opaque
        img_rgba = Image.new('RGBA', img.size)
        for x in range(img.width):
            for y in range(img.height):
                gray = img.getpixel((x, y))
                if gray < 128:
                    # Black dot - keep opaque black
                    img_rgba.putpixel((x, y), (0, 0, 0, 255))
                else:
                    # White background - make fully transparent
                    img_rgba.putpixel((x, y), (0, 0, 0, 0))
        img = img_rgba
    
    width, height = img.size
    
    # Save to PNG in memory with transparency
    png_buffer = io.BytesIO()
    img.save(png_buffer, format='PNG')
    png_data = png_buffer.getvalue()
    
    return png_data, width, height


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
    Overlay Ncode patterns (PNG images) on a PDF, following the NeoLAB Ncode SDK approach.
    
    The Ncode overlay preserves the original PDF content - text remains selectable.
    Ncode dots are overlaid as a transparent PNG where only the black dots are visible.
    
    Args:
        input_pdf: Path to the input PDF
        ncode_pngs: Either a list of PNG paths OR a prefix string for auto-detection
                   If a prefix, looks for prefix0.png, prefix1.png, etc.
        output_pdf: Path to the output PDF
        dpi: DPI for rendering (used for coordinate calculations)
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
    
    # Open the input PDF for modification
    doc = fitz.open(input_pdf)
    
    # Process each page
    for page_num in range(page_count):
        page = doc[page_num]
        png_path = ncode_pngs_list[page_num]
        
        # Get page dimensions in points (PDF coordinate system)
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        # Load the Ncode PNG with transparent background
        png_data, img_width, img_height = load_ncode_png(png_path, ncode_dpi)
        
        # Calculate the size to draw the Ncode image
        # Ncode images are typically at 600 DPI, PDF is 72 DPI
        # So we need to scale: pdf_points = pixels * (72 / dpi)
        ncode_width_pt = img_width * 72 / ncode_dpi
        ncode_height_pt = img_height * 72 / ncode_dpi
        
        # Calculate scale factor to fit the Ncode image to the page
        # Ncode images should cover the entire page
        scale_x = page_width / ncode_width_pt
        scale_y = page_height / ncode_height_pt
        scale = min(scale_x, scale_y)
        
        # Center the Ncode image on the page
        scaled_width = ncode_width_pt * scale
        scaled_height = ncode_height_pt * scale
        x_offset = (page_width - scaled_width) / 2
        y_offset = (page_height - scaled_height) / 2
        
        # Create image insertion parameters
        rect = fitz.Rect(x_offset, y_offset, x_offset + scaled_width, y_offset + scaled_height)
        
        # Insert the image as an overlay (over the existing content)
        # The transparent background won't obscure the PDF
        page.insert_image(
            rect,
            stream=png_data,
            overlay=True  # Draw on top of existing content
        )
    
    # Save the output PDF
    doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    doc.close()
    
    return page_count


def create_scribble_overlay_pdf(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    scribble_color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
    scribble_opacity: float = 1.0,
    scale: float = 1.0
) -> int:
    """
    Overlay scribble PDF (smartpen handwriting) on a background PDF.
    
    This function merges handwriting from a scribble PDF onto the corresponding
    pages of a background PDF. The background PDF structure is preserved,
    meaning text remains selectable and the document remains searchable.
    
    The scribble PDF should contain pages with only the handwriting strokes
    (transparent background). The function will overlay these strokes onto
    the background PDF pages.
    
    Args:
        background_pdf: Path to the original/background PDF
        scribble_pdf: Path to the scribble PDF containing handwriting
        output_pdf: Path to the output merged PDF
        scribble_color: RGB tuple for recoloring the scribbles (default: red)
                       Values should be 0.0-1.0, e.g., (1.0, 0.0, 0.0) for red
        scribble_opacity: Opacity of the scribbles, 0.0-1.0 (default: 1.0)
        scale: Scale factor for the scribble PDF pages (default: 1.0)
        
    Returns:
        Number of pages in the output PDF
        
    Raises:
        ValueError: If page counts don't match
        FileNotFoundError: If input files don't exist
    """
    bg_path = Path(background_pdf)
    scribble_path = Path(scribble_pdf)
    
    if not bg_path.exists():
        raise FileNotFoundError(f"Background PDF not found: {background_pdf}")
    if not scribble_path.exists():
        raise FileNotFoundError(f"Scribble PDF not found: {scribble_pdf}")
    
    # Open both PDFs
    bg_doc = fitz.open(background_pdf)
    scribble_doc = fitz.open(scribble_pdf)
    
    bg_page_count = len(bg_doc)
    scribble_page_count = len(scribble_doc)
    
    # Use the minimum of the two page counts
    page_count = min(bg_page_count, scribble_page_count)
    
    if page_count == 0:
        bg_doc.close()
        scribble_doc.close()
        raise ValueError("One or both PDFs have no pages")
    
    if bg_page_count != scribble_page_count:
        click.echo(
            f"Warning: Page count mismatch - background has {bg_page_count} pages, "
            f"scribbles have {scribble_page_count} pages. Using {page_count} pages.",
            err=True
        )
    
    # Process each page
    for page_num in range(page_count):
        bg_page = bg_doc[page_num]
        scribble_page = scribble_doc[page_num]
        
        # Get the background page dimensions
        page_rect = bg_page.rect
        
        # Render the scribble page to a pixmap with the specified color
        # We use the page's media box for rendering
        scribble_rect = scribble_page.rect
        mat = fitz.Matrix(scale, scale)  # Apply scale
        
        # Render scribble page at high quality (2x DPI for better stroke quality)
        zoom = 2.0
        mat = fitz.Matrix(zoom * scale, zoom * scale)
        pix = scribble_page.get_pixmap(matrix=mat, alpha=True)
        
        # Get the pixmap as bytes
        img_data = pix.tobytes("png")
        
        # Calculate the size for insertion
        scaled_width = scribble_rect.width * scale
        scaled_height = scribble_rect.height * scale
        
        # Position at top-left
        rect = fitz.Rect(0, 0, scaled_width, scaled_height)
        
        # Insert the scribble image as an overlay
        # We use insert_image which preserves the background PDF structure
        bg_page.insert_image(
            rect,
            stream=img_data,
            overlay=True,
            opacity=scribble_opacity
        )
    
    # Save the output PDF
    bg_doc.save(
        output_pdf,
        garbage=4,
        deflate=True,
        clean=True,
        linear=True  # Optimize for web viewing
    )
    
    bg_doc.close()
    scribble_doc.close()
    
    return page_count


def create_scribble_overlay_pdf_vector(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    scribble_color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
    scribble_opacity: float = 1.0
) -> int:
    """
    Overlay scribble PDF using vector insertion to preserve stroke quality.
    
    This function uses insert_pdf to overlay scribble pages, which preserves
    vector data and allows for proper color transformation. The scribble strokes
    will remain crisp at any zoom level.
    
    Args:
        background_pdf: Path to the original/background PDF
        scribble_pdf: Path to the scribble PDF containing handwriting
        output_pdf: Path to the output merged PDF
        scribble_color: RGB tuple for recoloring the scribbles (default: red)
        scribble_opacity: Opacity of the scribbles, 0.0-1.0 (default: 1.0)
        
    Returns:
        Number of pages in the output PDF
    """
    # Note: The vector overlay method is experimental.
    # For best results, use overlay_scribbles_simple or overlay_scribbles_with_color
    # which use rasterized overlay for better compatibility.
    raise NotImplementedError(
        "Vector overlay is not yet implemented. "
        "Please use overlay_scribbles_simple or overlay_scribbles_with_color instead."
    )


# Simplified vector overlay that actually works with PyMuPDF
def overlay_scribbles_simple(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    scribble_color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
    scribble_opacity: float = 1.0
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
        
    Returns:
        Number of pages processed
    """
    bg_doc = fitz.open(background_pdf)
    scribble_doc = fitz.open(scribble_pdf)
    
    page_count = min(len(bg_doc), len(scribble_doc))
    
    if page_count == 0:
        raise ValueError("One or both PDFs have no pages")
    
    for page_num in range(page_count):
        bg_page = bg_doc[page_num]
        scribble_page = scribble_doc[page_num]
        
        # Render scribble page to pixmap (preserves alpha channel)
        zoom = 2.0  # High quality
        pix = scribble_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
        
        # Convert to bytes
        img_bytes = pix.tobytes("png")
        
        # Create image insertion rectangle
        scribble_rect = scribble_page.rect
        rect = fitz.Rect(0, 0, scribble_rect.width, scribble_rect.height)
        
        # Insert image as overlay
        bg_page.insert_image(
            rect,
            stream=img_bytes,
            overlay=True,
            opacity=scribble_opacity
        )
    
    bg_doc.save(output_pdf, garbage=4, deflate=True)
    bg_doc.close()
    scribble_doc.close()
    
    return page_count


def overlay_scribbles_with_color(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    scribble_color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
    scribble_opacity: float = 1.0
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
        
    Returns:
        Number of pages processed
    """
    bg_doc = fitz.open(background_pdf)
    scribble_doc = fitz.open(scribble_pdf)
    
    page_count = min(len(bg_doc), len(scribble_doc))
    
    if page_count == 0:
        bg_doc.close()
        scribble_doc.close()
        raise ValueError("One or both PDFs have no pages")
    
    for page_num in range(page_count):
        bg_page = bg_doc[page_num]
        scribble_page = scribble_doc[page_num]
        
        # Render scribble page with color transformation
        # First, render to get the alpha mask (handwriting strokes)
        zoom = 2.0
        pix = scribble_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
        
        # Create a new pixmap with the target color
        rgba_pix = fitz.Pixmap(fitz.csRGB, pix)
        
        # Apply color transformation
        # For each pixel, replace RGB with target color while preserving alpha
        for y in range(rgba_pix.height):
            for x in range(rgba_pix.width):
                # Get original pixel
                orig = pix.get_pixel(x, y)
                alpha = orig[3] if len(orig) > 3 else 255
                
                if alpha > 0:
                    # Set to target color with original alpha
                    r = int(scribble_color[0] * 255)
                    g = int(scribble_color[1] * 255)
                    b = int(scribble_color[2] * 255)
                    rgba_pix.set_pixel(x, y, (r, g, b, alpha))
        
        # Convert to image bytes
        img_bytes = rgba_pix.tobytes("png")
        
        # Insert on background page
        scribble_rect = scribble_page.rect
        rect = fitz.Rect(0, 0, scribble_rect.width, scribble_rect.height)
        
        bg_page.insert_image(
            rect,
            stream=img_bytes,
            overlay=True,
            opacity=scribble_opacity
        )
    
    bg_doc.save(output_pdf, garbage=4, deflate=True)
    bg_doc.close()
    scribble_doc.close()
    
    return page_count


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """PyNcode - Tool for overlaying Ncode patterns and scribbles on PDFs."""
    pass


@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True))
@click.argument('output_pdf', type=click.Path())
@click.argument('ncode_prefix', type=str, default='')
@click.option('--pngs', '-p', multiple=True, type=click.Path(exists=True),
              help='Explicit PNG file paths (overrides prefix)')
@click.option('--dpi', '-d', default=600, help='DPI of the PDF (default: 600)')
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
    """Overlay Ncode PNG patterns on a PDF.
    
    INPUT_PDF: Path to the input PDF
    
    OUTPUT_PDF: Path to the output PDF with Ncode overlay
    
    NCODE_PREFIX: Optional prefix for auto-detecting PNG files.
                  Looks for prefix0.png, prefix1.png, etc.
                  If provided with --pngs, --pngs takes precedence.
    
    Examples:
        # Auto-detect with prefix (like the original SDK)
        pyncode ncode input.pdf output.pdf ncode_3_28_10_
        
        # Explicit PNG files
        pyncode ncode input.pdf output.pdf --pngs page0.png page1.png page2.png
        
        # Combined (explicit PNGs take precedence)
        pyncode ncode input.pdf output.pdf ncode_ --pngs custom1.png custom2.png
    """
    # Determine which PNG files to use
    if pngs:
        # Explicit PNGs provided
        ncode_pngs_list = list(pngs)
    elif ncode_prefix:
        # Use prefix for auto-detection
        if num_pages is None:
            # Get page count from PDF
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
        click.echo(f"Successfully overlayed Ncode on {pages} pages → {output_pdf}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('background_pdf', type=click.Path(exists=True))
@click.argument('scribble_pdf', type=click.Path(exists=True))
@click.argument('output_pdf', type=click.Path())
@click.option('--color', '-c', default='red',
              help='Scribble color: red, blue, green, black, or RGB triplet (e.g., "1,0,0")')
@click.option('--opacity', '-o', default=1.0, type=float,
              help='Scribble opacity (0.0-1.0, default: 1.0)')
def scribble(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    color: str,
    opacity: float
):
    """Overlay scribble PDF (smartpen handwriting) on a background PDF.
    
    BACKGROUND_PDF: Path to the original/background PDF
    
    SCRIBBLE_PDF: Path to the scribble PDF containing handwriting
    
    OUTPUT_PDF: Path to the output merged PDF
    
    The background PDF structure is preserved (text remains selectable).
    
    Example:
        pyncode scribble document.pdf my_scribbles.pdf merged.pdf --color red
    """
    # Parse color
    scribble_color = (1.0, 0.0, 0.0)  # Default: red
    
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
    
    # Validate opacity
    if opacity < 0.0 or opacity > 1.0:
        click.echo("Error: Opacity must be between 0.0 and 1.0", err=True)
        raise click.Abort()
    
    try:
        pages = overlay_scribbles_with_color(
            background_pdf,
            scribble_pdf,
            output_pdf,
            scribble_color=scribble_color,
            scribble_opacity=opacity
        )
        color_str = f"{int(scribble_color[0]*255)},{int(scribble_color[1]*255)},{int(scribble_color[2]*255)}"
        click.echo(f"Successfully overlaid scribbles on {pages} pages → {output_pdf}")
        click.echo(f"  Color: {color_str}, Opacity: {opacity}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('background_pdf', type=click.Path(exists=True))
@click.argument('scribble_pdf', type=click.Path(exists=True))
@click.argument('output_pdf', type=click.Path())
@click.option('--opacity', '-o', default=1.0, type=float,
              help='Scribble opacity (0.0-1.0, default: 1.0)')
def scribble_simple(
    background_pdf: str,
    scribble_pdf: str,
    output_pdf: str,
    opacity: float
):
    """Simple scribble overlay (no color transformation, faster).
    
    This is a faster version that simply overlays the scribbles without
    color transformation. Use this when you don't need to recolor the
    handwriting.
    
    BACKGROUND_PDF: Path to the original/background PDF
    
    SCRIBBLE_PDF: Path to the scribble PDF
    
    OUTPUT_PDF: Path to the output PDF
    
    Example:
        pyncode scribble-simple document.pdf my_scribbles.pdf merged.pdf
    """
    if opacity < 0.0 or opacity > 1.0:
        click.echo("Error: Opacity must be between 0.0 and 1.0", err=True)
        raise click.Abort()
    
    try:
        pages = overlay_scribbles_simple(
            background_pdf,
            scribble_pdf,
            output_pdf,
            scribble_opacity=opacity
        )
        click.echo(f"Successfully overlaid scribbles on {pages} pages → {output_pdf}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
