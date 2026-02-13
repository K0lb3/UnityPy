#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#  UnityPy Explorer — macOS one-click build script
#
#  Default: builds BOTH arm64 (Apple Silicon) + Intel architectures
#
#  Usage:
#    ./build.sh              Build both arm64 + Intel (default)
#    ./build.sh arm64        Build Apple Silicon only
#    ./build.sh intel        Build Intel only
#    ./build.sh all          Build all 4 targets (skips Windows)
#    ./build.sh clean        Clean + build both architectures
# ──────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Color helpers ──
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[ OK ]${NC} $*"; }
err()   { echo -e "${RED}[ERR ]${NC} $*"; }

# ── Check Python ──
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    err "Python not found. Please install Python 3.9+."
    exit 1
fi

info "Using Python: $($PY --version 2>&1) at $($PY -c 'import sys; print(sys.executable)')"

# ── Check dependencies ──
$PY -c "import PyInstaller" 2>/dev/null || {
    err "PyInstaller not found. Installing..."
    $PY -m pip install pyinstaller
}

$PY -c "import PySide6" 2>/dev/null || {
    err "PySide6 not found. Installing..."
    $PY -m pip install PySide6
}

# ── Parse argument ──
TARGET="${1:-}"
EXTRA_ARGS=""

case "$TARGET" in
    arm64|m1|m2|m3|m4|m5|apple)
        EXTRA_ARGS="--target mac-arm64"
        ;;
    intel|x86|x86_64)
        EXTRA_ARGS="--target mac-intel"
        ;;
    all)
        EXTRA_ARGS="--target all"
        ;;
    clean)
        EXTRA_ARGS="--clean"
        ;;
    "")
        # Default: build both macOS architectures
        EXTRA_ARGS="--target mac-all"
        ;;
    *)
        err "Unknown argument: $TARGET"
        echo "Usage: $0 [arm64|intel|all|clean]"
        exit 1
        ;;
esac

# ── Run build ──
info "Starting build..."
echo ""
$PY build_app.py $EXTRA_ARGS

# ── Done ──
echo ""
ok "Build script finished. Check dist/ for output."
echo ""

# Open dist folder in Finder
if [[ -d "dist" ]]; then
    open dist/ 2>/dev/null || true
fi
