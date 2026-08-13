@echo off
setlocal DisableDelayedExpansion

title Git Project Manager (Auto Installer)
set "SCRIPT_DIR=%~dp0"
set "CORE_PATH=%SCRIPT_DIR%auto_installer.py"
set "BOOTSTRAP="
set "SUGGESTED_PYTHON="
set "LANG_CODE=EN"

if exist "%SCRIPT_DIR%python_embeded\python.exe" set "BOOTSTRAP=%SCRIPT_DIR%python_embeded\python.exe"
if not defined BOOTSTRAP if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" set "BOOTSTRAP=%SCRIPT_DIR%.venv\Scripts\python.exe"
if not defined BOOTSTRAP if exist "%SCRIPT_DIR%venv\Scripts\python.exe" set "BOOTSTRAP=%SCRIPT_DIR%venv\Scripts\python.exe"
if not defined BOOTSTRAP if exist "%SCRIPT_DIR%..\python_embeded\python.exe" set "BOOTSTRAP=%SCRIPT_DIR%..\python_embeded\python.exe"
if not defined BOOTSTRAP if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" set "BOOTSTRAP=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
if not defined BOOTSTRAP if exist "%SCRIPT_DIR%..\venv\Scripts\python.exe" set "BOOTSTRAP=%SCRIPT_DIR%..\venv\Scripts\python.exe"
if not defined BOOTSTRAP (
    where.exe python.exe >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP=python.exe"
)
if not defined BOOTSTRAP (
    echo ERROR: no usable Python bootstrap was found. Install Python or place a venv beside this launcher.
    exit /b 2
)
if not exist "%CORE_PATH%" (
    echo ERROR: auto_installer.py was not found beside this launcher.
    exit /b 2
)

echo ========================================================
echo       Auto Installer - Language Setup
echo ========================================================
echo.
echo  [1] English
echo  [2] Traditional Chinese (正體中文)
echo.
set /p "LANG_CHOICE=Select Language (1 or 2): "
setlocal EnableDelayedExpansion
if "!LANG_CHOICE!"=="2" (endlocal & set "LANG_CODE=CHT") else (endlocal & set "LANG_CODE=EN")

:MainMenu
echo ========================================================
echo       Auto Installer - Main Menu
echo ========================================================
echo.
if "%LANG_CODE%"=="CHT" (
    echo  [1] 批次複製專案 ^(Git Clone^)
    echo  [2] 批次安裝依賴 ^(pip install requirements^)
    echo  [3] 離開 ^(Exit^)
    set /p "MENU_CHOICE=請輸入選項 (1-3): "
) else (
    echo  [1] Batch Git Clone ^(Download Projects^)
    echo  [2] Batch Install Dependencies ^(pip install^)
    echo  [3] Exit
    set /p "MENU_CHOICE=Please enter your choice (1-3): "
)
setlocal EnableDelayedExpansion
if "!MENU_CHOICE!"=="1" (endlocal & goto DoClone)
if "!MENU_CHOICE!"=="2" (endlocal & goto SelectTarget)
if "!MENU_CHOICE!"=="3" (endlocal & goto End)
endlocal
echo Invalid option.
goto MainMenu

:DoClone
echo [Mode] Git Clone Selected.
"%BOOTSTRAP%" "%CORE_PATH%" --clone --lang %LANG_CODE%
set "CHILD_STATUS=%ERRORLEVEL%"
if not "%CHILD_STATUS%"=="0" exit /b %CHILD_STATUS%
set /p "PAUSE_INPUT=Press Enter to continue: "
goto MainMenu

:SelectTarget
set "SELECTOR_FLAG="
set "SELECTOR_VALUE="
set "SUGGESTED_PYTHON="
if exist "%SCRIPT_DIR%python_embeded\python.exe" set "SUGGESTED_PYTHON=%SCRIPT_DIR%python_embeded\python.exe"
if not defined SUGGESTED_PYTHON if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" set "SUGGESTED_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"
if not defined SUGGESTED_PYTHON if exist "%SCRIPT_DIR%venv\Scripts\python.exe" set "SUGGESTED_PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"
echo.
echo Environment target / 環境目標
echo  [1] Current Python / 目前 Python
echo  [2] Explicit Python executable / 指定 Python 執行檔
echo  [3] venv directory / venv 目錄
echo  [4] Conda environment name / Conda 環境名稱
echo  [5] Conda prefix / Conda prefix 路徑
setlocal EnableDelayedExpansion
if defined SUGGESTED_PYTHON echo Detected venv or embedded Python: !SUGGESTED_PYTHON!
endlocal
echo  [6] Cancel / 取消
set /p "TARGET_CHOICE=Select target (1-6): "
setlocal EnableDelayedExpansion
if "!TARGET_CHOICE!"=="1" (endlocal & goto TargetCurrent)
if "!TARGET_CHOICE!"=="2" (
    endlocal
    set "SELECTOR_FLAG=--python-executable"
    goto ReadTargetValue
)
if "!TARGET_CHOICE!"=="3" (
    endlocal
    set "SELECTOR_FLAG=--venv"
    goto ReadTargetValue
)
if "!TARGET_CHOICE!"=="4" (
    endlocal
    set "SELECTOR_FLAG=--conda-env"
    goto ReadTargetValue
)
if "!TARGET_CHOICE!"=="5" (
    endlocal
    set "SELECTOR_FLAG=--conda-prefix"
    goto ReadTargetValue
)
if "!TARGET_CHOICE!"=="6" (endlocal & goto MainMenu)
endlocal
echo Invalid target selection.
goto SelectTarget

:TargetCurrent
"%BOOTSTRAP%" "%CORE_PATH%" --install --use-current-python --lang %LANG_CODE%
set "CHILD_STATUS=%ERRORLEVEL%"
if not "%CHILD_STATUS%"=="0" exit /b %CHILD_STATUS%
set /p "PAUSE_INPUT=Press Enter to continue: "
goto MainMenu

:ReadTargetValue
set /p "SELECTOR_VALUE=Enter target value: "
if not defined SELECTOR_VALUE goto InvalidTarget
setlocal EnableDelayedExpansion
set "SELECTOR_NO_QUOTES=!SELECTOR_VALUE!"
set "SELECTOR_NO_QUOTES=!SELECTOR_NO_QUOTES:"=!"
if not "!SELECTOR_NO_QUOTES!"=="!SELECTOR_VALUE!" (
    endlocal
    goto InvalidTarget
)
set "GMP003_SELECTOR_VALUE=!SELECTOR_VALUE!"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -Command "$v=[Environment]::GetEnvironmentVariable('GMP003_SELECTOR_VALUE'); $bad=0..31 + 127 | ForEach-Object {[char]$_}; if ([string]::IsNullOrEmpty($v) -or $v.IndexOfAny([char[]]$bad) -ge 0) { exit 1 }" >nul 2>&1
if errorlevel 1 (
    endlocal
    goto InvalidTarget
)
set "GMP003_SELECTOR_VALUE="
set "SELECTOR_ARG=!SELECTOR_VALUE!"
if "!SELECTOR_ARG:~-1!"=="\" set "SELECTOR_ARG=!SELECTOR_ARG!\"
"%BOOTSTRAP%" "%CORE_PATH%" --install %SELECTOR_FLAG% "!SELECTOR_ARG!" --lang %LANG_CODE%
if errorlevel 1 (
    set "CHILD_STATUS=!ERRORLEVEL!"
    for /f "delims=" %%S in ("!CHILD_STATUS!") do (
        endlocal
        exit /b %%S
    )
)
endlocal
set /p "PAUSE_INPUT=Press Enter to continue: "
goto MainMenu

:InvalidTarget
echo Invalid or empty target value. Quotes are not accepted.
goto SelectTarget

:End
echo Goodbye!
exit /b 0
