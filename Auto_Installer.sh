#!/bin/bash

RED='\033[0;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

ENV_ACTIVATED=0
PYTHON_CMD="python3"
LANG_CMD=""
L_CHOICE=""
SUGGESTED_PYTHON=""

if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

clear
echo "========================================================"
echo "      Auto Installer - Language Setup"
echo "========================================================"
echo ""
echo " [1] English"
echo " [2] Traditional Chinese (正體中文)"
echo ""
read -p "Select Language (1 or 2): " L_CHOICE

if [ "$L_CHOICE" == "2" ]; then
    LANG_CMD="--lang CHT"
    echo -e "[*] Language set to Traditional Chinese"
else
    LANG_CMD="--lang EN"
    echo -e "[*] Language set to English"
fi
sleep 1

press_enter() {
    echo ""
    read -n 1 -s -r -p "Press any key to continue..."
    echo ""
}

detect_venv() {
    SUGGESTED_PYTHON=""
    if [ -f "./venv/bin/python" ]; then
        SUGGESTED_PYTHON="./venv/bin/python"
    elif [ -f "./.venv/bin/python" ]; then
        SUGGESTED_PYTHON="./.venv/bin/python"
    elif [ -f "../venv/bin/python" ]; then
        SUGGESTED_PYTHON="../venv/bin/python"
    fi
}

show_menu() {
    while true; do
        clear
        echo "========================================================"
        echo "      Auto Installer - Main Menu"
        echo "========================================================"
        echo ""
        if [ "$L_CHOICE" == "2" ]; then
            echo " [1] 批次複製專案 (Git Clone)"
            echo " [2] 批次安裝依賴 (pip install requirements)"
            echo " [3] 離開 (Exit)"
            echo ""
            read -p "請輸入選項 (1-3): " CHOICE
        else
            echo " [1] Batch Git Clone (Download Projects)"
            echo " [2] Batch Install Dependencies (pip install)"
            echo " [3] Exit"
            echo ""
            read -p "Please enter your choice (1-3): " CHOICE
        fi

        case $CHOICE in
            1) do_clone ;;
            2) check_env_and_install ;;
            3) echo "Goodbye!"; exit 0 ;;
            *) echo "Invalid option." ;;
        esac
    done
}

do_clone() {
    echo ""
    if [ "$L_CHOICE" == "2" ]; then
        echo "[模式] 已選擇 Git Clone (複製專案)。"
    else
        echo "[Mode] Git Clone Selected."
    fi
    
    $PYTHON_CMD auto_installer.py --clone $LANG_CMD
    
    press_enter
}

check_env_and_install() {
    echo ""
    if [ "$L_CHOICE" == "2" ]; then
        echo "[模式] 已選擇安裝依賴組件。"
    else
        echo "[Mode] Install Dependencies Selected."
    fi

    detect_venv
    
    if [ ! -z "$SUGGESTED_PYTHON" ]; then
        PORTABLE_MSG="[Detection] Virtual Environment Found!"
    fi

    echo ""
    echo -e "${RED}********************************************************"
    echo ""
    if [ "$L_CHOICE" == "2" ]; then
        echo "  嚴重警告 (CRITICAL WARNING)"
        echo ""
        echo "  執行此步驟前，請務必確認您已使用正確的 Python 環境！"
        echo "  (Linux/Mac 用戶請確保已激活 venv 或 conda)"
    else
        echo "  CRITICAL WARNING"
        echo ""
        echo "  Please ensure your Virtual Environment is ACTIVATED!"
        echo "  (Linux/Mac users: ensure venv or conda is active)"
    fi
    echo ""

    if [ ! -z "$SUGGESTED_PYTHON" ]; then
        if [ "$L_CHOICE" == "2" ]; then
            echo -e "  ${YELLOW}[!] 偵測到虛擬環境 (venv)！${RED}"
            echo "  建議路徑: $SUGGESTED_PYTHON"
            echo "  建議使用此路徑，不要使用系統全域 Python。"
        else
            echo -e "  ${YELLOW}[!] Virtual Environment detected!${RED}"
            echo "  Suggested Path: $SUGGESTED_PYTHON"
            echo "  Do NOT use system Python. Use the venv path."
        fi
    fi
    echo ""
    echo -e "********************************************************${RESET}"
    echo ""

    if [ "$ENV_ACTIVATED" == "1" ]; then
        if [ "$L_CHOICE" == "2" ]; then
            echo -e "${YELLOW}[*] 環境似乎已設定完畢。${RESET}"
            echo "    當前 Python 指令: $PYTHON_CMD"
            echo ""
            read -p "請按 Enter 繼續安裝，或輸入 'r' 重新設定環境... " RE_ACT
        else
            echo -e "${YELLOW}[*] Environment seems already activated/set.${RESET}"
            echo "    Current Python Command: $PYTHON_CMD"
            echo ""
            read -p "Press Enter to continue, or type 'r' to reset env... " RE_ACT
        fi

        if [[ "$RE_ACT" == "r" || "$RE_ACT" == "R" ]]; then
            ask_env
        else
            run_install_direct
        fi
    else
        ask_env
    fi
}

ask_env() {
    while true; do
        echo ""
        echo "--------------------------------------------------------"
        if [ "$L_CHOICE" == "2" ]; then
            echo "[環境激活] 請輸入激活指令 (強制步驟)"
            echo ""
            echo "常用指令範例 (可複製):"
            echo -e "  1. Conda 環境:  ${YELLOW}conda activate comfyui${RESET}"
            echo -e "  2. venv 環境 :  ${YELLOW}source venv/bin/activate${RESET}"
            echo ""
            if [ ! -z "$SUGGESTED_PYTHON" ]; then
                echo -e "${YELLOW}[提示] 偵測到 venv: 輸入 'p' 可直接使用建議路徑。${RESET}"
            fi
            echo "請直接輸入上方指令，或 'python3' (若已在環境中)。"
        else
            echo "[Environment Activation] Enter command (Mandatory)"
            echo ""
            echo "Common Commands (Copy & Paste):"
            echo -e "  1. Conda Env :  ${YELLOW}conda activate comfyui${RESET}"
            echo -e "  2. venv Env  :  ${YELLOW}source venv/bin/activate${RESET}"
            echo ""
            if [ ! -z "$SUGGESTED_PYTHON" ]; then
                echo -e "${YELLOW}[Hint] venv detected: Type 'p' to use the suggested path.${RESET}"
            fi
            echo "Please enter command, or 'python3' if already active."
        fi
        echo "--------------------------------------------------------"

        read -p "Command > " ACT_CMD

        if [[ "$ACT_CMD" == "p" || "$ACT_CMD" == "P" ]]; then
            if [ ! -z "$SUGGESTED_PYTHON" ]; then
                echo ""
                echo -e "${YELLOW}[*] Using Suggested Python Path: $SUGGESTED_PYTHON${RESET}"
                PYTHON_CMD="$SUGGESTED_PYTHON"
                ENV_ACTIVATED=1
                run_install_direct
                return
            else
                echo -e "${RED}No suggested path found. Please type command.${RESET}"
            fi
        elif [ -z "$ACT_CMD" ]; then
            echo -e "${RED}Input required.${RESET}"
        else

            if [[ "$ACT_CMD" == source* || "$ACT_CMD" == "."* ]]; then
                 eval "$ACT_CMD"
                 if [ $? -eq 0 ]; then
                    echo -e "${YELLOW}[Success] Environment activated.${RESET}"
                    ENV_ACTIVATED=1
                    PYTHON_CMD="python" 
                    run_install_direct
                    return
                 else
                    echo -e "${RED}[Warning] Activation Failed!${RESET}"
                 fi
            elif [[ "$ACT_CMD" == conda* ]]; then
                 echo -e "${YELLOW}[Info] Conda activation inside script can be tricky.${RESET}"
                 echo "Please ensure you have initialized conda shell."
                 eval "$ACT_CMD"
                 if [ $? -eq 0 ]; then
                    ENV_ACTIVATED=1
                    run_install_direct
                    return
                 fi
            else
                echo -e "${YELLOW}[*] Setting custom command: $ACT_CMD${RESET}"
                PYTHON_CMD="$ACT_CMD"
                ENV_ACTIVATED=1
                run_install_direct
                return
            fi
        fi
    done
}

run_install_direct() {
    echo ""
    echo "--------------------------------------------------------"
    if [ "$L_CHOICE" == "2" ]; then
        echo "當前使用的 Python 指令/路徑:"
    else
        echo "Active Python Interpreter Command:"
    fi
    echo "$PYTHON_CMD"
    echo "--------------------------------------------------------"
    echo ""

    $PYTHON_CMD auto_installer.py --install $LANG_CMD

    press_enter
}

show_menu