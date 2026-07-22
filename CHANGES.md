# PyNcode Changes

## Version 1.1.0 (Current)

### Bug Fixes

1. **Ncode overlay obscuring PDF - FIXED**
   - The Ncode PNGs now have transparent backgrounds
   - Only the black dots are visible, the white background is transparent
   - Original PDF content remains fully visible and selectable

2. **Manual PNG file listing - IMPROVED**
   - Added auto-detection of Ncode PNG files using a prefix
   - Similar to the original NeoLAB SDK naming convention
   - Example: `ncode_3_28_10_` automatically finds `ncode_3_28_10_0.png`, `ncode_3_28_10_1.png`, etc.

### New Features

1. **Auto-detection of Ncode PNGs**
   ```bash
   # Before: Had to list every file
   pyncode ncode input.pdf output.pdf --pngs page0.png page1.png page2.png
   
   # Now: Just specify the prefix
   pyncode ncode input.pdf output.pdf ncode_3_28_10_
   ```

2. **Flexible CLI options**
   - Can use prefix OR explicit PNG files
   - Both methods can be combined (explicit takes precedence)
   - `--num-pages` option to override auto-detected page count

### Changed Files

- `pyncode.py`:
  - `load_ncode_png()`: Now returns PNG with transparent background
  - `create_ncoded_pdf()`: Updated to handle transparent PNGs and prefix auto-detection
  - `find_ncode_pngs()`: New function for auto-detecting PNG files
  - `ncode` command: Updated CLI to support prefix and explicit PNGs

- `README.md`: Updated documentation with new features

- `examples/quick_start.py`: Updated to demonstrate auto-detection

### Usage Examples

#### Ncode Overlay with Auto-Detection

```bash
# Auto-detect Ncode PNGs with prefix
pyncode ncode input.pdf output.pdf ncode_3_28_10_

# Or specify explicit PNG files
pyncode ncode input.pdf output.pdf --pngs page0.png page1.png page2.png

# Override auto-detected page count
pyncode ncode input.pdf output.pdf ncode_3_28_10_ --num-pages 10
```

#### Scribble Overlay (unchanged)

```bash
# Default red scribbles
pyncode scribble document.pdf scribbles.pdf output.pdf

# Custom color
pyncode scribble document.pdf scribbles.pdf output.pdf --color blue

# Custom opacity
pyncode scribble document.pdf scribbles.pdf output.pdf --opacity 0.7
```

### Python API Changes

```python
from pyncode.pyncode import create_ncoded_pdf

# Before: Required list of PNG paths
create_ncoded_pdf(
    'input.pdf',
    ['ncode_0.png', 'ncode_1.png', 'ncode_2.png'],
    'output.pdf'
)

# Now: Can use prefix for auto-detection
create_ncoded_pdf(
    'input.pdf',
    'ncode_',  # Prefix - auto-detects ncode_0.png, ncode_1.png, etc.
    'output.pdf'
)
```
