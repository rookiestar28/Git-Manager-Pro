import os
import subprocess
import argparse
import sys
import platform
from pathlib import Path
from typing import List, NamedTuple
from datetime import datetime

# --- Configuration: 永久排除名單 ---
MANUAL_EXCLUDE_LIST = [
    "__pycache__", ".git", ".vscode", ".idea", 
    "archive_models", "temp_backup", "venv", "env"
]

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

if platform.system() == "Windows":
    os.system('color')

TEXT = {
    'EN': {
        'header': "--- Git Repository Manager (Pro) ---",
        'target_dir': "Target Directory: {}",
        'err_path': "Error: Directory '{}' does not exist.",
        'list_read': "Reading list file: {}",
        'list_err': "Error reading list file: {}",
        'scanning': "Scanning directory...",
        'temp_exclude': "Temporary Exclusion List: {}",
        'exclude_blacklisted': "  -> [Excluded] Directory '{}' is in the manual blacklist.",
        
        'phase_convert': "Phase 1: Project Conversion (Non-Git -> Git)",
        'phase_update': "Phase 2: Project Update (Git Pull)",
        'phase_reset': "Phase: Time Machine (Git Reset)",
        
        'conv_start': "  -> [Converting] '{}'...",
        'conv_success': "  -> [Success] Converted '{}'",
        'conv_fail': "  -> [Failed] Error converting '{}': {}",
        'reset_warn': "      'origin/main' not found, trying 'origin/master'...",
        
        'check_proj': "Checking Project: '{}'",
        'no_upstream': "  -> [Ignored] No upstream branch tracked (No Upstream).",
        'ask_update': "  Update '{}'? (y/n): ",
        'usr_skip': "  -> [Skipped] User selected skip.",
        'detect_sub': "  -> Submodules detected, enabling recursive update...",
        'up_success': "  -> [Success] '{}'",
        'up_fail': "  -> [Failed] '{}'",

        'time_fmt_err': "Error: Invalid timestamp format. Please use 'YYYY-MM-DD HH:MM:SS'.",
        'warn_title': "!!! CRITICAL WARNING !!!",
        'warn_msg': "This will perform a 'git reset --hard' on ALL target repositories.",
        'warn_desc': "All local changes and commits after '{}' will be LOST forever.",
        'warn_confirm': "Type 'YES' to confirm: ",
        'op_cancel': "Operation cancelled.",
        'reset_start': "  -> [Resetting] '{}' to '{}'...",
        'reset_success': "  -> [Success] Reset '{}'",
        'reset_fail': "  -> [Failed] Could not reset '{}'. (Check reflog existence)",
        'ask_reset': "  Reset '{}'? (y/n): ",

        'summary_header': "Execution Summary:",
        'sum_excluded': "  Excluded (Blacklist): {} folders",
        'sum_conv': "  Conversion: Success {} | Failed {}",
        'sum_up': "  Update: Success {} | Failed {}",
        'sum_reset': "  Reset: Success {} | Failed {}",
        'sum_skip': "  Skipped: {} | No Upstream/Non-Git: {}",
        'list_fail': "\n[!] The following projects failed:",
        'done': "All tasks completed."
    },
    'CHT': {
        'header': "--- Git 專案批次管理工具 (Pro) ---",
        'target_dir': "目標目錄: {}",
        'err_path': "錯誤: 目錄 '{}' 不存在。",
        'list_read': "讀取清單檔: {}",
        'list_err': "讀取清單錯誤: {}",
        'scanning': "正在掃描目錄...",
        'temp_exclude': "臨時排除名單: {}",
        'exclude_blacklisted': "  -> [已排除] 資料夾 '{}' 位於黑名單中。",
        
        'phase_convert': "階段一：專案轉換 (Convert)",
        'phase_update': "階段二：專案更新 (Pull)",
        'phase_reset': "階段：時光回溯 (Git Reset)",
        
        'conv_start': "  -> [轉換中] '{}'...",
        'conv_success': "  -> [轉換成功] '{}'",
        'conv_fail': "  -> [轉換錯誤] '{}': {}",
        'reset_warn': "      'origin/main' 不存在，嘗試 'origin/master'...",
        
        'check_proj': "檢查專案: '{}'",
        'no_upstream': "  -> [忽略] 未設定遠端追蹤分支 (No Upstream)。",
        'ask_update': "  是否更新 '{}'？ (y/n): ",
        'usr_skip': "  -> [略過] 使用者選擇跳過。",
        'detect_sub': "  -> 偵測到子模組，啟用遞歸更新 (Recursive)...",
        'up_success': "  -> [更新成功] '{}'",
        'up_fail': "  -> [更新失敗] '{}'",

        'time_fmt_err': "錯誤: 時間格式無效。請務必使用 'YYYY-MM-DD HH:MM:SS'。",
        'warn_title': "!!! 嚴重警告 !!!",
        'warn_msg': "此操作將對所有目標 Git 專案執行 'git reset --hard'。",
        'warn_desc': "所有在 '{}' 之後的提交與本地修改都將 永久遺失。",
        'warn_confirm': "請輸入 'YES' 以確認執行: ",
        'op_cancel': "操作已取消。",
        'reset_start': "  -> [回溯中] 將 '{}' 重置回 '{}'...",
        'reset_success': "  -> [回溯成功] '{}'",
        'reset_fail': "  -> [回溯失敗] '{}' (請檢查該時間點是否在 Reflog 中)",
        'ask_reset': "  是否回溯 '{}'？ (y/n): ",

        'summary_header': "執行結果總結：",
        'sum_excluded': "  已排除 (Blacklist): {} 個資料夾",
        'sum_conv': "  轉換結果: 成功 {} | 失敗 {}",
        'sum_up': "  更新結果: 成功 {} | 失敗 {}",
        'sum_reset': "  回溯結果: 成功 {} | 失敗 {}",
        'sum_skip': "  略過: {} | 無追蹤/非Git: {}",
        'list_fail': "\n[!] 以下專案執行失敗：",
        'done': "作業完成。"
    }
}

current_lang = 'EN'

def t(key):
    return TEXT[current_lang].get(key, key)

def print_color(color: str, message: str):
    print(f"{color}{message}{Colors.ENDC}")

class RepoInfo(NamedTuple):
    path: Path
    url: str = "" 


def run_command(command: List[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace'
    )

def validate_timestamp(timestamp_str: str) -> bool:
    try:
        datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False

def convert_repo(repo: RepoInfo) -> bool:
    project_path = repo.path
    project_name = project_path.name
    print_color(Colors.BLUE, t('conv_start').format(project_name))
    try:
        run_command(["git", "init"], cwd=str(project_path))
        
        remote_check = run_command(["git", "remote", "get-url", "origin"], cwd=str(project_path))
        if remote_check.returncode == 0:
            run_command(["git", "remote", "set-url", "origin", repo.url], cwd=str(project_path))
        else:
            run_command(["git", "remote", "add", "origin", repo.url], cwd=str(project_path))

        run_command(["git", "fetch", "origin"], cwd=str(project_path))

        reset_main = run_command(["git", "reset", "--hard", "origin/main"], cwd=str(project_path))
        if reset_main.returncode != 0:
            print_color(Colors.YELLOW, t('reset_warn'))
            reset_master = run_command(["git", "reset", "--hard", "origin/master"], cwd=str(project_path))
            if reset_master.returncode != 0:
                raise subprocess.CalledProcessError(reset_master.returncode, reset_master.args)
        
        print_color(Colors.GREEN, t('conv_success').format(project_name))
        return True
    except Exception as e:
        print_color(Colors.RED, t('conv_fail').format(project_name, e))
        return False

def update_repo(repo: RepoInfo, mode: str) -> tuple[str, str]:
    project_path = repo.path
    project_name = project_path.name
    
    print_color(Colors.CYAN, t('check_proj').format(project_name))

    upstream_check = run_command(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=str(project_path))
    if upstream_check.returncode != 0:
        print_color(Colors.YELLOW, t('no_upstream'))
        return "ignored", project_name

    if mode == 'interactive':
        try:
            choice = input(t('ask_update').format(project_name)).lower().strip()
            if choice != 'y':
                print_color(Colors.YELLOW, t('usr_skip'))
                return "skipped", project_name
        except:
            sys.exit(0)
    
    git_command = ["git", "pull"]
    if (project_path / ".gitmodules").is_file():
        print_color(Colors.HEADER, t('detect_sub'))
        git_command.append("--recurse-submodules")
    
    result = run_command(git_command, cwd=str(project_path))

    if result.returncode == 0:
        print_color(Colors.GREEN, t('up_success').format(project_name))
        return "success", project_name
    else:
        print_color(Colors.RED, t('up_fail').format(project_name))
        return "failed", project_name

def reset_repo(repo: RepoInfo, timestamp: str, mode: str) -> tuple[str, str]:
    project_path = repo.path
    project_name = project_path.name

    if mode == 'interactive':
        try:
            choice = input(t('ask_reset').format(project_name)).lower().strip()
            if choice != 'y':
                print_color(Colors.YELLOW, t('usr_skip'))
                return "skipped", project_name
        except:
            sys.exit(0)

    print_color(Colors.BLUE, t('reset_start').format(project_name, timestamp))
    
    cmd = ["git", "reset", "--hard", f"HEAD@{{{timestamp}}}"]
    
    result = run_command(cmd, cwd=str(project_path))

    if result.returncode == 0:
        print_color(Colors.GREEN, t('reset_success').format(project_name))
        return "success", project_name
    else:
        print_color(Colors.RED, t('reset_fail').format(project_name))
        return "failed", project_name

def manage_repositories(args: argparse.Namespace):
    base_path = Path(args.directory).resolve()
    print_color(Colors.HEADER, t('header'))
    
    if args.reset_timestamp:
        if not validate_timestamp(args.reset_timestamp):
            print_color(Colors.RED, t('time_fmt_err'))
            return
        
        print("\n" + "!"*60)
        print_color(Colors.RED, t('warn_title'))
        print_color(Colors.RED, t('warn_msg'))
        print_color(Colors.RED, t('warn_desc').format(args.reset_timestamp))
        print("!"*60)
        
        confirm = input(t('warn_confirm')).strip()
        if confirm != "YES":
            print_color(Colors.YELLOW, t('op_cancel'))
            return
        print("-" * 60)

    cli_exclude_list = args.exclude if args.exclude else []
    full_exclude_list = set(MANUAL_EXCLUDE_LIST + cli_exclude_list)
    if cli_exclude_list:
        print_color(Colors.YELLOW, t('temp_exclude').format(', '.join(cli_exclude_list)))

    if not base_path.is_dir():
        print_color(Colors.RED, t('err_path').format(base_path))
        return

    conversion_map = {}
    if args.list_file and not args.reset_timestamp and not args.skip_convert:
        list_file = Path(args.list_file).resolve()
        if list_file.is_file():
            print(t('list_read').format(list_file))
            try:
                with open(list_file, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines()]
                i = 0
                while i < len(lines):
                    if lines[i].startswith("-"):
                        name = lines[i].lstrip('-').strip()
                        if (i + 1) < len(lines) and lines[i+1].startswith(("http", "git@")):
                            conversion_map[name] = lines[i+1]
                    i += 1
            except Exception as e:
                print_color(Colors.RED, t('list_err').format(e))

    repos_to_process = []
    repos_to_convert = []
    skipped_by_exclude = []

    print(t('scanning'))
    for item in base_path.iterdir():
        if not item.is_dir(): continue
        if item.name in full_exclude_list:
            skipped_by_exclude.append(item.name)
            continue
        
        if (item / ".git").is_dir():
            repos_to_process.append(RepoInfo(path=item))
        elif item.name in conversion_map and not args.reset_timestamp:
            repos_to_convert.append(RepoInfo(path=item, url=conversion_map[item.name]))

    repos_to_process.sort(key=lambda r: r.path.name)
    failed_folders = []
    
    if args.reset_timestamp:
        print("\n" + "-"*50)
        print_color(Colors.HEADER, t('phase_reset'))
        
        success_count, failure_count, skipped_count = 0, 0, 0
        
        for repo in repos_to_process:
            status, name = reset_repo(repo, args.reset_timestamp, args.mode)
            if status == "success": success_count += 1
            elif status == "failed": 
                failure_count += 1
                failed_folders.append(name)
            elif status == "skipped": skipped_count += 1
            
        print("\n" + "="*50)
        print_color(Colors.BOLD, t('summary_header'))
        print(t('sum_reset').format(success_count, failure_count))
        print(t('sum_skip').format(skipped_count, len(repos_to_process) - success_count - failure_count - skipped_count))
        if failed_folders:
            print_color(Colors.RED, t('list_fail'))
            for name in failed_folders: print(f"  - {name}")

    else:
        converted_count, convert_failed_count = 0, 0
        if not args.skip_convert and repos_to_convert:
            print("\n" + "-"*50)
            print_color(Colors.HEADER, t('phase_convert'))
            for repo in repos_to_convert:
                if convert_repo(repo):
                    converted_count += 1
                    repos_to_process.append(repo)
                else:
                    convert_failed_count += 1
        
        success_count, failure_count, skipped_count, ignored_count = 0, 0, 0, 0
        if not args.skip_update and repos_to_process:
            print("\n" + "-"*50)
            print_color(Colors.HEADER, t('phase_update'))
            
            repos_to_process.sort(key=lambda r: r.path.name)
            
            for repo in repos_to_process:
                status, name = update_repo(repo, args.mode)
                if status == "success": success_count += 1
                elif status == "failed": 
                    failure_count += 1
                    failed_folders.append(name)
                elif status == "skipped": skipped_count += 1
                elif status == "ignored": ignored_count += 1

        print("\n" + "="*50)
        print_color(Colors.BOLD, t('summary_header'))
        if not args.skip_convert:
            print(t('sum_conv').format(converted_count, convert_failed_count))
        if not args.skip_update:
            print(t('sum_up').format(success_count, failure_count))
            print(t('sum_skip').format(skipped_count, ignored_count))
            if failed_folders:
                print_color(Colors.RED, t('list_fail'))
                for name in failed_folders: print(f"  - {name}")

    print("="*50)
    print_color(Colors.HEADER, t('done'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--directory", default=".", help="Target Directory")
    parser.add_argument("-l", "--list-file", help="List file for conversion")
    parser.add_argument("-m", "--mode", choices=['auto', 'interactive'], default='auto')
    parser.add_argument("--skip-update", action="store_true")
    parser.add_argument("--skip-convert", action="store_true")
    parser.add_argument("-e", "--exclude", nargs='+', help="Temporary exclusion list")
    
    parser.add_argument("--reset-timestamp", help="Format: YYYY-MM-DD HH:MM:SS")
    
    parser.add_argument("--lang", choices=['EN', 'CHT'], help="Language")
    
    args = parser.parse_args()
    
    if args.lang:
        current_lang = args.lang
    else:
        print("1. English\n2. Traditional Chinese")
        l = input("Select Language (1/2): ").strip()
        current_lang = 'CHT' if l == '2' else 'EN'

    manage_repositories(args)