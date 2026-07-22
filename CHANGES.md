# PyNcode Changes

## Version 1.2.0 (Current)

### Major Correction: Ncode vs. Scribble Requirements

**Fixed a critical misunderstanding**: The two tools have **opposite** requirements:

| Tool | Requirement | Implementation | Text Selectable? |
|------|-------------|----------------|------------------|
| **Ncode Overlay** | Must do K=0 conversion | Rasterizes PDF, CMYK conversion, K=255 for dots, K=0 for background | ❌ NO (required for pen) |
| **Scribble Overlay** | Must preserve structure | Transparent image overlays on original PDF | ✅ YES (required for searchability) |

### Ncode Overlay Changes

**Before (Wrong):** Transparent PNG overlay that preserved PDF structure

**After (Correct):** Full CMYK K-removal conversion like the original NeoLAB SDK

```python
# Algorithm (same as original NeoLAB SDK):
1. Render PDF page to RGB at 600 DPI
2. Convert RGB to CMYK
3. For each pixel:
   - If Ncode dot:   CMYK = (0, 0, 0, 255)  # Pure black - pen sees this as dot
   - If background:  CMYK = (C, M, Y, 0)    # No K - pen ignores this
4. Save as CMYK PNG in new PDF
```

**Why K=0 is required:**
- The Neo smartpen's IR sensor detects K=255 (dots) vs K=0 (background)
- If background has K > 0 (like regular black text), the pen can't distinguish Ncode dots
- PDF must be rasterized - text becomes non-selectable, but the pen works correctly

### Scribble Overlay

**No changes** - was already correctly preserving PDF structure

### CLI Usage

```bash
# Ncode overlay (rasterizes, text NOT selectable - required for pen)
pyncode ncode input.pdf output.pdf ncode_3_28_10_
# Note: Output is rasterized, required for pen detection

# Scribble overlay (preserves PDF, text IS selectable)  
pyncode scribble original.pdf scribbles.pdf output.pdf --color red
# Note: Original PDF structure preserved, text selectable
```

### Recommended Workflow

```bash
# 1. Keep original PDF (selectable text)
# 2. Create Ncoded version for printing
pyncode ncode original.pdf ncoded.pdf ncode_3_28_10_

# 3. Print ncoded.pdf and use with Neo pen

# 4. After writing, overlay scribbles on ORIGINAL (not Ncoded!)
pyncode scribble original.pdf scribbles.pdf annotated.pdf --color red
# annotated.pdf has your handwriting + selectable text
```

### Files Changed

- `pyncode.py`: Completely rewrote `create_ncoded_pdf()` for proper CMYK K-removal
- `README.md`: Clarified different requirements for each tool
- `test_fix.py`: Added tests for both behaviors
