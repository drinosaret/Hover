# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['hover.py'],
    pathex=[],
    binaries=[],
    datas=[('README.md', '.'), ('hover_icon.ico', '.')],
    hiddenimports=['win32gui', 'win32con', 'win32api'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest', 'unittest', 'pip', 'setuptools',
        '_bz2', '_lzma', 'gzip',  # Remove some compression modules
        '_hashlib', 'hashlib', '_blake2',  # Remove crypto-related modules
        '_ssl', 'ssl', 'cryptography'  # Remove more crypto modules
    ],
    win_no_prefer_redirects=False,
    cipher=None,
    noarchive=False,  # Need this for basic functionality
)

# Create PYZ without compression
pyz = PYZ(a.pure, cipher=None)

exe = EXE(
    pyz,  # Need this for imports to work
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='hover',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='hover_icon.ico',
)
