@echo off
setlocal enabledelayedexpansion

REM === 犀鸟 (Hornbill) — Rhino 8 一键安装脚本 ===
REM 用法：把整个项目文件夹放桌面，双击 install.bat
REM 前置条件：已安装 Rhino 8 并至少运行过一次

for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

set "PLUGIN_NAME=my-plugin"
set "RHINO_PATH=C:\Program Files\Rhino 8\System"

echo %ESC%[96m============================================%ESC%[0m
echo %ESC%[96m  %PLUGIN_NAME% - Rhino 8 plugin installer%ESC%[0m
echo %ESC%[96m============================================%ESC%[0m
echo.

REM 1. Detect Rhino 8
set "RHINO_EXE=%RHINO_PATH%\Rhino.exe"
set "RHINOCODE_EXE=%RHINO_PATH%\rhinocode.exe"
set "YAK_EXE=%RHINO_PATH%\yak.exe"

if not exist "%RHINO_EXE%" (
    echo [ERROR] Rhino 8 not found at %RHINO_PATH%
    echo Install Rhinoceros 8 first: https://www.rhino3d.com/download/
    pause
    exit /b 1
)

REM 2. Kill running Rhino
taskkill /f /im Rhino.exe 2>nul

REM 3. Locate Rhino Python interpreter
set "PYTHON_EXE=%USERPROFILE%\.rhinocode\py39-rh8\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [ERROR] %PYTHON_EXE% not found. Run Rhino 8 at least once first.
    pause
    exit /b 1
)

REM 4. Locate site-envs directory (dynamic folder name)
set "SITE_ENV_DIR="
for /d %%d in ("%USERPROFILE%\.rhinocode\py39-rh8\site-envs\*") do (
    set "SITE_ENV_DIR=%%d"
)
if not defined SITE_ENV_DIR (
    echo [ERROR] site-envs directory not found.
    pause
    exit /b 1
)

REM 5. Configure Aliyun pip mirror
echo %ESC%[93m[1/5]%ESC%[0m Configuring pip mirror (Aliyun)...
call "%PYTHON_EXE%" -m pip install --index-url https://mirrors.aliyun.com/pypi/simple/ pip -U
call "%PYTHON_EXE%" -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

REM 6. Install dependencies (skip if all present)
echo %ESC%[93m[2/5]%ESC%[0m Checking dependencies...
if exist "requirements.txt" (
    "%PYTHON_EXE%" -c "import sys; sys.path.insert(0,r'%SITE_ENV_DIR%'); import matplotlib,numpy,pandas,scipy,aiohttp,timezonefinder,parse,pyproj,PIL" >nul 2>&1
    if errorlevel 1 (
        echo   Installing missing packages...
        call "%PYTHON_EXE%" -s -m pip --disable-pip-version-check install --target "%SITE_ENV_DIR%" -r requirements.txt
    ) else (
        echo   All dependencies already installed, skipping.
    )
) else (
    echo   requirements.txt not found, skipping dependency install.
)

REM 6.5. Sync config .ini files to src/core/ (packaging requirement)
echo %ESC%[93m[2.5/5]%ESC%[0m Syncing config files...
if exist "configs\*.ini" (
    xcopy /Y "configs\urls.ini" "src\core\" >nul
    xcopy /Y "configs\lang_*.ini" "src\core\" >nul
    echo   Configs synced to src/core/
)

REM 7. Build plugin
echo %ESC%[93m[3/5]%ESC%[0m Building plugin...
set "RHPROJ="
for %%f in (*.rhproj) do set "RHPROJ=%%f"
if defined RHPROJ (
    if exist "%RHINOCODE_EXE%" (
        call "%RHINOCODE_EXE%" project build "%RHPROJ%"
        if errorlevel 1 (
            echo [ERROR] Build failed.
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] rhinocode.exe not found.
        pause
        exit /b 1
    )
) else (
    echo [ERROR] No .rhproj file found.
    pause
    exit /b 1
)

REM 8. Install .yak package
echo %ESC%[93m[4/5]%ESC%[0m Installing plugin...
if exist "%YAK_EXE%" (
    "%YAK_EXE%" uninstall %PLUGIN_NAME% >nul 2>&1
    for %%f in (build\rh8\*rh8-any.yak) do (
        call "%YAK_EXE%" install "%%f"
        echo   Installed: %%f
    )
) else (
    echo [WARN] yak.exe not found. Drag build\*.yak into Rhino window manually.
)

REM 9. Launch Rhino
echo %ESC%[93m[5/5]%ESC%[0m Launching Rhino 8...
start "" "%RHINO_EXE%"

echo.
echo %ESC%[92m============================================%ESC%[0m
echo %ESC%[92mInstall complete. Open Rhino and type your command.%ESC%[0m
echo %ESC%[92m============================================%ESC%[0m
pause
