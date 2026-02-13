@echo off
REM ──────────────────────────────────────────────────────────────
REM  UnityPy Explorer — Windows one-click build script
REM
REM  Default: builds BOTH 64-bit + 32-bit architectures
REM
REM  Usage:
REM    build.bat              Build both 64-bit + 32-bit (default)
REM    build.bat 64           Build Windows 64-bit only
REM    build.bat 32           Build Windows 32-bit only
REM    build.bat all          Build all 4 targets (skips macOS)
REM    build.bat clean        Clean + build both architectures
REM ──────────────────────────────────────────────────────────────

cd /d "%~dp0"

echo ══════════════════════════════════════════════
echo  UnityPy Explorer — Windows Build
echo ══════════════════════════════════════════════
echo.

REM ── Find Python ──
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY=python
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set PY=python3
    ) else (
        echo [ERR] Python not found. Please install Python 3.9+.
        pause
        exit /b 1
    )
)

echo [INFO] Using Python:
%PY% --version

REM ── Check dependencies ──
%PY% -c "import PyInstaller" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing PyInstaller...
    %PY% -m pip install pyinstaller
)

%PY% -c "import PySide6" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing PySide6...
    %PY% -m pip install PySide6
)

REM ── Parse argument ──
set TARGET=%1
set EXTRA_ARGS=

if "%TARGET%"=="" (
    REM Default: build both Windows architectures
    set EXTRA_ARGS=--target win-all
    goto :run
)
if "%TARGET%"=="64" (
    set EXTRA_ARGS=--target win64
    goto :run
)
if "%TARGET%"=="32" (
    set EXTRA_ARGS=--target win32
    goto :run
)
if "%TARGET%"=="all" (
    set EXTRA_ARGS=--target all
    goto :run
)
if "%TARGET%"=="clean" (
    set EXTRA_ARGS=--clean
    goto :run
)

echo [ERR] Unknown argument: %TARGET%
echo Usage: build.bat [64^|32^|all^|clean]
pause
exit /b 1

:run
echo.
echo [INFO] Starting build...
echo.
%PY% build_app.py %EXTRA_ARGS%

echo.
echo [OK] Build script finished. Check dist\ for output.
echo.

REM Open dist folder in Explorer
if exist "dist" (
    explorer dist
)

pause
