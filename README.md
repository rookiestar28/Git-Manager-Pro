# Git Manager Pro: The most powerful toolkit for managing ComfyUI custom nodes

<div align="center">
    <strong>English</strong> | <a href="README.zh-TW.md"><strong>繁體中文</strong></a>
</div>

---

## Introduction

Welcome to the **Git Manager Pro**. This collection of scripts is designed specifically for AIGC engineers and ComfyUI enthusiasts to automate the tedious management of `custom_nodes`.

For Auto Installer, whether you use system Python, a venv, Conda, or the ComfyUI Portable (Embedded)
version, the launchers select a concrete Python target and invoke the core through a discovered
bootstrap interpreter. They do not execute shell activation commands inside the launcher process.

---

**2025-12-10 update:** Added Unix `.sh` launcher scripts. Native launcher behavior is verified on
Windows `cmd.exe` and Linux/WSL Bash; macOS compatibility remains unverified.

## Key Features

### Tool 1: Git Manager Pro (`manage_git_pro.py`)

The ultimate solution for version control management.

- **Batch Update (Git Pull)**: Automatically update all nodes. Supports recursive updates for submodules.
- **Real-time Streaming**: Displays detailed git output (e.g., file changes) directly in the terminal during updates.
- **Smart Conversion**: Detects non-Git folders (unzipped/copied nodes) and converts them into proper Git repositories using a mapping list.
- **Session Exclusion**: Temporarily skip specific nodes (e.g., `ComfyUI-Manager` or active development folders) during an update session.
- **Time Machine (Git Reset)**: **[New]** Mass revert all repositories to a specific timestamp. Lifesaver when a global update breaks your workflow (Please also check if the default Python package versions for the nodes have been modified, and reinstall dependencies if necessary).
- **Safety Checks**: Skips repositories with no upstream tracking (detached HEAD) to protect your local modifications.

### Tool 2: Auto Installer (`auto_installer.py`)

- **Batch Git Clone**: Reads a list of Git URLs from a text file and clones them into a target directory automatically.
- **Batch Pip Install**: Scans all folders for `requirements.txt` and installs their dependencies.
- **Real-time Streaming**: View download and installation progress live in the terminal.
- **Failure Summary**: Generates a bounded summary of skipped and failed items at the end.

---

## Included Files

| File | Description |
|:-----|:------------|
| `GitManagerPro.bat` | **[Launcher]** The entry point for Git Manager Pro (Updates/Resets). |
| `Auto_Installer.bat` | **[Launcher]** The entry point for the Auto Installer (Cloning/Installing). |
| `GitManagerPro.sh` | **[Launcher]** Unix entry point; Linux/WSL is verified and macOS is unverified. |
| `Auto_Installer.sh` | **[Launcher]** Unix entry point; Linux/WSL is verified and macOS is unverified. |
| `manage_git_pro.py` | The core Python script for Git operations (V4). |
| `auto_installer.py` | The core Python script for Cloning and Pip operations. |

---

## Usage Guide

### Prerequisites

1. **Git** must be installed and added to your system PATH.
2. Keep each launcher beside its matching Python script and run it from the project directory. The
   Auto Installer resolves its core relative to the launcher, so it can also be started by full path.
3. Auto Installer needs a usable Python bootstrap; it checks embedded/project-local Python and venvs
   before falling back to a system interpreter. You do not need to copy the files into
   `ComfyUI/custom_nodes/` when supplying an explicit target directory.

### 1. Git Manager Pro

Double-click `GitManagerPro.bat` to launch the menu.

- **[1] Auto Update All**: Updates every Git repository found in the target directory.
- **[2] Interactive Update**: Asks for confirmation (Y/N) before updating each repository.
- **[3] Auto Update with Exclusions**: Allows you to type folder names (e.g., `NodeA NodeB`) to skip them for this session.
- **[4] Convert and Update**: Requires a list file (e.g., `repo_list.txt`) containing lines like `- FolderName` followed by the Git URL. Converts plain folders to Git repos.
- **[6] Time Machine (Git Reset)**: ⚠️ **DANGER**
  - Reverts all repositories to a specific timestamp (Format: `YYYY-MM-DD HH:MM:SS`).
  - **Warning**: This discards all local changes and commits made after that time. Use this only to recover a working environment after a broken update.

### 2. Auto Installer (Clone & Install)

Double-click `Auto_Installer.bat` to launch the menu.

#### **Mode 1: Batch Git Clone**

Ideal for setting up a new environment or migrating nodes.

1. Select Option `1`.
2. Enter the target directory (e.g., `custom_nodes`). The script can create it if it doesn't exist.
3. Provide the path to a `.txt` file containing Git URLs (one URL per line).
4. The script will clone all repositories sequentially, skipping any that already exist.

#### **Mode 2: Batch Install Dependencies**

Scans and installs requirements for all nodes.

1. Select Option `2`.
2. Select exactly one target from the structured menu: current Python, an explicit Python executable, a venv directory, a Conda environment name, or a Conda prefix. Choose `Cancel` to return to the main menu without running the child process.
3. The selected target is validated before installation and is passed to `auto_installer.py --install`
   as a structured selector. The launcher never evaluates or sources an activation command.
4. It scans all subdirectories for `requirements.txt`.
5. It attempts to install dependencies and provides a colored summary report upon completion. A non-zero child status is returned immediately.

### 3. Unix Support (Linux/WSL; macOS Unverified)

We have introduced dedicated shell scripts (`.sh`) for Unix-based systems. The functionality mirrors the Windows version but is optimized for Terminal environments.

#### **Initial Setup**

Before running the scripts for the first time, you must grant execution permissions. Open your terminal in the script directory and run:

```bash
chmod +x GitManagerPro.sh Auto_Installer.sh
```

#### **Launch Git Manager Pro**

```bash
./GitManagerPro.sh
```

#### **Launch Auto Installer**

```bash
./Auto_Installer.sh
```

#### **Smart Environment Detection**

The verified Unix Auto Installer launcher is anchored to its own script directory and discovers a
bootstrap Python in the following priority:

1. **Portable or project-local Python**: It checks embedded Python and `venv`/`.venv` beside the launcher or in its parent directory.

2. **System Python**: Falls back to `python3` (then `python`) if no local bootstrap is found.

For Conda, choose `Conda environment name` or `Conda prefix` in the install menu. The launcher passes the
selection as structured arguments; an already activated shell is not required or treated as target
identity proof. Native launcher behavior is verified on Windows `cmd.exe` and Linux/WSL Bash; macOS
behavior remains unverified.

---

## Advanced Configuration

### Permanent Blacklist

You can edit `manage_git_pro.py` to add folders that should **always** be ignored (e.g., backup folders).

```python
# Inside manage_git_pro.py
MANUAL_EXCLUDE_LIST = [
    "__pycache__", ".git", "archive_models", "my_secret_node"
]
```

### Automation (CLI)

You can call the Python script directly from your own scripts:

```bash
# Update all, skip conversion, use Traditional Chinese
python manage_git_pro.py --directory "B:\ComfyUI\custom_nodes" --mode auto --skip-convert --lang CHT

# Clone repositories from a list
python auto_installer.py --clone --lang EN

# Install into the Python that launched the script
python auto_installer.py --install --use-current-python --lang EN

# Install into an explicit interpreter or venv
python auto_installer.py --install --python-executable "C:\\Tools\\Python\\python.exe" --lang EN
python auto_installer.py --install --venv "C:\\ComfyUI\\.venv" --lang EN

# Install through a validated Conda environment name or prefix
python auto_installer.py --install --conda-env comfyui --lang EN
python auto_installer.py --install --conda-prefix "C:\\Conda\\envs\\comfyui" --lang EN

# Reset all nodes to yesterday noon
python manage_git_pro.py --reset-timestamp "2025-11-27 12:00:00"
```

The direct install command requires exactly one environment selector. Before scanning any
`requirements.txt`, it probes the selected Python for its executable, version, prefix, and pip
availability. Invalid or mismatched targets fail without running an install subprocess. The Auto
Installer Batch and Unix launchers expose the same selector contract and keep the core invocation
anchored to the launcher directory; they do not activate or mutate the caller's shell.

### Non-interactive automation

Automation callers can provide every input explicitly. The target directory must already exist;
non-interactive clone never creates directories or prompts, and install requires exactly one validated
GMP-002 environment selector.

```bash
# Clone without prompts and write a machine-readable result file
python auto_installer.py --clone --non-interactive \
  --target-directory "C:\\ComfyUI\\custom_nodes" \
  --clone-list "C:\\jobs\\repos.txt" --json "C:\\jobs\\clone-result.json"

# Install without prompts; stdout is JSON and human progress is on stderr
python auto_installer.py --install --non-interactive \
  --target-directory "C:\\ComfyUI\\custom_nodes" \
  --use-current-python --json -
```

Exit codes are stable: `0` success or all-skipped, `2` usage/input error, `3` target validation
failure, `4` one or more item failures, `5` interactive cancellation, and `6` machine-output or
broken-pipe failure. A JSON result is schema-versioned and contains only bounded item states, counts,
safe labels, and error categories; it never includes credentials, private URLs, absolute paths, or
raw Git/pip output. `--json -` reserves stdout for the single JSON document, while a JSON path is
replaced atomically after the operation.

Schema version 1 is intentionally small and stable. The top-level fields are `schema_version` (integer,
always `1`), `operation` (`clone` or `install`), `status` (`success`, `usage_error`,
`environment_error`, `partial_failure`, `failure`, `cancelled`, or `output_error`), `exit_code` (integer),
`counts` (`attempted`, `succeeded`, `failed`, `skipped` integers), and `items` (an array). Each item has
`item_id` (`item-0001` style), `label` (a bounded safe identifier), `state` (`succeeded`, `failed`, or
`skipped`), `attempts` (integer), and `error_category` (null or one of `clone_failed`, `install_failed`,
`requirements_missing`, `already_exists`, `timeout`, `spawn_failed`, `input_invalid`,
`environment_invalid`, `cancelled`, `output_failed`, or `broken_pipe`). Timestamps, absolute paths, raw
child logs, credentials, and private URL components are never schema fields.

---

## Disclaimer

The Time Machine feature performs a `git reset --hard`. Data loss is expected for uncommitted changes. Always backup your `custom_nodes` folder before major operations.

This tool is provided "as is" to help the community.

---

## License

This project is open source and available for community use.

---

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

---

## Contact

For questions or support, please open an issue in the repository.
