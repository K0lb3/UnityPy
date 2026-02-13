#!/usr/bin/env python3
"""
UnityPy Explorer — One-click cross-platform build script.

Usage:
    python build.py                     # Build for the current platform/arch
    python build.py --target mac-arm64  # macOS Apple Silicon
    python build.py --target mac-intel  # macOS Intel
    python build.py --target mac-all    # macOS arm64 + Intel (two separate builds)
    python build.py --target win64      # Windows 64-bit
    python build.py --target win32      # Windows 32-bit
    python build.py --target win-all    # Windows 32 + 64 bit
    python build.py --target all        # All targets valid for the current OS
    python build.py --list              # List available targets
    python build.py --clean             # Remove build/dist before building

Notes:
    - PyInstaller does NOT support cross-compilation.
      macOS targets can only be built on macOS; Windows targets on Windows.
    - For Windows 32-bit you need a 32-bit Python interpreter.
    - On macOS, building for Intel (x86_64) from an arm64 host requires
      Rosetta 2 and an x86_64 Python or a universal2 Python installation.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════════════

APP_NAME = "UnityPy Explorer"
EXE_NAME = "UnityPyExplorer"
VERSION = "1.0.0"
BUNDLE_ID = "com.unitypy.explorer"

PROJECT_ROOT = Path(__file__).resolve().parent
ENTRY_SCRIPT = PROJECT_ROOT / "run_explorer.py"
RUNTIME_HOOK = PROJECT_ROOT / "rthook_archspec.py"
ICON_ICNS = PROJECT_ROOT / "UnityPyExplorer.icns"   # macOS icon
ICON_ICO = PROJECT_ROOT / "UnityPyExplorer.ico"      # Windows icon

DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

# All defined targets
TARGETS = {
    "mac-arm64": {"os": "Darwin", "arch": "arm64",   "desc": "macOS Apple Silicon (M1–M5)"},
    "mac-intel": {"os": "Darwin", "arch": "x86_64",  "desc": "macOS Intel"},
    "win64":     {"os": "Windows", "arch": "x86_64",  "desc": "Windows 64-bit"},
    "win32":     {"os": "Windows", "arch": "x86",     "desc": "Windows 32-bit"},
}

# Composite targets
COMPOSITE = {
    "mac-all": ["mac-arm64", "mac-intel"],
    "win-all": ["win64", "win32"],
    "all":     [],  # resolved at runtime based on OS
}

# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def log(msg: str, level: str = "INFO"):
    colors = {"INFO": "\033[36m", "OK": "\033[32m", "WARN": "\033[33m", "ERR": "\033[31m"}
    reset = "\033[0m"
    c = colors.get(level, "")
    try:
        print(f"{c}[{level}]{reset} {msg}")
    except UnicodeEncodeError:
        print(f"{c}[{level}]{reset} {msg.encode('ascii', 'replace').decode('ascii')}")


def run_cmd(cmd: list[str], cwd: Path | None = None):
    """Run a command, stream output, return exit code."""
    log(f"Running: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print(line, end="")
    proc.wait()
    return proc.returncode


def current_os() -> str:
    s = platform.system()
    return s  # "Darwin" or "Windows" or "Linux"


def current_arch() -> str:
    m = platform.machine().lower()
    if m in ("arm64", "aarch64"):
        return "arm64"
    elif m in ("x86_64", "amd64"):
        return "x86_64"
    elif m in ("i386", "i686", "x86"):
        return "x86"
    return m


def resolve_targets(target_name: str) -> list[str]:
    """Resolve a target name (possibly composite) into a list of concrete targets."""
    if target_name in TARGETS:
        return [target_name]

    if target_name == "all":
        # All four targets — cross-platform ones will be skipped gracefully
        return list(TARGETS.keys())

    if target_name in COMPOSITE:
        return COMPOSITE[target_name]

    return [target_name]


def auto_detect_targets() -> list[str]:
    """Return ALL build targets for the current OS (both architectures)."""
    os_name = current_os()
    targets = [k for k, v in TARGETS.items() if v["os"] == os_name]
    if not targets:
        log(f"No targets available for {os_name}", "ERR")
        sys.exit(1)
    return targets


def validate_target(target: str) -> bool:
    """Check if the target can be built on this machine. Returns False to skip."""
    info = TARGETS[target]
    os_name = current_os()
    if info["os"] != os_name:
        log(f"SKIP '{target}' — requires {info['os']}, but you are on {os_name}.", "WARN")
        log("  (PyInstaller does not support cross-compilation.)", "WARN")
        log(f"  To build this target, run build.py on a {info['os']} machine.", "WARN")
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════
#  Spec-file generator
# ═══════════════════════════════════════════════════════════════════════

def generate_spec(target: str) -> Path:
    """Generate a PyInstaller .spec file for the given target and return its path."""
    info = TARGETS[target]
    is_mac = info["os"] == "Darwin"
    is_win = info["os"] == "Windows"
    arch = info["arch"]

    spec_name = f"UnityPyExplorer_{target}.spec"
    spec_path = PROJECT_ROOT / spec_name

    # Output sub-directory
    out_name = f"{EXE_NAME}-{target}"

    # Runtime hooks
    rt_hooks = f"[{repr(str(RUNTIME_HOOK))}]" if RUNTIME_HOOK.exists() else "[]"

    # Platform-specific values
    argv_emu = "True" if is_mac else "False"
    fmod_comment = "# fmod_toolkit native library (libfmod.dylib)" if is_mac else "# fmod_toolkit native library (fmod.dll)"

    lines: list[str] = []
    W = lines.append  # shorthand

    W("# -*- mode: python ; coding: utf-8 -*-")
    W(f"# Auto-generated spec for target: {target} ({info['desc']})")
    W("# Do not edit manually — regenerated by build.py")
    W("")
    W("import os")
    W("import sys")
    W("from PyInstaller.utils.hooks import collect_submodules, collect_data_files")
    W("")
    W("block_cipher = None")
    W(f"PROJECT_ROOT = {repr(str(PROJECT_ROOT))}")
    W("")
    W("# ── Hidden imports ─────────────────────────────────────────────────")
    W("hiddenimports = []")
    W("hiddenimports += collect_submodules('UnityPy')")
    W("hiddenimports += [")
    W("    'UnityPyExplorer',")
    W("    'UnityPyExplorer.main',")
    W("    'UnityPyExplorer.asset_browser',")
    W("    'UnityPyExplorer.preview_panel',")
    W("    'UnityPyExplorer.property_panel',")
    W("    'UnityPyExplorer.dialogs',")
    W("    'UnityPyExplorer.helpers',")
    W("    'UnityPyExplorer.style',")
    W("]")
    W("hiddenimports += collect_submodules('lz4')")
    W("hiddenimports += ['brotli', 'fsspec', 'PIL', 'attrs', 'attr']")
    W("hiddenimports += [")
    W("    'PySide6.QtCore',")
    W("    'PySide6.QtGui',")
    W("    'PySide6.QtWidgets',")
    W("]")
    W("")
    W("try:")
    W("    import PySide6.QtMultimedia")
    W("    hiddenimports += ['PySide6.QtMultimedia']")
    W("except ImportError:")
    W("    pass")
    W("")
    W("for mod in ['fmod_toolkit', 'pyfmodex']:")
    W("    try:")
    W("        __import__(mod)")
    W("        hiddenimports.append(mod)")
    W("        hiddenimports += collect_submodules(mod)")
    W("    except ImportError:")
    W("        pass")
    W("")
    W("for mod in ['texture2ddecoder', 'etcpak', 'astc_encoder', 'archspec']:")
    W("    try:")
    W("        __import__(mod)")
    W("        hiddenimports.append(mod)")
    W("        hiddenimports += collect_submodules(mod)")
    W("    except ImportError:")
    W("        pass")
    W("")
    W("# ── Data files ─────────────────────────────────────────────────────")
    W("datas = []")
    W("")
    W("unitypy_resources = os.path.join(PROJECT_ROOT, 'UnityPy', 'resources')")
    W("if os.path.isdir(unitypy_resources):")
    W("    datas.append((unitypy_resources, 'UnityPy/resources'))")
    W("")
    W("fmod_dir = os.path.join(PROJECT_ROOT, 'UnityPy', 'lib', 'FMOD')")
    W("if os.path.isdir(fmod_dir):")
    W("    datas.append((fmod_dir, 'UnityPy/lib/FMOD'))")
    W("")
    W(fmod_comment)
    W("try:")
    W("    import fmod_toolkit")
    W("    fmod_pkg_dir = os.path.dirname(fmod_toolkit.__file__)")
    W("    fmod_lib_dir = os.path.join(fmod_pkg_dir, 'libfmod')")
    W("    if os.path.isdir(fmod_lib_dir):")
    W("        datas.append((fmod_lib_dir, 'fmod_toolkit/libfmod'))")
    W("    datas += collect_data_files('fmod_toolkit')")
    W("except ImportError:")
    W("    pass")
    W("")
    W("try:")
    W("    import archspec")
    W("    datas += collect_data_files('archspec')")
    W("except ImportError:")
    W("    pass")
    W("")
    W("# ── Analysis ───────────────────────────────────────────────────────")
    W("a = Analysis(")
    W(f"    [{repr(str(ENTRY_SCRIPT))}],")
    W("    pathex=[PROJECT_ROOT],")
    W("    binaries=[],")
    W("    datas=datas,")
    W("    hiddenimports=hiddenimports,")
    W("    hookspath=[],")
    W("    hooksconfig={},")
    W(f"    runtime_hooks={rt_hooks},")
    W("    excludes=[")
    W("        'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras',")
    W("        'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',")
    W("        'PySide6.QtBluetooth', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',")
    W("        'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtLocation',")
    W("        'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtQuick',")
    W("        'PySide6.QtQuick3D', 'PySide6.QtQuickWidgets', 'PySide6.QtRemoteObjects',")
    W("        'PySide6.QtScxml', 'PySide6.QtSensors', 'PySide6.QtSerialBus',")
    W("        'PySide6.QtSerialPort', 'PySide6.QtSpatialAudio', 'PySide6.QtStateMachine',")
    W("        'PySide6.QtTest', 'PySide6.QtWebChannel', 'PySide6.QtWebEngine',")
    W("        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',")
    W("        'PySide6.QtWebSockets',")
    W("        'tkinter', 'unittest', 'xmlrpc', 'pydoc', 'doctest',")
    W("    ],")
    W("    noarchive=False,")
    W("    optimize=0,")
    W(")")
    W("")
    W("# ── PYZ ────────────────────────────────────────────────────────────")
    W("pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)")
    W("")
    W("# ── EXE ────────────────────────────────────────────────────────────")
    W("exe = EXE(")
    W("    pyz,")
    W("    a.scripts,")
    W("    [],")
    W("    exclude_binaries=True,")
    W(f"    name='{EXE_NAME}',")
    W("    debug=False,")
    W("    bootloader_ignore_signals=False,")
    W("    strip=False,")
    W("    upx=False,")
    W("    console=False,")
    W("    disable_windowed_traceback=False,")
    W(f"    argv_emulation={argv_emu},")
    if is_mac:
        W(f"    target_arch={repr(arch)},")
    W("    codesign_identity=None,")
    W("    entitlements_file=None,")
    # Icon
    if is_mac and ICON_ICNS.exists():
        W(f"    icon={repr(str(ICON_ICNS))},")
    elif is_win and ICON_ICO.exists():
        W(f"    icon={repr(str(ICON_ICO))},")
    W(")")
    W("")
    W("# ── COLLECT ────────────────────────────────────────────────────────")
    W("coll = COLLECT(")
    W("    exe,")
    W("    a.binaries,")
    W("    a.datas,")
    W("    strip=False,")
    W("    upx=False,")
    W("    upx_exclude=[],")
    W(f"    name='{out_name}',")
    W(")")
    W("")

    # macOS BUNDLE
    if is_mac:
        W("# ── BUNDLE (macOS .app) ────────────────────────────────────────────")
        W("app = BUNDLE(")
        W("    coll,")
        W(f"    name='{APP_NAME}.app',")
        if ICON_ICNS.exists():
            W(f"    icon={repr(str(ICON_ICNS))},")
        W(f"    bundle_identifier='{BUNDLE_ID}',")
        W("    info_plist={")
        W(f"        'CFBundleName': '{APP_NAME}',")
        W(f"        'CFBundleDisplayName': '{APP_NAME}',")
        W(f"        'CFBundleVersion': '{VERSION}',")
        W(f"        'CFBundleShortVersionString': '{VERSION}',")
        W("        'CFBundleInfoDictionaryVersion': '6.0',")
        W("        'CFBundlePackageType': 'APPL',")
        W("        'CFBundleSignature': 'UPEX',")
        W("        'LSMinimumSystemVersion': '13.0',")
        W("        'NSHighResolutionCapable': True,")
        W("        'NSRequiresAquaSystemAppearance': False,")
        W("        'CFBundleDocumentTypes': [")
        W("            {")
        W("                'CFBundleTypeName': 'Unity Asset Bundle',")
        W("                'CFBundleTypeRole': 'Viewer',")
        W("                'LSItemContentTypes': ['public.data'],")
        W("                'CFBundleTypeExtensions': [")
        W("                    'unity3d', 'assets', 'bundle', 'asset',")
        W("                    'apk', 'zip',")
        W("                ],")
        W("            },")
        W("        ],")
        W("    },")
        W(")")
    else:
        W("# No BUNDLE on Windows")
    W("")

    spec_content = "\n".join(lines) + "\n"
    spec_path.write_text(spec_content, encoding="utf-8")
    log(f"Generated spec: {spec_path.name}")
    return spec_path


# ═══════════════════════════════════════════════════════════════════════
#  Build runner
# ═══════════════════════════════════════════════════════════════════════

def build_target(target: str, clean: bool = False):
    """Build one target."""
    info = TARGETS[target]
    if not validate_target(target):
        return None  # skipped (cross-platform)

    log(f"{'=' * 60}")
    log(f"Building: {target}  -  {info['desc']}")
    log(f"{'=' * 60}")

    if clean:
        for d in [BUILD_DIR, DIST_DIR]:
            if d.exists():
                log(f"Cleaning {d}")
                shutil.rmtree(d, ignore_errors=True)

    spec_path = generate_spec(target)

    t0 = time.time()
    cmd = [sys.executable, "-m", "PyInstaller", str(spec_path), "--noconfirm"]
    rc = run_cmd(cmd, cwd=PROJECT_ROOT)

    elapsed = time.time() - t0

    if rc != 0:
        log(f"Build FAILED for {target} (exit code {rc})", "ERR")
        return False

    # Report output
    out_name = f"{EXE_NAME}-{target}"
    is_mac = info["os"] == "Darwin"

    if is_mac:
        app_path = DIST_DIR / f"{APP_NAME}.app"
        final_path = DIST_DIR / f"{APP_NAME}-{target}.app"
        if app_path.exists():
            # Rename to include target in name
            if final_path.exists():
                shutil.rmtree(final_path)
            app_path.rename(final_path)
            log(f"Output: {final_path}", "OK")
        else:
            log(f"Output: {DIST_DIR / out_name}", "OK")
    else:
        exe_path = DIST_DIR / out_name / f"{EXE_NAME}.exe"
        if exe_path.exists():
            log(f"Output: {exe_path}", "OK")
        else:
            log(f"Output: {DIST_DIR / out_name}", "OK")

    log(f"Build completed in {elapsed:.1f}s", "OK")
    return True


# ═══════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════

def list_targets():
    """Print available targets."""
    os_name = current_os()
    arch = current_arch()
    print(f"\nCurrent platform: {os_name} / {arch}\n")
    print(f"{'Target':<14} {'Platform':<10} {'Arch':<8} {'Description':<35} {'Available'}")
    print(f"{'-' * 14} {'-' * 10} {'-' * 8} {'-' * 35} {'-' * 10}")
    for name, info in TARGETS.items():
        available = "Y" if info["os"] == os_name else "N (need " + info["os"] + ")"
        print(f"{name:<14} {info['os']:<10} {info['arch']:<8} {info['desc']:<35} {available}")
    print()
    print("Composite targets:")
    print(f"  mac-all    = mac-arm64 + mac-intel")
    print(f"  win-all    = win64 + win32")
    print(f"  all        = all 4 targets (cross-platform ones skipped gracefully)")
    print()
    print(f"Default (no --target): builds all targets for current OS ({os_name})")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="UnityPy Explorer — Cross-platform build script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python build.py                      Build all targets for current OS
              python build.py --target all         Build all 4 targets (skips cross-platform)
              python build.py --target mac-arm64   Build for macOS Apple Silicon only
              python build.py --target mac-intel   Build for macOS Intel only
              python build.py --target mac-all     Build both macOS architectures
              python build.py --target win64       Build for Windows 64-bit only
              python build.py --target win32       Build for Windows 32-bit only
              python build.py --target win-all     Build both Windows architectures
              python build.py --clean              Clean build/ & dist/ before building
              python build.py --list               Show all targets
        """),
    )
    parser.add_argument(
        "--target", "-t",
        default=None,
        help="Build target (mac-arm64, mac-intel, mac-all, win64, win32, win-all, all)",
    )
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="Remove build/ and dist/ before building",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        dest="list_targets",
        help="List available build targets",
    )
    args = parser.parse_args()

    if args.list_targets:
        list_targets()
        return

    # Resolve target — default: all targets for current OS
    if args.target:
        target_name = args.target
    else:
        target_name = None  # will use auto_detect_targets()

    if target_name is None:
        targets = auto_detect_targets()
    else:
        targets = resolve_targets(target_name)

    if not targets:
        log(f"Unknown target: {target_name}", "ERR")
        list_targets()
        sys.exit(1)

    log(f"Build plan: {', '.join(targets)}")
    log(f"Python: {sys.executable} ({platform.python_version()})")
    log(f"Platform: {current_os()} / {current_arch()}")
    print()

    # Check PyInstaller is available
    try:
        import PyInstaller
        log(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        log("PyInstaller not found. Install it:  pip install pyinstaller", "ERR")
        sys.exit(1)

    results = {}
    for t in targets:
        result = build_target(t, clean=args.clean)
        results[t] = result  # True=ok, False=failed, None=skipped
        print()

    # Summary
    print()
    log("=" * 60)
    log("Build Summary")
    log("=" * 60)
    has_failure = False
    for t, result in results.items():
        if result is None:
            log(f"  -  {t:<14} {TARGETS[t]['desc']}  (skipped - wrong OS)", "WARN")
        elif result:
            log(f"  *  {t:<14} {TARGETS[t]['desc']}", "OK")
        else:
            log(f"  X  {t:<14} {TARGETS[t]['desc']}", "ERR")
            has_failure = True

    built = [t for t, r in results.items() if r is True]
    skipped = [t for t, r in results.items() if r is None]
    failed = [t for t, r in results.items() if r is False]

    print()
    if built:
        log(f"Built {len(built)} target(s). Output in: {DIST_DIR}", "OK")
    if skipped:
        os_name = current_os()
        other_os = "Windows" if os_name == "Darwin" else "macOS"
        log(f"Skipped {len(skipped)} target(s) - run build_app.py on {other_os} to build them.", "WARN")
    if has_failure:
        log("Some builds failed. Check the output above.", "ERR")
        sys.exit(1)


if __name__ == "__main__":
    main()
