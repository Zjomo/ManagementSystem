﻿﻿@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo   Competition Management System - Startup Script
echo ========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found, creating...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)

echo [1/3] Installing root dependencies...
"venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo Failed to install root dependencies!
    pause
    exit /b 1
)

echo [2/3] Starting Smart Mermaid tool (port 3000)...
pushd "utils\smart-mermaid"
if exist "package.json" (
    if not exist "node_modules" (
        echo Installing Smart Mermaid dependencies...
        call npm install --loglevel=error
    )
    start "" /min cmd /c "npm run dev"
) else (
    echo Smart Mermaid folder not found, skipping.
)
popd

set "PRESENTON_FASTAPI_PORT=3002"
set "PRESENTON_NEXTJS_PORT=3001"
set "PRESENTON_APP_DATA=%~dp0utils\presenton-main\app_data"
if not exist "%PRESENTON_APP_DATA%" mkdir "%PRESENTON_APP_DATA%"
set "PRESENTON_APP_DATA=%PRESENTON_APP_DATA:\=/%"
set "APP_DATA_DIRECTORY=%PRESENTON_APP_DATA%"
set "PRESENTON_TEMP_DIRECTORY=%PRESENTON_APP_DATA%/temp"
if not exist "%PRESENTON_TEMP_DIRECTORY%" mkdir "%PRESENTON_TEMP_DIRECTORY%"
set "PRESENTON_TEMP_DIRECTORY=%PRESENTON_TEMP_DIRECTORY:\=/%"
set "TEMP_DIRECTORY=%PRESENTON_TEMP_DIRECTORY%"
set "DATABASE_URL=sqlite:///%PRESENTON_APP_DATA%/fastapi.db"
set "FAST_API_INTERNAL_URL=http://127.0.0.1:%PRESENTON_FASTAPI_PORT%"
set "NEXT_PUBLIC_FAST_API=http://127.0.0.1:%PRESENTON_FASTAPI_PORT%"

echo [3/3] Starting Presenton FastAPI server...
pushd "utils\presenton-main\servers\fastapi"
start "" /min cmd /c "uv run python server.py --port %PRESENTON_FASTAPI_PORT% --reload true"
popd
if errorlevel 1 (
    echo Failed to start Presenton FastAPI server!
    pause
    exit /b 1
)

echo Starting Presenton Next.js app on port %PRESENTON_NEXTJS_PORT%...
pushd "utils\presenton-main\servers\nextjs"
if not exist "node_modules" (
    echo Installing Presenton Next.js dependencies...
    call npm install --loglevel=error
)
set "HOSTNAME=127.0.0.1"
set "PORT=%PRESENTON_NEXTJS_PORT%"
start "" /min cmd /c "npm run dev"
popd
if errorlevel 1 (
    echo Failed to start Presenton Next.js app!
    pause
    exit /b 1
)

echo [4/4] Starting Flask backend server (port 5000)...
set "FLASK_APP=backend\app.py"
start "" /min cmd /c ""venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, 'backend'); from app import app; app.run(host='0.0.0.0', port=5000, debug=True)""
if errorlevel 1 (
    echo Failed to start Flask backend server!
    pause
    exit /b 1
)

echo Waiting for services...
timeout /t 8 /nobreak >nul

echo Opening browser...
start "" http://localhost:5000
start "" http://localhost:3000
start "" http://localhost:3001

echo.
echo ========================================
echo   System started!
echo   Competition Management: http://localhost:5000
echo   Smart Mermaid:          http://localhost:3000
echo   Presenton:              http://localhost:3001
echo   Presenton API:         http://127.0.0.1:3002
echo   Close the background windows to stop services.
echo ========================================
echo.
echo Press any key to close this window...
pause >nul
