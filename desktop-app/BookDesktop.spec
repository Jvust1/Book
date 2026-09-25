from pathlib import Path

project_root = Path(SPEC).resolve().parent.parent
build_root = project_root / ".build" / "desktop"

datas = [
    (str(build_root / "web"), "desktop_web"),
    (str(project_root / "books"), "books"),
    (str(project_root / "courses"), "courses"),
    (str(project_root / "library"), "library"),
]

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "webview.platforms.edgechromium",
]

a = Analysis(
    [str(project_root / "desktop-app" / "launcher.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "numpy", "PIL.ImageQt"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Book-0.1.4-Windows-x64",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(build_root / "book.ico"),
)
