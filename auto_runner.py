import os
import subprocess
import sys
import platform
from pathlib import Path

IGNORE_LIST = ["__pycache__", ".git", ".vscode", "venv", "env", ".idea"]

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

if platform.system() == "Windows":
    os.system('color')

TEXT = {
    'EN': {
        'menu_header': " AIGC Project Manager ",
        'menu_1': "1. Batch Git Clone (from list)",
        'menu_2': "2. Batch Install Dependencies (requirements.txt)",
        'menu_prompt': "Please select a mode (1 or 2): ",
        'lang_prompt': "Select Language (1: EN, 2: CHT): ",
        
        # Common
        'path_prompt': "Please enter the target root directory: ",
        'path_invalid': "Directory does not exist. Create it? (y/n): ",
        'path_created': "Directory created: {}",
        'op_cancel': "Operation cancelled.",
        'done': "All tasks completed.",

        # Clone Specific
        'list_prompt': "Please enter the path to the URL list file (.txt): ",
        'list_err': "File not found. Please try again.",
        'cloning': "  [*] Cloning: {}",
        'clone_success': "    -> [Success] Cloned '{}'",
        'clone_fail': "    -> [Failed] Error cloning '{}'",
        'clone_exists': "    -> [Skip] Folder '{}' already exists.",

        # Install Specific
        'scanning': "Scanning directory: ",
        'found_req': "  [*] Found 'requirements.txt' in: ",
        'installing': "    -> Installing dependencies (Stream output)...",
        'success': "    -> [Success] Dependencies installed for '{}'.",
        'fail': "    -> [Failed] Error installing dependencies for '{}'.",
        'skip': "    -> [Skipped] No requirements.txt found.",
        'summary_header': " Execution Summary ",
        'conflict_header': " Error Report ",
    },
    'CHT': {
        'menu_header': " AIGC 專案管理工具 ",
        'menu_1': "1. 批次複製專案 (Git Clone)",
        'menu_2': "2. 批次安裝依賴 (Install Dependencies)",
        'menu_prompt': "請選擇模式 (1 或 2): ",
        'lang_prompt': "請選擇語言 (1: EN, 2: CHT): ",

        # Common
        'path_prompt': "請輸入目標根目錄路徑 (例如 custom_nodes): ",
        'path_invalid': "目錄不存在，是否建立？(y/n): ",
        'path_created': "已建立目錄: {}",
        'op_cancel': "作業已取消。",
        'done': "所有作業執行完畢。",

        # Clone Specific
        'list_prompt': "請輸入 URL 清單文件的路徑 (.txt): ",
        'list_err': "找不到檔案，請重新輸入。",
        'cloning': "  [*] 正在複製專案: {}",
        'clone_success': "    -> [成功] 已複製 '{}'",
        'clone_fail': "    -> [失敗] 複製 '{}' 時發生錯誤",
        'clone_exists': "    -> [略過] 資料夾 '{}' 已存在。",

        # Install Specific
        'scanning': "正在掃描目錄: ",
        'found_req': "  [*] 在目錄中找到 'requirements.txt': ",
        'installing': "    -> 正在安裝依賴 (即時輸出)...",
        'success': "    -> [成功] 已安裝 '{}' 的依賴。",
        'fail': "    -> [失敗] 安裝 '{}' 的依賴時發生錯誤。",
        'skip': "    -> [略過] 未找到 requirements.txt。",
        'summary_header': " 執行結果統計 ",
        'conflict_header': " 錯誤報告 ",
    }
}

current_lang = 'EN'

def t(key):
    return TEXT[current_lang].get(key, key)

def print_color(color, message):
    print(f"{color}{message}{Colors.RESET}")

def set_language_interactive():
    global current_lang
    print("")
    lang_c = input("Select Language / 語言選擇 (1: EN, 2: CHT): ").strip()
    if lang_c == '2': current_lang = 'CHT'
    else: current_lang = 'EN'

def get_target_directory(allow_create=False):
    while True:
        print("")
        user_path = input(t('path_prompt')).strip().strip('"').strip("'")
        path_obj = Path(user_path)
        
        if path_obj.is_dir():
            return path_obj
        else:
            if allow_create:
                confirm = input(t('path_invalid')).lower()
                if confirm == 'y':
                    try:
                        os.makedirs(path_obj, exist_ok=True)
                        print(t('path_created').format(path_obj))
                        return path_obj
                    except Exception as e:
                        print_color(Colors.RED, f"Error: {e}")
                else:
                    print(t('op_cancel'))
                    sys.exit()
            else:
                print_color(Colors.RED, "Invalid path.")

def run_command_stream(command, cwd):
    captured_log = []
    try:
        process = subprocess.Popen(
            command, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='replace', bufsize=1
        )
        while True:
            output_line = process.stdout.readline()
            if output_line == '' and process.poll() is not None: break
            if output_line:
                sys.stdout.write(output_line)
                sys.stdout.flush()
                captured_log.append(output_line)
        return process.poll(), "".join(captured_log)
    except Exception as e:
        print_color(Colors.RED, f"Execution Error: {e}")
        return -1, str(e)

def mode_git_clone():
    target_dir = get_target_directory(allow_create=True)
    while True:
        list_path_str = input(t('list_prompt')).strip().strip('"').strip("'")
        list_path = Path(list_path_str)
        if list_path.is_file(): break
        print_color(Colors.RED, t('list_err'))

    with open(list_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    print("\n" + "-"*50)
    print(f"Target: {target_dir}")
    print(f"Total URLs: {len(urls)}")
    print("-" * 50)

    for url in urls:
        folder_name = url.split('/')[-1].replace('.git', '')
        destination = target_dir / folder_name
        print_color(Colors.CYAN, t('cloning').format(folder_name))
        
        if destination.exists():
            print_color(Colors.YELLOW, t('clone_exists').format(folder_name))
            continue

        cmd = ["git", "clone", url]
        return_code, _ = run_command_stream(cmd, cwd=target_dir)

        if return_code == 0: print_color(Colors.GREEN, t('clone_success').format(folder_name))
        else: print_color(Colors.RED, t('clone_fail').format(folder_name))
        print("-" * 30)
    print("\n" + t('done'))

def extract_error_info(full_log):
    error_lines = []
    if not full_log: return error_lines
    keywords = ["ERROR:", "conflict", "Conflict", "Incompatible", "ResolutionImpossible"]
    lines = full_log.splitlines()
    for line in lines:
        clean_line = line.strip()
        if clean_line.startswith("ERROR:") or any(k in clean_line for k in keywords):
            if len(clean_line) > 120: clean_line = clean_line[:117] + "..."
            error_lines.append(clean_line)
    if not error_lines and lines: error_lines = lines[-3:]
    return error_lines

def mode_install_dependencies():
    target_directory = get_target_directory(allow_create=False)
    
    print("\n" + "-"*50)
    print(f"{t('scanning')}{target_directory}")
    print("-" * 50)

    python_exec = sys.executable 
    print_color(Colors.YELLOW, f"Using Python Interpreter: {python_exec}")
    print("-" * 50)

    processed, failed, skipped = [], [], []
    conflict_details = {}
    items = sorted([x for x in target_directory.iterdir() if x.is_dir()])

    for item in items:
        if item.name in IGNORE_LIST: continue
        req_file = item / "requirements.txt"
        if req_file.exists():
            print_color(Colors.CYAN, f"{t('found_req')}{item.name}")
            print(t('installing'))
            print("-" * 20 + " PIP LOG " + "-" * 20)
            
            cmd = [python_exec, "-m", "pip", "install", "-r", req_file]
            return_code, full_log = run_command_stream(cmd, cwd=item)
            
            print("-" * 20 + " END LOG " + "-" * 20)
            if return_code == 0:
                print_color(Colors.GREEN, t('success').format(item.name))
                processed.append(item.name)
            else:
                print_color(Colors.RED, t('fail').format(item.name))
                failed.append(item.name)
                conflict_details[item.name] = extract_error_info(full_log)
        else:
            skipped.append(item.name)
        print("="*50 + "\n")

    print("\n" + "="*20 + t('summary_header') + "="*20)
    print(f"Success: {len(processed)} | Failed: {len(failed)} | Skipped: {len(skipped)}")
    if failed:
        print("\n" + "="*20 + t('conflict_header') + "="*20)
        for name in failed:
            print(f"\n[ {name} ]")
            for err in conflict_details.get(name, []):
                print_color(Colors.YELLOW, f"    {err}")
    print("\n" + t('done'))

def main():
    set_language_interactive()
    print(f"\n{t('menu_header')}")
    print(t('menu_1'))
    print(t('menu_2'))
    choice = input(t('menu_prompt')).strip()
    if choice == '1': mode_git_clone()
    elif choice == '2': mode_install_dependencies()

if __name__ == "__main__":
    if "--lang" in sys.argv:
        try:
            idx = sys.argv.index("--lang")
            lang_arg = sys.argv[idx + 1]
            if lang_arg in ['EN', 'CHT']:
                current_lang = lang_arg
        except:
            pass 

    if "--clone" in sys.argv:
        mode_git_clone()
    elif "--install" in sys.argv:
        mode_install_dependencies()
    else:
        main()