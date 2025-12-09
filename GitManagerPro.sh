#!/bin/bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

TARGET_DIR="."
PYTHON_CMD="python3"
ENV_TYPE="System Python"
LANG_CMD=""

clear
echo -e "${CYAN}[System] Detecting Python environment...${RESET}"

if [ -f "./venv/bin/python" ]; then
    PYTHON_CMD="./venv/bin/python"
    ENV_TYPE="Virtual Env (./venv)"
elif [ -f "./.venv/bin/python" ]; then
    PYTHON_CMD="./.venv/bin/python"
    ENV_TYPE="Virtual Env (./.venv)"
elif [ -f "../venv/bin/python" ]; then
    PYTHON_CMD="../venv/bin/python"
    ENV_TYPE="Virtual Env (Parent Dir)"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    ENV_TYPE="System Python3"
else
    PYTHON_CMD="python" 
    ENV_TYPE="System Python"
fi

echo -e "   -> Using: ${GREEN}$ENV_TYPE${RESET}"
echo -e "   -> Path : ${YELLOW}$PYTHON_CMD${RESET}"
sleep 1

clear
echo "========================================================"
echo "      Git Manager Pro - Language Setup"
echo "========================================================"
echo ""
echo " [1] English"
echo " [2] Traditional Chinese (正體中文)"
echo ""
read -p "Select Language (1 or 2): " L_CHOICE

if [ "$L_CHOICE" == "2" ]; then
    LANG_CMD="--lang CHT"
    echo -e "${GREEN}[*] Language set to Traditional Chinese${RESET}"
else
    LANG_CMD="--lang EN"
    echo -e "${GREEN}[*] Language set to English${RESET}"
fi
sleep 1

pause() {
    echo ""
    read -n 1 -s -r -p "Press any key to continue..."
    echo ""
}

while true; do
    clear
    echo "========================================================"
    echo -e "      ${CYAN}Git Manager Pro - Main Menu${RESET}"
    echo "========================================================"
    echo " Target Directory: $TARGET_DIR"
    echo ""
    echo " [1] Auto Update All (全自動更新)"
    echo " [2] Interactive Update (互動模式)"
    echo " [3] Auto Update with Exclusions (排除特定資料夾)"
    echo " [4] Convert and Update (新增/修復專案)"
    echo ""
    echo " [5] Exit"
    echo ""
    echo " ------------------------------------------------"
    echo " [6] Time Machine (Git Reset - DANGER)"
    echo "     - Revert all repos to a specific time."
    echo -e "     - ${RED}USE WITH CAUTION.${RESET}"
    echo " ------------------------------------------------"
    echo ""
    echo "========================================================"
    read -p "Please enter your choice (1-6): " CHOICE

    case $CHOICE in
        1)
            clear
            echo -e "${GREEN}[Mode] Auto Update Selected.${RESET}"
            echo ""
            $PYTHON_CMD manage_git_pro.py -d "$TARGET_DIR" --mode auto --skip-convert $LANG_CMD
            pause
            ;;
        2)
            clear
            echo -e "${GREEN}[Mode] Interactive Update Selected.${RESET}"
            echo ""
            $PYTHON_CMD manage_git_pro.py -d "$TARGET_DIR" --mode interactive --skip-convert $LANG_CMD
            pause
            ;;
        3)
            clear
            echo -e "${GREEN}[Mode] Auto Update with Exclusions.${RESET}"
            echo ""
            echo "Please enter the folder names you want to SKIP."
            echo "Separate multiple names with spaces."
            echo "Example: node_A node_B ComfyUI-Manager"
            echo ""
            read -p "Exclusion List > " EX_LIST
            echo ""
            $PYTHON_CMD manage_git_pro.py -d "$TARGET_DIR" --mode auto --skip-convert --exclude $EX_LIST $LANG_CMD
            pause
            ;;
        4)
            clear
            echo -e "${GREEN}[Mode] Convert and Update Selected.${RESET}"
            echo ""
            echo "Please enter the filename of your URL list."
            echo "(You can drag and drop the file here)"
            echo ""
            read -p "List File > " LIST_FILE
            
            LIST_FILE="${LIST_FILE%\'}"
            LIST_FILE="${LIST_FILE#\'}"
            LIST_FILE="${LIST_FILE%\"}"
            LIST_FILE="${LIST_FILE#\"}"
            
            LIST_FILE="$(echo -e "${LIST_FILE}" | sed -e 's/[[:space:]]*$//')"

            if [ ! -f "$LIST_FILE" ]; then
                echo ""
                echo -e "${RED}[Error] File \"$LIST_FILE\" not found!${RESET}"
                echo "Please make sure the path is correct and try again."
                pause
            else
                echo ""
                echo -e "[*] Processing list: ${YELLOW}$LIST_FILE${RESET}"
                $PYTHON_CMD manage_git_pro.py -d "$TARGET_DIR" --mode auto --list-file "$LIST_FILE" $LANG_CMD
                pause
            fi
            ;;
        5)
            echo ""
            echo "Goodbye!"
            exit 0
            ;;
        6)
            clear
            echo "========================================================"
            echo -e "      ${RED}TIME MACHINE (Hard Reset)${RESET}"
            echo "========================================================"
            echo ""
            echo " Warning: This will discard all changes after the timestamp."
            echo ""
            echo " Please enter target timestamp."
            echo " Format: YYYY-MM-DD HH:MM:SS"
            echo " Example: 2025-08-25 10:30:00"
            echo ""
            read -p "Target Timestamp > " TS_INPUT

            if [ -z "$TS_INPUT" ]; then
                echo -e "${RED}[Error] Input cannot be empty.${RESET}"
                pause
            else
                echo ""
                echo -e "${YELLOW}[*] Initializing Time Machine...${RESET}"
                $PYTHON_CMD manage_git_pro.py -d "$TARGET_DIR" --mode auto --reset-timestamp "$TS_INPUT" $LANG_CMD
                pause
            fi
            ;;
        *)
            echo "Invalid option."
            sleep 1
            ;;
    esac
done