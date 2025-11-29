@echo off
setlocal enabledelayedexpansion

title Git Project Manager (Auto Installer)

chcp 65001 >nul

for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "RESET=%ESC%[0m"

set ENV_ACTIVATED=0

:: ==========================================================
:: Step 0: Language Selection (Global Setting)
:: ==========================================================
cls
echo ========================================================
echo       Auto Installer - Language Setup
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
echo       Auto Installer - Main Menu
echo ========================================================
echo.
echo  [1] Batch Git Clone (Download Projects)
echo  [2] Batch Install Dependencies (pip install)
echo  [3] Exit
echo.
echo ========================================================
set /p "CHOICE=Please enter your choice (1-3): "

if "%CHOICE%"=="1" goto DoClone
if "%CHOICE%"=="2" goto CheckEnvAndInstall
if "%CHOICE%"=="3" goto End
goto MainMenu

:: ----------------------------------------------------------
:: Option 1: Git Clone (No special env needed)
:: ----------------------------------------------------------
:DoClone
echo.
echo [Mode] Git Clone Selected.
:: Pass the language argument here
:: 【修改處 1】將 auto_runner.py 改為 auto_installer.py
python auto_installer.py --clone %LANG_CMD%
echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:: Option 2: Install Dependencies (Needs Environment)
:: ----------------------------------------------------------
:CheckEnvAndInstall
echo.
echo [Mode] Install Dependencies Selected.

echo.
:: ==========================================================
:: 【新增】紅色嚴重警告區域 (優化版)
:: ==========================================================
echo.
:: 開頭開啟紅色，畫上邊框
echo %RED%********************************************************
echo.
echo  CRITICAL WARNING
echo.
echo  Please ensure your Virtual Environment is ACTIVATED
echo  before proceeding with dependency installation!
echo.
echo  【嚴重警告】
echo  執行此步驟前，請務必確認您已「激活」虛擬環境！
echo  (例如: conda activate comfyui 或 venv\Scripts\activate)
echo.
:: 結束邊框，重置顏色
echo ********************************************************%RESET%
echo.

if "!ENV_ACTIVATED!"=="1" (
    echo %YELLOW%[*] Environment seems already activated.%RESET%
    echo     Current Python: 
    where python
    echo.
    set /p "RE_ACT=Do you want to re-activate/change environment? (y/n): "
    if /i "!RE_ACT!"=="y" goto AskEnv
    goto RunInstall
)

:AskEnv
echo.
echo --------------------------------------------------------
echo [Requirement] Virtual Environment Check
echo Do you need to activate a specific environment for pip install?
echo (If you are already in the correct env, press 'n')
echo --------------------------------------------------------
set /p "NEED_ACTIVATE=Enter 'y' to activate, 'n' to skip: "

if /i "%NEED_ACTIVATE%"=="n" goto RunInstall

:ActivateBlock
echo.
echo Please enter your activation command below.
echo   (e.g., "call conda activate comfyui" OR "call venv\Scripts\activate")
set /p "ACT_CMD=Command > "

echo.
echo [*] Executing: %ACT_CMD%
call %ACT_CMD%

if %errorlevel% neq 0 (
    echo %RED%[Warning] Activation might have failed.%RESET%
) else (
    echo %YELLOW%[Success] Environment command executed.%RESET%
    set ENV_ACTIVATED=1
)

:RunInstall
echo.
echo --------------------------------------------------------
echo Active Python Environment:
where python
echo --------------------------------------------------------
echo.

:: Pass the language argument here too
:: 【修改處 2】將 auto_runner.py 改為 auto_installer.py
python auto_installer.py --install %LANG_CMD%

echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:End
echo.
echo Goodbye!
exit