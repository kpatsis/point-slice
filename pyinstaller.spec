# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path.cwd()

block_cipher = None

a = Analysis(
    ['point_slice_studio_gui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src', 'src'),  # Include the src directory
        ('tests/testdata', 'tests/testdata'),  # Include test data
        ('README.md', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox', 
        'tkinter.scrolledtext',
        'ezdxf',
        'ezdxf.document',
        'ezdxf.entities',
        'ezdxf.layouts',
        'ezdxf.math',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Point_Slice_Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app, no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='point_slice_studio.ico',  # Add an icon file path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Point_Slice_Studio',
) 