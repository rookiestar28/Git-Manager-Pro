@echo off
setlocal enabledelayedexpansion

:: 設定視窗標題
title Ray's AIGC Project Manager (Interactive)

:: 設定編碼為 UTF-8
chcp 65001 >nul

:: 用於記錄環境是否已經被激活過 (0=否, 1=是)
set ENV_ACTIVATED=0

:: ==========================================================
:: Step 0: Language Selection (Global Setting)
:: ==========================================================
cls
echo ========================================================
echo       AIGC Project Manager - Language Setup
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
echo       AIGC Project Manager - Main Menu
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
python auto_runner.py --clone %LANG_CMD%
echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:: Option 2: Install Dependencies (Needs Environment)
:: ----------------------------------------------------------
:CheckEnvAndInstall
echo.
echo [Mode] Install Dependencies Selected.

:: 如果已經激活過，詢問是否要重新激活
if "!ENV_ACTIVATED!"=="1" (
    echo [*] Environment seems already activated. 
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
    echo [Warning] Activation might have failed.
) else (
    echo [Success] Environment command executed.
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
python auto_runner.py --install %LANG_CMD%

echo.
pause
goto MainMenu

:: ----------------------------------------------------------
:End
echo.
echo Goodbye!
exit