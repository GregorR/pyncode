# PyNcode

A Python tool for overlaying Ncode patterns and smartpen scribbles on PDFs.

## Features

1. **Ncode Overlay**: Overlay Ncode pattern PNG images on PDFs (similar to the original NeoLAB Ncode SDK)
   - Preserves text selectability - the original PDF content remains visible and searchable
   - Supports auto-detection of Ncode PNG files using a prefix (e.g., `ncode_3_28_10_` finds `ncode_3_28_10_0.png`, `ncode_3_28_10_1.png`, etc.)

2. **Scribble Overlay**: Overlay smartpen handwriting (scribble PDFs) on original PDFs with color control
   - Preserves the background PDF structure (text remains selectable)
   - Supports custom colors (default: red)
   - Adjustable opacity

## Installation

```bash
cd /sandbox/pyncode
pip install -r requirements.txt
pip install -e .
```

### Dependencies

- **PyMuPDF** (fitz): Python binding for MuPDF - the same library used by the C++ Ncode SDK
- **Pillow**: Image processing for Ncode PNG handling
- **Click**: Command-line interface framework

## Usage

### 1. Overlay Ncode Patterns on PDF

#### Auto-detect Ncode PNGs with prefix (recommended)

Like the original SDK, you can specify a prefix and it will automatically find the PNG files:

```bash
# Auto-detect ncode_3_28_10_0.png, ncode_3_28_10_1.png, etc.
pyncode ncode input.pdf output.pdf ncode_3_28_10_
```

#### Specify explicit PNG files

```bash
pyncode ncode input.pdf output.pdf --pngs ncode_page1.png ncode_page2.png ncode_page3.png
```

Options:
- `--dpi, -d`: DPI of the PDF (default: 600)
- `--ncode-dpi`: DPI of Ncode PNG images (default: 600)
- `--num-pages, -n`: Number of pages (defaults to PDF page count)
- `--pngs, -p`: Explicit PNG file paths (overrides prefix)

**Requirements:**
- Ncode PNGs should be 1-bit (black dots on white background)
- PNGs are typically generated at 600 DPI by the Ncode SDK
- The Ncode pattern is overlaid with transparent background - it won't obscure your PDF!

### 2. Overlay Scribbles on PDF (with color control)

Overlay smartpen handwriting on the original document:

```bash
# Default: red scribbles
pyncode scribble document.pdf my_scribbles.pdf output.pdf

# Custom color (blue)
pyncode scribble document.pdf my_scribbles.pdf output.pdf --color blue

# Custom RGB color
pyncode scribble document.pdf my_scribbles.pdf output.pdf --color "0,128,0"  # Green

# Adjust opacity
pyncode scribble document.pdf my_scribbles.pdf output.pdf --color red --opacity 0.8
```

Options:
- `--color, -c`: Scribble color (red, blue, green, black, or RGB triplet like "1,0,0")
- `--opacity, -o`: Opacity (0.0-1.0, default: 1.0)

**Important:**
- The background PDF structure is preserved - text remains selectable!
- Both PDFs should have the same number of pages (or it will use the minimum)
- Scribble PDF should contain only the handwriting (transparent background)

### 3. Simple Scribble Overlay (faster, no color transformation)

```bash
pyncode scribble-simple document.pdf my_scribbles.pdf output.pdf
```

This is faster but doesn't recolor the scribbles. Use when you don't need color transformation.

## How It Works

### Ncode Overlay

The Ncode overlay function follows the principles of the NeoLAB Ncode SDK:

1. Loads each Ncode PNG (1-bit pattern)
2. Converts the white background to transparent
3. Embeds the dots as a transparent overlay on each PDF page
4. Preserves the original PDF content (text remains selectable)

The original C SDK uses a more complex two-layer CMYK approach where:
- The artwork layer has K=0 (no black ink)
- The Ncode dots are pure K (black ink only)

This Python implementation uses transparent PNG overlay which achieves the same visual result while preserving PDF structure and text selectability.

### Scribble Overlay

The scribble overlay function:

1. Renders each scribble page to a high-resolution pixmap
2. Applies color transformation (if specified)
3. Overlays the result on the corresponding background page
4. Preserves the background PDF structure

**Why text remains selectable:**
- The background PDF is not rasterized
- Only the scribble layers are added as image overlays
- The original text content and structure are preserved

## Examples

### Example 1: Process a multi-page document with Ncode

```bash
# Generate Ncode PNGs using the official SDK (Windows only)
# Or use the Go SDK on Linux

# Then overlay them on your PDF with auto-detection
pyncode ncode my_document.pdf ncoded_document.pdf ncode_3_28_10_

# Or with explicit files
pyncode ncode my_document.pdf ncoded_document.pdf --pngs \
  ncode_3_28_10_0.png \
  ncode_3_28_10_1.png \
  ncode_3_28_10_2.png
```

### Example 2: Add handwritten notes to a document

```bash
# Capture scribbles with your Neo smartpen
# Export as PDF (this creates scribbles.pdf)

# Overlay on the original document with red ink
pyncode scribble original_document.pdf scribbles.pdf annotated.pdf --color red

# Or with blue ink and semi-transparent
pyncode scribble original_document.pdf scribbles.pdf annotated.pdf --color blue --opacity 0.7
```

### Example 3: Batch processing

```bash
#!/bin/bash
# Process all documents in a directory

for doc in documents/*.pdf; do
    base=$(basename "$doc" .pdf)
    
    # Check if Ncode PNGs exist with prefix
    if [ -f "ncode/${base}_0.png" ]; then
        pyncode ncode "$doc" "ncoded/${base}.pdf" "ncode/${base}_"
        echo "Ncoded: $base"
    fi
    
    # Check if scribble PDF exists
    if [ -f "scribbles/${base}_scribbles.pdf" ]; then
        pyncode scribble "$doc" "scribbles/${base}_scribbles.pdf" "annotated/${base}.pdf" --color red
        echo "Annotated: $base"
    fi
done
```

## Python API

You can also use PyNcode as a Python library:

```python
from pyncode.pyncode import create_ncoded_pdf, overlay_scribbles_with_color

# Overlay Ncode patterns with auto-detection
pages = create_ncoded_pdf(
    input_pdf='input.pdf',
    ncode_pngs='ncode_3_28_10_',  # Prefix for auto-detection
    output_pdf='output.pdf',
    dpi=600,
    ncode_dpi=600
)
print(f"Processed {pages} pages")

# Or with explicit PNG list
pages = create_ncoded_pdf(
    input_pdf='input.pdf',
    ncode_pngs=['ncode1.png', 'ncode2.png'],
    output_pdf='output.pdf'
)

# Overlay scribbles with custom color
pages = overlay_scribbles_with_color(
    background_pdf='document.pdf',
    scribble_pdf='scribbles.pdf',
    output_pdf='annotated.pdf',
    scribble_color=(1.0, 0.0, 0.0),  # Red
    scribble_opacity=1.0
)
```

## Compatibility

- **Python**: 3.8+
- **PyMuPDF**: 1.23.0+
- **Operating Systems**: Linux, macOS, Windows

## Limitations

1. **Ncode Generation**: This tool only overlays existing Ncode PNGs. To generate Ncode patterns, you need:
   - The official NeoLAB Ncode SDK (Windows only), or
   - The Go SDK (`Ncode-SDK-for-Linux`) with Mono runtime

2. **Ncode Recognition**: For best pen recognition:
   - Use 600 DPI Ncode PNGs
   - Ensure Ncode PNGs are properly generated by the SDK
   - The transparent overlay approach may have slightly different recognition characteristics than the full CMYK two-layer approach

3. **Scribble Color**: Color transformation works best on grayscale/black scribbles. Colored scribbles may not transform perfectly.

## Troubleshooting

### "Ncode completely obscures the PDF" (should be fixed now!)
If this still happens, check that:
- Your Ncode PNGs are properly formatted (black dots on white background)
- The PNGs are being loaded correctly
- Try updating to the latest version

### "Page count mismatch" error
Ensure both PDFs have the same number of pages. The tool will use the minimum if they differ, but this may cause issues.

### "Only found X Ncode PNGs" error
Check that your PNG files exist and match the naming pattern:
- If prefix is `ncode_3_28_10_`, it looks for `ncode_3_28_10_0.png`, `ncode_3_28_10_1.png`, etc.
- File extensions `.png` and `.PNG` are both supported

### Text not selectable after Ncode overlay
This is unexpected - the tool is designed to preserve text selectability. If this occurs, check:
- PyMuPDF version is up to date
- The Ncode PNGs aren't too large (should match page dimensions)

## Running Examples

```bash
# Quick start example with fake patterns
python examples/quick_start.py

# View CLI help
pyncode --help
pyncode ncode --help
pyncode scribble --help
```

## References

- [NeoLAB Ncode SDK 2.0](https://github.com/NeoSmartpen/Ncode-SDK2.0) (Official Windows SDK)
- [Ncode-SDK-for-Linux](https://github.com/Post-Math/Ncode-SDK-for-Linux) (Community Go SDK)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [MuPDF](https://mupdf.com/) - The underlying PDF rendering library
