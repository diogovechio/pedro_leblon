@echo off
echo Checking Python installation...

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3 first.
    pause
    exit /b 1
)

set VENV_DIR=venv

if not exist %VENV_DIR%\ (
    echo Creating virtual environment...
    python3 -m venv %VENV_DIR%
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment. Make sure you have Python 3.3+ with venv support.
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat

echo Upgrading pip...
python3 -m pip install --upgrade pip

echo Installing dependencies with trusted hosts...
python3 -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

if %ERRORLEVEL% EQU 0 (
    echo Installation complete!
    echo.
    echo To run the application, first activate the virtual environment:
    echo     %VENV_DIR%\Scripts\activate.bat
    echo Then run the application:
    echo     python run.py
    echo.
    echo You can deactivate the virtual environment when done:
    echo     deactivate
) else (
    echo Installation failed!
)

pause
