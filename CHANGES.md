# PyNcode Changes

## Version 1.2.0 (Current)

### Major Correction

**Ncode vs. Scribble requirements clarified:**

I mistakenly applied the "preserve PDF structure" requirement to BOTH tools, but they have **opposite** requirements:

1. **Ncode overlay (`ncode` command)**: Must rasterize and do K=0 conversion
   - Text becomes non-selectable - **this is required**
   - The Neo smartpen needs to distinguish Ncode dots (K=255) from background (K=0)
   - Follows the original NeoLAB SDK's CMYK conversion approach

2. **Scribble overlay (`scribble` command)**: Must preserve PDF structure
   - Text remains selectable - **this is required**
   - Original PDF is not modified
   - Scribbles are added as transparent overlays

### Changes in 1.2.0

#### Ncode Overlay (`ncode` command)

**Before (wrong):** Transparent PNG overlay, preserved PDF structure, text selectable

**After (correct):** Full CMYK K-removal conversion, rasterizes PDF, text NOT selectable

```python
# Key algorithm - same as original NeoLAB SDK
for each pixel:
    if is_ncode_dot:
        CMYK = (0, 0, 0, 255)  # Pure black - pen sees this as a dot
    else:
        CMYK = (255-R, 255-G, 255-B, 0)  # No K component - pen ignores this
```

**Why this is required:**
- The Neo smartpen uses an IR camera to detect Ncode
- The pen distinguishes dots (K=255) from background (K=0)
- If background has K > 0 (like regular text), pen can't tell the difference
- Text becomes non-selectable, but the pen works correctly

#### Scribble Overlay (`scribble` command)

**Before (correct):** Image overlay, preserved PDF structure, text selectable

**After (correct):** No change - this was already correct

```python
# Scribbles are added as transparent image overlays
bg_page.insert_image(rect, stream=img_bytes, overlay=True)
```

**Why this works:**
- Original PDF is not modified
- Scribbles are overlaid on top
- Text remains fully selectable and searchable

### CLI Changes

```bash
# Ncode overlay (rasterizes, text NOT selectable)
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
# Print ncoded.pdf and use with Neo smartpen

# 3. After writing, overlay scribbles on ORIGINAL (not Ncoded)
pyncode scribble original.pdf scribbles.pdf annotated.pdf --color red
# annotated.pdf has your handwriting + selectable text
```

### Why Not Overlay Scribbles on Ncoded PDF?

If you overlay scribbles on the Ncoded PDF:
- The Ncoded PDF is already rasterized
- Text is not selectable
- You lose searchability

Better: Keep original, create separate Ncoded version for printing, overlay scribbles on original.

### Files Changed

- `pyncode.py`: Completely rewrote Ncode overlay to use CMYK K-removal
- `README.md`: Clarified different requirements for each tool
- `test_fix.py`: Added tests for both behaviors
- `CHANGES.md`: This changelog
