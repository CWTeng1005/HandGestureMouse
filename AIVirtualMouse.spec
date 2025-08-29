# -*- mode: python ; coding: utf-8 -*-
# Full-featured spec to bundle MediaPipe + OpenCV + NumPy + Pygame + SE assets

from PyInstaller.utils.hooks import collect_all

# Collect everything from these heavy packages
_pkgs = ["mediapipe", "cv2", "numpy", "pygame"]
_datas, _binaries, _hidden = [], [], []
for _p in _pkgs:
    d, b, h = collect_all(_p)
    _datas += d
    _binaries += b
    _hidden += h

block_cipher = None

a = Analysis(
    ['AIVirtualMouse.py'],
    pathex=[],
    binaries=_binaries,
    datas=_datas + [
        ('SE/*.mp3', 'SE'),
    ],
    hiddenimports=_hidden + ['win32gui', 'win32con'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AIVirtualMouse',
    debug=False,               # 调试期可改 True 以便看到异常
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,             # 调试期可改 True 打开控制台
    icon=None,
)
