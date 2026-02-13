@echo off
REM Set code page to UTF-8
chcp 65001 >nul

echo Starting to build AutoDoor OCR System (Windows version)...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not added to environment variables
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: pip is not available
    pause
    exit /b 1
)

REM Verify module structure
echo Verifying module structure...
for %%m in (core ui modules input utils) do (
    if exist "%%m" (
        echo [OK] Module '%%m' found
    ) else (
        echo [ERROR] Module '%%m' not found
        pause
        exit /b 1
    )
)

REM Delete old virtual environment if it exists
if exist venv (
    echo Deleting old virtual environment...
    rmdir /s /q venv
)

REM Create new virtual environment
echo Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo Warning: Failed to create virtual environment, will use current Python environment
) else (
    echo Activating virtual environment...
    call venv\Scripts\activate
    echo Updating pip...
    pip install --upgrade pip
)

REM Install six library first to ensure it's correctly installed
echo Installing six library...
pip install "six>=1.16.0"
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install six library
    pause
    exit /b 1
)

REM Install other dependencies
echo Installing other dependencies...
pip install -r requirements.txt pyinstaller
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Clean old build files
if exist build (
    echo Cleaning old build files...
    rmdir /s /q build
)
if exist dist (
    echo Cleaning old distribution files...
    rmdir /s /q dist
)

REM Build with PyInstaller, force rebuild
echo Building with PyInstaller...
pyinstaller autodoor.spec --noconfirm --clean
if %ERRORLEVEL% neq 0 (
    echo Error: Build failed
    pause
    exit /b 1
)

REM Verify build output
if exist "dist\autodoor\autodoor.exe" (
    echo [OK] Build successful: autodoor.exe found
    dir "dist\autodoor\autodoor.exe"
) else (
    echo [ERROR] Build failed: autodoor.exe not found
    pause
    exit /b 1
)

echo.
echo Build successful!
echo Executable location: dist\autodoor\autodoor.exe
echo Please copy the entire dist\autodoor directory to the target machine to run
echo.
pause
