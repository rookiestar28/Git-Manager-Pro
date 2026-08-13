#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
CORE_PATH="$SCRIPT_DIR/auto_installer.py"
LANG_CODE="EN"
BOOTSTRAP_PYTHON=""
SUGGESTED_PYTHON=""

RED=''
YELLOW=''
RESET=''

is_valid_value() {
    local value="$1"
    [[ -n "$value" ]] || return 1
    [[ "$value" != *$'\n'* ]] || return 1
    [[ "$value" != *$'\r'* ]] || return 1
    [[ "$value" != *$'\t'* ]] || return 1
    [[ "$value" != *$'\e'* ]] || return 1
    [[ "$value" != *[[:cntrl:]]* ]] || return 1
    return 0
}

discover_bootstrap() {
    local candidate
    local candidates=(
        "$SCRIPT_DIR/python_embeded/python"
        "$SCRIPT_DIR/python_embeded/python3"
        "$SCRIPT_DIR/.venv/bin/python"
        "$SCRIPT_DIR/venv/bin/python"
        "$SCRIPT_DIR/../python_embeded/python"
        "$SCRIPT_DIR/../python_embeded/python3"
        "$SCRIPT_DIR/../.venv/bin/python"
        "$SCRIPT_DIR/../venv/bin/python"
    )
    for candidate in "${candidates[@]}"; do
        if [[ -x "$candidate" ]]; then
            BOOTSTRAP_PYTHON="$candidate"
            return 0
        fi
    done
    if command -v python3 >/dev/null 2>&1; then
        BOOTSTRAP_PYTHON="$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        BOOTSTRAP_PYTHON="$(command -v python)"
    fi
    [[ -n "$BOOTSTRAP_PYTHON" ]]
}

detect_suggested_python() {
    local candidate
    local candidates=(
        "$SCRIPT_DIR/python_embeded/python"
        "$SCRIPT_DIR/python_embeded/python3"
        "$SCRIPT_DIR/.venv/bin/python"
        "$SCRIPT_DIR/venv/bin/python"
        "$SCRIPT_DIR/../python_embeded/python"
        "$SCRIPT_DIR/../python_embeded/python3"
        "$SCRIPT_DIR/../.venv/bin/python"
        "$SCRIPT_DIR/../venv/bin/python"
    )
    SUGGESTED_PYTHON=""
    for candidate in "${candidates[@]}"; do
        if [[ -x "$candidate" ]]; then
            SUGGESTED_PYTHON="$candidate"
            return 0
        fi
    done
    return 1
}

pause_after_success() {
    local ignored
    printf '\nPress Enter to continue... '
    IFS= read -r ignored || true
    printf '\n'
}

run_clone() {
    local status
    echo "[Mode] Git Clone Selected."
    "${BOOTSTRAP_ARGS[@]}" "$CORE_PATH" --clone --lang "$LANG_CODE"
    status=$?
    if (( status != 0 )); then
        return "$status"
    fi
    pause_after_success
    return 0
}

select_install_target() {
    local choice value
    SELECTOR_ARGS=()
    detect_suggested_python || true
    echo ""
    echo "Environment target / 環境目標"
    echo "  [1] Current Python / 目前 Python"
    echo "  [2] Explicit Python executable / 指定 Python 執行檔"
    echo "  [3] venv directory / venv 目錄"
    echo "  [4] Conda environment name / Conda 環境名稱"
    echo "  [5] Conda prefix / Conda prefix 路徑"
    if [[ -n "$SUGGESTED_PYTHON" ]]; then
        echo "  Detected venv or embedded Python: $SUGGESTED_PYTHON"
    fi
    echo "  [6] Cancel / 取消"
    IFS= read -r -p "Select target (1-6): " choice || return 3
    case "$choice" in
        1)
            SELECTOR_ARGS=(--use-current-python)
            ;;
        2)
            IFS= read -r -p "Python executable path: " value || return 3
            if ! is_valid_value "$value"; then
                echo "Invalid or empty target value."
                return 1
            fi
            SELECTOR_ARGS=(--python-executable "$value")
            ;;
        3)
            IFS= read -r -p "venv directory path: " value || return 3
            if ! is_valid_value "$value"; then
                echo "Invalid or empty target value."
                return 1
            fi
            SELECTOR_ARGS=(--venv "$value")
            ;;
        4)
            IFS= read -r -p "Conda environment name: " value || return 3
            if ! is_valid_value "$value"; then
                echo "Invalid or empty target value."
                return 1
            fi
            SELECTOR_ARGS=(--conda-env "$value")
            ;;
        5)
            IFS= read -r -p "Conda prefix path: " value || return 3
            if ! is_valid_value "$value"; then
                echo "Invalid or empty target value."
                return 1
            fi
            SELECTOR_ARGS=(--conda-prefix "$value")
            ;;
        6)
            return 2
            ;;
        *)
            echo "Invalid target selection."
            return 1
            ;;
    esac
    return 0
}

run_install() {
    local status
    while true; do
        select_install_target
        status=$?
        if (( status == 0 )); then
            break
        fi
        if (( status == 2 )); then
            return 0
        fi
        if (( status == 3 )); then
            return 3
        fi
    done
    echo "[Mode] Install Dependencies Selected."
    "${BOOTSTRAP_ARGS[@]}" "$CORE_PATH" --install "${SELECTOR_ARGS[@]}" --lang "$LANG_CODE"
    status=$?
    if (( status != 0 )); then
        return "$status"
    fi
    pause_after_success
    return 0
}

discover_bootstrap || {
    echo "ERROR: no usable Python bootstrap was found; install Python or place a venv beside this launcher." >&2
    exit 2
}
if [[ ! -f "$CORE_PATH" ]]; then
    echo "ERROR: auto_installer.py was not found beside this launcher." >&2
    exit 2
fi
BOOTSTRAP_ARGS=("$BOOTSTRAP_PYTHON")

printf '%s\n' "========================================================"
printf '%s\n' "      Auto Installer - Language Setup"
printf '%s\n\n' "========================================================"
printf '%s\n' " [1] English"
printf '%s\n' " [2] Traditional Chinese (正體中文)"
printf '%s' "Select Language (1 or 2): "
IFS= read -r language_choice || exit 2
if [[ "$language_choice" == "2" ]]; then
    LANG_CODE="CHT"
else
    LANG_CODE="EN"
fi

while true; do
    printf '%s\n' "========================================================"
    printf '%s\n' "      Auto Installer - Main Menu"
    printf '%s\n\n' "========================================================"
    if [[ "$LANG_CODE" == "CHT" ]]; then
        printf '%s\n' " [1] 批次複製專案 (Git Clone)"
        printf '%s\n' " [2] 批次安裝依賴 (pip install requirements)"
        printf '%s\n' " [3] 離開 (Exit)"
        printf '%s' "請輸入選項 (1-3): "
    else
        printf '%s\n' " [1] Batch Git Clone (Download Projects)"
        printf '%s\n' " [2] Batch Install Dependencies (pip install)"
        printf '%s\n' " [3] Exit"
        printf '%s' "Please enter your choice (1-3): "
    fi
    IFS= read -r choice || exit 2
    case "$choice" in
        1)
            run_clone || exit $?
            ;;
        2)
            run_install || exit $?
            ;;
        3)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option."
            ;;
    esac
done
