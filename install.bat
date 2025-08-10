@echo off
REM Project Sage Installation Script for Windows
REM Automatically sets up virtual environment and installs Sage

echo 🤖 Project Sage Installation Script
echo ==========================================

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

python --version
echo ✅ Python found

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo ❌ Please run this script from the project-sage directory
    echo Usage: cd project-sage ^&^& install.bat
    pause
    exit /b 1
)

if not exist "sage" (
    echo ❌ Please run this script from the project-sage directory
    echo Usage: cd project-sage ^&^& install.bat
    pause
    exit /b 1
)

REM Check for Tesseract
echo Checking Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Tesseract OCR not found
    echo Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
    echo After installation, restart this script
    pause
    exit /b 1
)

echo ✅ Tesseract OCR found

REM Remove existing virtual environment
if exist "sage-env" (
    echo ⚠️  Virtual environment already exists. Removing...
    rmdir /s /q sage-env
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv sage-env
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment created

REM Activate virtual environment
echo Activating virtual environment...
call sage-env\Scripts\activate
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment activated

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo ❌ Failed to upgrade pip
    pause
    exit /b 1
)
echo ✅ pip upgraded

REM Install Project Sage
echo Installing Project Sage...
pip install -e .
if errorlevel 1 (
    echo ❌ Failed to install Project Sage
    pause
    exit /b 1
)
echo ✅ Project Sage installed

REM Verify installation
echo Verifying installation...
sage --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Installation verification failed
    pause
    exit /b 1
)

sage --version
echo ✅ Installation verified

echo.
echo 🎉 Project Sage installed successfully!
echo.
echo 📋 Next Steps:
echo 1. Navigate to your project directory:
echo    cd C:\path\to\your\project
echo.
echo 2. Activate the Sage environment:
echo    %CD%\sage-env\Scripts\activate
echo.
echo 3. Initialize Sage for your project:
echo    sage setup
echo.
echo 4. Index your documents:
echo    sage update
echo.
echo 5. Start using Sage:
echo    sage chat
echo.
echo 💡 Pro Tip: For Vietnamese documents, choose Google Gemini during setup!
echo.
echo 📚 Documentation: https://github.com/yourusername/project-sage

pause