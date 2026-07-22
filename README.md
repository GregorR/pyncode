# PyNcode

A Python tool for overlaying Ncode patterns and smartpen scribbles on PDFs.

## ⚠️ Important: Two Different Approaches

This tool has **two different functions** with **opposite requirements**:

### 1. Ncode Overlay (ncode command)
**Does NOT preserve PDF structure** - text becomes non-selectable
- Uses full CMYK conversion with K=0 (like the original NeoLAB SDK)
- Rasterizes the PDF at 600 DPI
- **Required** for proper Ncode pen detection - the pen needs to distinguish Ncode dots (K=255) from background (K=0)

### 2. Scribble Overlay (scribble command)  
**DOES preserve PDF structure** - text remains selectable
- Adds scribbles as transparent image overlays
- Original PDF is not modified
- Text remains fully searchable and selectable

## Features

1. **Ncode Overlay**: Overlay Ncode pattern PNGs on PDFs
   - Follows original NeoLAB SDK's CMYK K-removal approach
   - Auto-detection of PNG files using prefix (e.g., `ncode_3_28_10_`)
   - ⚠️ **Text becomes non-selectable** (required for pen detection)

2. **Scribble Overlay**: Overlay smartpen handwriting on original PDFs
   - Preserves PDF structure - text remains selectable
   - Supports custom colors (default: red)
   - Adjustable opacity

## Installation

```bash
cd /sandbox/pyncode
pip install -r requirements.txt
pip install -e .
```

### Dependencies

- **PyMuPDF** (fitz): Python binding for MuPDF
- **Pillow**: Image processing
- **Click**: CLI framework

## Usage

### 1. Ncode Overlay (Rasterizes PDF, Text NOT Selectable)

```bash
# Auto-detect with prefix
pyncode ncode input.pdf output.pdf ncode_3_28_10_

# Explicit PNG files
pyncode ncode input.pdf output.pdf --pngs page0.png page1.png page2.png

# Options
pyncode ncode --help
```

**⚠️ Warning**: This command rasterizes the PDF. Text will NOT remain selectable. This is **required** for proper Ncode pen detection.

**How it works:**
1. Renders each PDF page to RGB at 600 DPI
2. Converts to CMYK
3. For each pixel:
   - If Ncode dot: CMYK = (0, 0, 0, 255) - pure black (K only)
   - If background: CMYK = (C, M, Y, 0) - no K component
4. The pen sees only the K=255 dots, ignoring the K=0 background

### 2. Scribble Overlay (Preserves PDF Structure, Text IS Selectable)

```bash
# Default: red scribbles (sequential page mapping)
pyncode scribble document.pdf my_scribbles.pdf output.pdf

# Custom color
pyncode scribble document.pdf my_scribbles.pdf output.pdf --color blue

# Custom RGB color
pyncode scribble document.pdf my_scribbles.pdf output.pdf --color "0,128,0"

# Adjust opacity
pyncode scribble document.pdf my_scribbles.pdf output.pdf --color red --opacity 0.8

# Specify which original pages to overlay (for incomplete scribble exports)
# If scribble PDF has pages for original pages 1, 3, 5, 7:
pyncode scribble document.pdf my_scribbles.pdf output.pdf --pages "1,3,5,7"

# Use ranges and open-ended ranges
# If scribble PDF has pages for original pages 1, 3-5, 7-10:
pyncode scribble document.pdf my_scribbles.pdf output.pdf --pages "1,3-5,7-10"

# If scribble PDF has pages starting from page 48 to the end:
pyncode scribble document.pdf my_scribbles.pdf output.pdf --pages "48-"

# Options
pyncode scribble --help
```

✅ **Text remains selectable** - the background PDF is not modified.

### 3. Simple Scribble Overlay (faster, no color transformation)

```bash
# Default mapping
pyncode scribble-simple document.pdf my_scribbles.pdf output.pdf

# With page mapping
pyncode scribble-simple document.pdf my_scribbles.pdf output.pdf --pages "1,3-5,7"
```

Faster than `scribble` because it doesn't recolor - just overlays as-is.

## Examples

### Example 1: Add Ncode to a Document

```bash
# Generate Ncode PNGs using NeoLAB SDK or Go SDK
# Then overlay on your PDF
pyncode ncode my_document.pdf ncoded_document.pdf ncode_3_28_10_

# Note: ncoded_document.pdf will have Ncode dots, but text is not selectable
```

### Example 2: Add Handwritten Notes

```bash
# Overlay scribbles on the ORIGINAL (non-ncoded) document
pyncode scribble original_document.pdf scribbles.pdf annotated.pdf --color red

# Now you can see your handwriting AND the text is still selectable!
```

### Example 3: Complete Workflow

```bash
#!/bin/bash
# 1. Add Ncode to document (for printing and pen use)
pyncode ncode document.pdf ncoded.pdf ncode_3_28_10_
echo "Print ncoded.pdf and use with Neo smartpen"

# 2. After writing, overlay scribbles on original
# (Keep original document with selectable text)
pyncode scribble document.pdf scribbles.pdf annotated.pdf --color red

# Result: annotated.pdf has your handwriting + selectable text
```

## Python API

```python
from pyncode.pyncode import create_ncoded_pdf, overlay_scribbles_with_color

# Ncode overlay (rasterizes PDF)
pages = create_ncoded_pdf(
    input_pdf='input.pdf',
    ncode_pngs='ncode_3_28_10_',  # Prefix
    output_pdf='output.pdf',
    dpi=600  # Standard Ncode DPI
)

# Scribble overlay (preserves PDF)
pages = overlay_scribbles_with_color(
    background_pdf='document.pdf',
    scribble_pdf='scribbles.pdf',
    output_pdf='annotated.pdf',
    scribble_color=(1.0, 0.0, 0.0),  # Red
    scribble_opacity=0.8
)
```

## Why Ncode Requires K=0 Conversion

The Neo smartpen uses an IR camera to detect the Ncode pattern. The algorithm works like this:

1. **Ncode dots** are printed as pure black (K=255 in CMYK)
2. **Background** should have K=0 (no black ink)
3. The pen's IR sensor sees K=255 (dots) vs K=0 (background)

If you don't set K=0 in the background:
- Text and graphics also have K values
- The pen can't distinguish Ncode dots from regular black text
- Pen tracking fails

This is why the Ncode overlay **must** rasterize and do the K=0 conversion - it's fundamental to how the pen works.

## Workflow Recommendations

### For Best Results:

1. **Keep original PDF** - Always keep your original document with selectable text
2. **Create Ncoded version for printing** - Use `ncode` command to make print-ready version
3. **Capture scribbles** - Write on the printed Ncoded document with your Neo pen
4. **Overlay scribbles on ORIGINAL** - Use `scribble` command to overlay on original (not Ncoded)
   - This keeps text selectable
   - You see both your handwriting and the original content

### Why Not Overlay on Ncoded PDF?

If you overlay scribbles on the Ncoded PDF:
- The Ncoded PDF is already rasterized
- Text is not selectable
- You lose the ability to search/copy text

Better workflow: Overlay on original, keep separate Ncoded version for printing.

## Troubleshooting

### "Pen doesn't recognize Ncode"
- Ensure Ncode PNGs are generated at 600 DPI
- Ensure PNGs are 1-bit (black dots on white)
- Don't modify the Ncoded PDF after creation

### "Text is not selectable"
- This is **expected** for Ncode-overlayed PDFs
- Use `scribble` command instead if you need selectable text

### "Only found X Ncode PNGs"
- Check file naming: `prefix0.png`, `prefix1.png`, etc.
- Both `.png` and `.PNG` extensions supported

## References

- [NeoLAB Ncode SDK 2.0](https://github.com/NeoSmartpen/Ncode-SDK2.0)
- [Ncode-SDK-for-Linux](https://github.com/Post-Math/Ncode-SDK-for-Linux)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
