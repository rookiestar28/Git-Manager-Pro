@echo off
setlocal enabledelayedexpansion

title Git Manager (Pro) Launcher
chcp 65001 >nul

set "TARGET_DIR=."

echo.
echo [System] Detecting Python environment...

set "PYTHON_EXE=python"
set "ENV_TYPE=System Python"

if exist "python_embeded\python.exe" (
    set "PYTHON_EXE=python_embeded\python.exe"
    set "ENV_TYPE=Portable Python (Local)"
)

if exist "..\python_embeded\python.exe" (
    set "PYTHON_EXE=..\python_embeded\python.exe"
    set "ENV_TYPE=Portable Python (Parent Dir)"
)

echo    -^> Using: !ENV_TYPE!
echo    -^> Path : !PYTHON_EXE!
timeout /t 1 >nul

:LangSelect
cls
echo ========================================================
echo       Git Manager Pro - Language Setup
echo ========================================================
echo.
echo  [1] English
echo  [2] Traditional Chinese (正體中文)
echo.
set /p "L_CHOICE=Select Language (1 or 2): "

if "%L_CHOICE%"=="2" (
    set LANG_CMD=--lang CHT
    echo [*] Language set to Traditional Chinese
) else (
    set LANG_CMD=--lang EN
    echo [*] Language set to English
)
timeout /t 1 >nul

:MainMenu
cls
echo ========================================================
echo       Git Manager Pro - Main Menu
echo ========================================================
echo  Target Directory: %TARGET_DIR%
echo.
echo  [1] Auto Update All (全自動更新)
echo  [2] Interactive Update (互動模式)
echo  [3] Auto Update with Exclusions (排除特定資料夾)
echo  [4] Convert and Update (新增/修復專案)
echo.
echo  [5] Exit
echo.
echo  ------------------------------------------------
echo  [6] Time Machine (Git Reset - DANGER)
echo      - Revert all repos to a specific time.
echo      - USE WITH CAUTION.
echo  ------------------------------------------------
echo.
echo ========================================================
set /p "CHOICE=Please enter your choice (1-6): "

if "%CHOICE%"=="1" goto ModeAuto
if "%CHOICE%"=="2" goto ModeInteractive
if "%CHOICE%"=="3" goto ModeExclude
if "%CHOICE%"=="4" goto ModeConvert
if "%CHOICE%"=="5" goto End
if "%CHOICE%"=="6" goto ModeReset

goto MainMenu

:: ----------------------------------------------------------
:ModeAuto
cls
echo [Mode] Auto Update Selected.
echo.
"%PYTHON_EXE%" manage_git_pro.py -d "%TARGET_DIR%" --mode auto --skip-convert %LANG_CMD%
echo.
if %errorlevel% neq 0 pause
echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:ModeInteractive
cls
echo [Mode] Interactive Update Selected.
echo.
"%PYTHON_EXE%" manage_git_pro.py -d "%TARGET_DIR%" --mode interactive --skip-convert %LANG_CMD%
echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:ModeExclude
cls
echo [Mode] Auto Update with Exclusions.
echo.
echo Please enter the folder names you want to SKIP.
echo Separate multiple names with spaces.
echo Example: node_A node_B ComfyUI-Manager
echo.
set /p "EX_LIST=Exclusion List > "
echo.
"%PYTHON_EXE%" manage_git_pro.py -d "%TARGET_DIR%" --mode auto --skip-convert --exclude %EX_LIST% %LANG_CMD%
echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:ModeConvert
cls
echo [Mode] Convert and Update Selected.
echo.
echo Please enter the filename of your URL list.
echo (You can drag and drop the file here)
echo.
set /p "LIST_FILE=List File > "
set "LIST_FILE=%LIST_FILE:"=%"

if not exist "%LIST_FILE%" (
    echo.
    echo [Error] File "%LIST_FILE%" not found!
    echo Please make sure the path is correct and try again.
    pause
    goto MainMenu
)

echo.
echo [*] Processing list: "%LIST_FILE%"
"%PYTHON_EXE%" manage_git_pro.py -d "%TARGET_DIR%" --mode auto --list-file "%LIST_FILE%" %LANG_CMD%
echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:ModeReset
cls
echo ========================================================
echo       TIME MACHINE (Hard Reset)
echo ========================================================
echo.
echo  Warning: This will discard all changes after the timestamp.
echo.
echo  Please enter target timestamp.
echo  Format: YYYY-MM-DD HH:MM:SS
echo  Example: 2025-08-25 10:30:00
echo.
set /p "TS_INPUT=Target Timestamp > "

if "%TS_INPUT%"=="" (
    echo [Error] Input cannot be empty.
    pause
    goto MainMenu
)

echo.
echo [*] Initializing Time Machine...
"%PYTHON_EXE%" manage_git_pro.py -d "%TARGET_DIR%" --mode auto --reset-timestamp "%TS_INPUT%" %LANG_CMD%
echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:End
exit