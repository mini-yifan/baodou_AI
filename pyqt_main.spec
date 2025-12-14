# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pyqt_main.py'],
    pathex=[],
    binaries=[],
    datas=[('favicon.ico', '.'), ('imgs/*', 'imgs'), ('get_next_action_AI_doubao.txt', '.'), ('cv_shot_doubao.py', '.'), ('vl_model_test_doubao2.py', '.')],
    hiddenimports=['cv_shot_doubao', 'vl_model_test_doubao2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pyqt_main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['favicon.ico'],
)
