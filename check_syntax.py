#!/usr/bin/env python3
"""Check Python syntax of all source files."""
import sys
import py_compile

files = [
    'pyncode.py',
    '__init__.py',
    'test_pyncode.py',
    'test_import.py',
]

errors = []
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"✓ {f}: OK")
    except py_compile.PyCompileError as e:
        errors.append((f, str(e)))
        print(f"✗ {f}: {e}")

if errors:
    print(f"\n{len(errors)} file(s) with errors")
    sys.exit(1)
else:
    print(f"\nAll {len(files)} files passed syntax check!")
    sys.exit(0)
