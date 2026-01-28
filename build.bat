@echo off
echo Building RoboSell Sending App
echo.

if not exist "venv" (
    echo Creating virtual environment...
    py -m venv venv
    if errorlevel 1 (
        python -m venv venv
        if errorlevel 1 (
            echo ERROR: Failed to create venv
            pause
            exit /b 1
        )
    )
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip setuptools wheel
    pip install pandas selenium beautifulsoup4 requests webdriver-manager
)

call venv\Scripts\activate.bat
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    pip install pyinstaller
)

echo Cleaning build...
echo Closing any running instances...
taskkill /F /IM RoboSell_Sending_App.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
wmic process where "name='RoboSell_Sending_App.exe'" delete >nul 2>&1
timeout /t 3 /nobreak >nul

echo Removing build directories...
if exist "dist\RoboSell_Sending_App.exe" (
    attrib -r dist\RoboSell_Sending_App.exe >nul 2>&1
    del /f /q dist\RoboSell_Sending_App.exe >nul 2>&1
    timeout /t 1 /nobreak >nul
)
if exist "build" (
    attrib -r /s /d build\*.* >nul 2>&1
    rmdir /s /q build 2>nul
    timeout /t 1 /nobreak >nul
)
if exist "dist" (
    attrib -r /s /d dist\*.* >nul 2>&1
    rmdir /s /q dist 2>nul
    timeout /t 1 /nobreak >nul
)
timeout /t 2 /nobreak >nul

echo Building...
if exist "RoboSell_Sending_App.spec" (
    pyinstaller RoboSell_Sending_App.spec --noconfirm --clean
    if errorlevel 1 (
        echo.
        echo First build attempt failed, retrying after cleanup...
        timeout /t 5 /nobreak >nul
        taskkill /F /IM python.exe >nul 2>&1
        timeout /t 3 /nobreak >nul
        pyinstaller RoboSell_Sending_App.spec --noconfirm --clean
        if errorlevel 1 (
            echo.
            echo Build failed after retry. Please:
            echo 1. Close File Explorer windows
            echo 2. Close any IDE/editor
            echo 3. Wait 30 seconds
            echo 4. Try again
            pause
            exit /b 1
        )
    )
) else (
    echo ERROR: RoboSell_Sending_App.spec not found!
    pause
    exit /b 1
)

if exist "dist\RoboSell_Sending_App.exe" (
    echo.
    echo Build successful!
    echo Executable: dist\RoboSell_Sending_App.exe
) else (
    echo Build failed!
)

pause
