@echo off
setlocal enabledelayedexpansion

title Git Project Manager (Auto Installer)

chcp 65001 >nul

for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "RESET=%ESC%[0m"

set ENV_ACTIVATED=0
set "PYTHON_CMD=python"

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
if "%L_CHOICE%"=="2" (
    echo  [1] 批次複製專案 ^(Git Clone^)
    echo  [2] 批次安裝依賴 ^(pip install requirements^)
    echo  [3] 離開 ^(Exit^)
) else (
    echo  [1] Batch Git Clone ^(Download Projects^)
    echo  [2] Batch Install Dependencies ^(pip install^)
    echo  [3] Exit
)
echo.
echo ========================================================
set /p "CHOICE=Please enter your choice (1-3): "

if "%CHOICE%"=="1" goto DoClone
if "%CHOICE%"=="2" goto CheckEnvAndInstall
if "%CHOICE%"=="3" goto End
goto MainMenu

:DoClone
echo.
if "%L_CHOICE%"=="2" (
    echo [模式] 已選擇 Git Clone ^(複製專案^)。
) else (
    echo [Mode] Git Clone Selected.
)
python auto_installer.py --clone %LANG_CMD%
echo.
pause
goto MainMenu

:CheckEnvAndInstall
echo.
if "%L_CHOICE%"=="2" (
    echo [模式] 已選擇安裝依賴組件。
) else (
    echo [Mode] Install Dependencies Selected.
)

set "SUGGESTED_PYTHON="
set "PORTABLE_MSG="

if exist "python_embeded\python.exe" set "SUGGESTED_PYTHON=python_embeded\python.exe"
if exist "..\python_embeded\python.exe" set "SUGGESTED_PYTHON=..\python_embeded\python.exe"
if exist "..\..\python_embeded\python.exe" set "SUGGESTED_PYTHON=..\..\python_embeded\python.exe"

if defined SUGGESTED_PYTHON (
    set "PORTABLE_MSG=[Detection] ComfyUI Portable Environment Found^!"
)

echo.
echo %RED%********************************************************
echo.
if "%L_CHOICE%"=="2" (
    echo  嚴重警告 ^(CRITICAL WARNING^)
    echo.
    echo  執行此步驟前，請務必確認您已使用正確的 Python 環境！
    echo  ^(若是 ComfyUI 便攜版，請使用嵌入式 Python^)
) else (
    echo  CRITICAL WARNING
    echo.
    echo  Please ensure your Virtual Environment is ACTIVATED!
    echo  ^(For Portable users, use the embedded Python^)
)
echo.

if defined SUGGESTED_PYTHON (
    if "%L_CHOICE%"=="2" (
        echo  %YELLOW%[^!] 偵測到 ComfyUI Portable ^(便攜版^) 環境！%RED%
        echo  建議路徑: %SUGGESTED_PYTHON%
        echo  建議直接使用上述路徑，不要使用系統全域 Python。
    ) else (
        echo  %YELLOW%[^!] It seems you are using the Portable version.%RED%
        echo  Suggested Path: %SUGGESTED_PYTHON%
        echo  Do NOT use system Python. Use the embedded Python path.
    )
)
echo.
echo ********************************************************%RESET%
echo.

if "!ENV_ACTIVATED!"=="1" (
    if "%L_CHOICE%"=="2" (
        echo %YELLOW%[*] 環境似乎已設定完畢。%RESET%
        echo     當前 Python 指令: !PYTHON_CMD!
        echo.
        echo 請按 Enter 繼續安裝，或輸入 'r' 重新設定環境...
        set /p "RE_ACT=> "
    ) else (
        echo %YELLOW%[*] Environment seems already activated/set.%RESET%
        echo     Current Python Command: !PYTHON_CMD!
        echo.
        echo Press Enter to continue, or type 'r' to reset env...
        set /p "RE_ACT=> "
    )
    
    if /i "!RE_ACT!"=="r" goto AskEnv
    goto RunInstallDirect
)

:AskEnv
echo.
echo --------------------------------------------------------
if "%L_CHOICE%"=="2" (
    echo [環境激活] 請輸入激活指令 ^(強制步驟^)
    echo.
    echo 常用指令範例 ^(可複製^):
    echo  1. Conda 環境:  %YELLOW%conda activate comfyui%RESET%
    echo  2. venv 環境 :  %YELLOW%venv\Scripts\activate%RESET%
    echo.
    if defined SUGGESTED_PYTHON (
        echo %YELLOW%[提示] 便攜版用戶: 輸入 'p' 可直接使用偵測到的路徑。%RESET%
    )
    echo 請直接輸入上方指令並按 Enter。
) else (
    echo [Environment Activation] Enter command ^(Mandatory^)
    echo.
    echo Common Commands ^(Copy ^& Paste^):
    echo  1. Conda Env :  %YELLOW%conda activate comfyui%RESET%
    echo  2. venv Env  :  %YELLOW%venv\Scripts\activate%RESET%
    echo.
    if defined SUGGESTED_PYTHON (
        echo %YELLOW%[Hint] Portable User: Type 'p' to use the detected path.%RESET%
    )
    echo Please enter the command above and press Enter.
)
echo --------------------------------------------------------

set "ACT_CMD="
set /p "ACT_CMD=Command > "

if /i "%ACT_CMD%"=="p" goto UsePortable
if "%ACT_CMD%"=="" (
    echo.
    if "%L_CHOICE%"=="2" (
        echo %RED%[錯誤] 此為強制步驟，請輸入指令或 'p'。%RESET%
    ) else (
        echo %RED%[Error] This step is mandatory. Input required.%RESET%
    )
    goto AskEnv
)

echo.
echo [*] Executing: %ACT_CMD%
call %ACT_CMD%

if %errorlevel% neq 0 (
    echo %RED%[Warning] Activation Failed! Please try again.%RESET%
    echo.
    pause
    goto AskEnv
) else (
    echo %YELLOW%[Success] Environment command executed.%RESET%
    set ENV_ACTIVATED=1
    set "PYTHON_CMD=python"
)
goto RunInstallDirect

:UsePortable
echo.
echo %YELLOW%[*] Using Portable Python Path: %SUGGESTED_PYTHON%%RESET%
set "PYTHON_CMD=%SUGGESTED_PYTHON%"
set ENV_ACTIVATED=1
goto RunInstallDirect

:RunInstallDirect
echo.
echo --------------------------------------------------------
if "%L_CHOICE%"=="2" (
    echo 當前使用的 Python 指令/路徑:
) else (
    echo Active Python Interpreter Command:
)
echo %PYTHON_CMD%
echo --------------------------------------------------------
echo.

"%PYTHON_CMD%" auto_installer.py --install %LANG_CMD%

echo.
pause
goto MainMenu

:End
echo.
echo Goodbye!
exit