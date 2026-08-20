# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

from b2_photo_manager import __version__

ROOT = Path(SPECPATH).parents[1]
APP_NAME = "B² Photo Manager"
BUNDLE_IDENTIFIER = "de.bsquared.b2photomanager"
ICON = ROOT / "assets" / "icon.icns"

qt_plugin_datas = collect_data_files(
    "PySide6",
    includes=[
        "Qt/plugins/platforms/libqcocoa.dylib",
        "Qt/plugins/imageformats/libqgif.dylib",
        "Qt/plugins/imageformats/libqicns.dylib",
        "Qt/plugins/imageformats/libqico.dylib",
        "Qt/plugins/imageformats/libqjpeg.dylib",
        "Qt/plugins/imageformats/libqtiff.dylib",
        "Qt/plugins/imageformats/libqwebp.dylib",
        "Qt/plugins/styles/libqmacstyle.dylib",
    ],
)

asset_datas = collect_data_files("b2_photo_manager.assets")

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=qt_plugin_datas + asset_datas,
    hiddenimports=[
        "PIL.Image",
        "PIL.ImageOps",
        "PIL.ImageQt",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtGraphs",
        "PySide6.QtHelp",
        "PySide6.QtMultimedia",
        "PySide6.QtNetworkAuth",
        "PySide6.QtOpenGL",
        "PySide6.QtPdf",
        "PySide6.QtPrintSupport",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtSql",
        "PySide6.QtStateMachine",
        "PySide6.QtSvg",
        "PySide6.QtTest",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets",
        "PySide6.QtXml",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if ICON.exists() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=str(ICON) if ICON.exists() else None,
    bundle_identifier=BUNDLE_IDENTIFIER,
    info_plist={
        "CFBundleDisplayName": APP_NAME,
        "CFBundleName": APP_NAME,
        "CFBundleShortVersionString": __version__,
        "CFBundleVersion": __version__,
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.photography",
    },
)
