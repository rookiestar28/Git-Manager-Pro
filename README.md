# Git Manager Pro: The most powerful toolkit for managing ComfyUI custom nodes.

<div align="center">
    <strong>English</strong> | <a href="README.zh-TW.md"><strong>繁體中文</strong></a>
</div>

---

## Introduction

Welcome to the **Git Manager Pro**. This collection of scripts is designed specifically for AIGC engineers and ComfyUI enthusiasts to automate the tedious management of `custom_nodes`.

Whether you are using a system Python environment or the ComfyUI Portable (Embedded) version, this tool can automatically detect your setup and supports entering activation commands to launch virtual environments.

---

**10/12 2025 Update:** Added native support for macOS and Linux! Introduced `.sh` launcher scripts and updated the documentation with specific guides for Unix environments.

## Key Features

### Tool 1: Git Manager Pro (`manage_git_pro.py`)

The ultimate solution for version control management.

- **Batch Update (Git Pull)**: Automatically update all nodes. Supports recursive updates for submodules.
- **Smart Conversion**: Detects non-Git folders (unzipped/copied nodes) and converts them into proper Git repositories using a mapping list.
- **Session Exclusion**: Temporarily skip specific nodes (e.g., `ComfyUI-Manager` or active development folders) during an update session.
- **Time Machine (Git Reset)**: **[New]** Mass revert all repositories to a specific timestamp. Lifesaver when a global update breaks your workflow (Please also check if the default Python package versions for the nodes have been modified, and reinstall dependencies if necessary).
- **Safety Checks**: Skips repositories with no upstream tracking (detached HEAD) to protect your local modifications.

### Tool 2: Auto Installer (`auto_installer.py`)

- **Batch Git Clone**: Reads a list of Git URLs from a text file and clones them into a target directory automatically.
- **Batch Pip Install**: Scans all folders for `requirements.txt` and installs missing dependencies.
- **Real-time Streaming**: View download and installation progress live in the terminal.
- **Conflict Reporting**: Generates a summary of failed installations and potential version conflicts at the end.

---

## Included Files

| File | Description |
|:-----|:------------|
| `GitManagerPro.bat` | **[Launcher]** The entry point for Git Manager Pro (Updates/Resets). |
| `Auto_Installer.bat` | **[Launcher]** The entry point for the Auto Installer (Cloning/Installing). |
| `GitManagerPro.sh` | **[Launcher]** The entry point for Git Manager Pro on **macOS/Linux**. |
| `Auto_Installer.sh` | **[Launcher]** The entry point for the Auto Installer on **macOS/Linux**. |
| `manage_git_pro.py` | The core Python script for Git operations (V4). |
| `auto_installer.py` | The core Python script for Cloning and Pip operations. |

---

## Usage Guide

### Prerequisites

1. **Git** must be installed and added to your system PATH.
2. Before use, please copy these scripts into the ComfyUI/custom_nodes/ folder, and remove them after use.

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
2. **Virtual Environment Check**: The script will ask if you need to activate a specific environment (e.g., Conda, venv) before proceeding.
   > ⚠️ **IMPORTANT**: If you are **not** using the ComfyUI Portable version, ensure you provide the activation command (e.g., `conda activate comfyui`) when prompted. This ensures packages are installed into the correct environment.
3. The script detects the active Python environment.
4. It scans all subdirectories for `requirements.txt`.
5. It attempts to install dependencies and provides a colored summary report upon completion.

### 3. Support for macOS & Linux Users

We have introduced dedicated shell scripts (`.sh`) for Unix-based systems. The functionality mirrors the Windows version but is optimized for Terminal environments.

#### **Initial Setup**
Before running the scripts for the first time, you must grant execution permissions. Open your terminal in the script directory and run:

```bash
chmod +x GitManagerPro.sh Auto_Installer.sh

#### **Launch Git Manager Pro**

```bash
./GitManagerPro.sh
```

#### **Launch Auto Installer**

```bash
./Auto_Installer.sh
```

#### **Smart Environment Detection**

The Linux/macOS scripts are designed to automatically detect your Python setup in the following priority:

1. **Virtual Environments (venv)**: It checks for `venv` or `.venv` directories in the current or parent folders.

2. **System Python**: Falls back to `python3` if no virtual environment is found.

**Note**: If you are using Conda, please ensure your environment is activated (`conda activate environment_name`) before running the scripts, or simply run the scripts from within your active Conda shell.

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

# Reset all nodes to yesterday noon
python manage_git_pro.py --reset-timestamp "2025-11-27 12:00:00"
```

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

---

<div align="center">
Made with ❤️ for the ComfyUI Community
</div>