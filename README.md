# PyNcode

A Python tool for overlaying NeoLAB Ncode patterns and smartpen scribbles on
PDFs.

NOTE: This tool (and much of this documentation) was written by AI. The AI was
running on Gregor Richards's home system. His energy supply is mostly clean:
hydro and nuclear.

## Use case

In order to add your own paper to NeoLAB's tools, you need to pay them a
substantial sum and upload it to their system. Presumably the intended use case
for this is manufacturers of notebooks and such, for whom such an arrangement
makes sense. But, another use for custom paper also makes sense with the Neo
Smartpen: annotating existing documents. For instance, writing grammar and
spelling notes. It would be nonsensical to upload every document you want to
annotate and even more nonsensical to pay the fee for this use.

To that end, I've extracted the Ncode patterns from several of NeoLAB's freely
available templates, and this tool can be used to overlay them on your own
documents. Thus, you may take, for example, the letter-sized lined template
sheet, but actually write on your own document instead of lined paper. This
tool can both put the Ncode on your own document and take the scribbles that
your smartpen creates and put them back on the original document.

The original document never travels to NeoLAB. You can only use one document
with one template at a time, since the smartpen has no other way of
distinguishing them. For example, if you're working on form A and form B at the
same time, the system won't work if you apply the letter-sized lined template
to both forms, since it'll combine the scribbling on both. Either do form A
first, download it, delete it from the smartpen's system, then do form B, or
use different templates. There are about a dozen templates available, so it's
usually easy enough to keep things separated.

## Features

1. **Ncode Overlay**: Overlay Ncode pattern PNGs on PDFs
   - Follows original NeoLAB SDK's CMYK K-removal approach
   - Auto-detection of PNG files using prefix (e.g., `letter-`)
   - Original PDF content is rasterized (the produced files are huge and have
     non-selectable text)

2. **Scribble Overlay**: Overlay smartpen handwriting on original PDFs
   - Preserves PDF structure (text remains selectable)
   - Supports custom colors (default: red)
   - Adjustable opacity

## Installation

```sh
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
pyncode ncode input.pdf output.pdf ncode/letter-

# Explicit PNG files
pyncode ncode input.pdf output.pdf --pngs page0.png page1.png page2.png

# Options
pyncode ncode --help
```

### 2. Scribble Overlay (Preserves PDF Structure, Text IS Selectable)

```sh
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

# Export ALL pages from background (including pages without scribbles)
# Default is to only export pages with scribbles (trimmed output)
pyncode scribble document.pdf my_scribbles.pdf output.pdf --all-pages

# Options
pyncode scribble --help
```


### 3. Simple Scribble Overlay (faster, no color transformation)

```bash
# Default: only pages with scribbles
pyncode scribble-simple document.pdf my_scribbles.pdf output.pdf

# With page mapping
pyncode scribble-simple document.pdf my_scribbles.pdf output.pdf --pages "1,3-5,7"

# Export all pages
pyncode scribble-simple document.pdf my_scribbles.pdf output.pdf --all-pages
```

Faster than `scribble` because it doesn't recolor - just overlays as-is.


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

## Workflow Recommendations

### For Best Results:

1. **Keep original PDF** - Always keep your original document with selectable text
2. **Create Ncoded version for printing** - Use `ncode` command to make print-ready version
3. **Capture scribbles** - Write on the printed Ncoded document with your Neo pen
4. **Overlay scribbles on ORIGINAL** - Use `scribble` command to overlay on original (not Ncoded)


## References

- [NeoLAB Ncode SDK 2.0](https://github.com/NeoSmartpen/Ncode-SDK2.0)
- [Ncode-SDK-for-Linux](https://github.com/Post-Math/Ncode-SDK-for-Linux)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
