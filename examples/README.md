# PyNcode Examples

This directory contains example scripts demonstrating how to use PyNcode.

## Quick Start Example

Run `quick_start.py` for a complete example that demonstrates:
1. Creating a test PDF with selectable text
2. Generating fake Ncode pattern PNGs
3. Overlaying Ncode patterns using **auto-detection** (prefix-based)
4. Creating fake scribble PDFs
5. Overlaying scribbles with custom colors

**Run the example:**
```bash
cd /sandbox/pyncode
python examples/quick_start.py
```

## CLI Examples

The tool now supports two ways to specify Ncode PNG files:

### Auto-detection with prefix (recommended)

Like the original NeoLAB SDK:
```bash
pyncode ncode input.pdf output.pdf ncode_3_28_10_
```

This automatically finds `ncode_3_28_10_0.png`, `ncode_3_28_10_1.png`, etc.

### Explicit file list

```bash
pyncode ncode input.pdf output.pdf --pngs page0.png page1.png page2.png
```

## Ncode Overlay Example

See `quick_start.py` for Ncode overlay with auto-detection.

Key changes from the original implementation:
- **Transparent background**: Ncode PNGs now have transparent backgrounds so they don't obscure the PDF
- **Auto-detection**: Prefix-based file detection like the original SDK
- **Preserved text**: Original PDF text remains selectable

## Scribble Overlay Example

See `quick_start.py` for scribble overlay examples.

The scribble overlay:
- Preserves the background PDF structure (text is selectable)
- Supports color transformation (default: red)
- Supports opacity control

## Batch Processing Example

```bash
#!/bin/bash
# Process all documents in a directory

for doc in documents/*.pdf; do
    base=$(basename "$doc" .pdf)
    
    # Auto-detect Ncode PNGs with prefix
    if ls ncode/${base}_*.png 1> /dev/null 2>&1; then
        pyncode ncode "$doc" "ncoded/${base}.pdf" "ncode/${base}_"
        echo "Ncoded: $base"
    fi
    
    # Overlay scribbles
    if [ -f "scribbles/${base}_scribbles.pdf" ]; then
        pyncode scribble "$doc" "scribbles/${base}_scribbles.pdf" "annotated/${base}.pdf" --color red
        echo "Annotated: $base"
    fi
done
```
