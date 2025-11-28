# Git Manager Pro: The most powerful toolkit for managing ComfyUI custom nodes.

<div align="center">
    <strong>English</strong> | <a href="README.zh-TW.md"><strong>繁體中文</strong></a>
</div>

---

## Introduction

Welcome to the **Git Manager Pro**. This collection of scripts is designed specifically for AIGC engineers and ComfyUI enthusiasts to automate the tedious management of `custom_nodes`.

Whether you are using a standard Python installation or the **ComfyUI Portable (Embedded)** version, these tools automatically detect your environment and just work.

---

## Key Features

### Tool 1: Git Manager Pro (`manage_git_pro.py`)

The ultimate solution for version control management.

- **Batch Update (Git Pull)**: Automatically update all nodes. Supports recursive updates for submodules.
- **Smart Conversion**: Detects non-Git folders (unzipped/copied nodes) and converts them into proper Git repositories using a mapping list.
- **Session Exclusion**: Temporarily skip specific nodes (e.g., `ComfyUI-Manager` or active development folders) during an update session.
- **Time Machine (Git Reset)**: **[New]** Mass revert all repositories to a specific timestamp. Lifesaver when a global update breaks your workflow.
- **Safety Checks**: Skips repositories with no upstream tracking (detached HEAD) to protect your local modifications.

### Tool 2: Auto Dependency Installer (`auto_install.py`)

- **Batch Pip Install**: Scans all folders for `requirements.txt` and installs missing dependencies.
- **Real-time Streaming**: View download and installation progress live in the terminal.
- **Conflict Reporting**: Generates a summary of failed installations and potential version conflicts at the end.

---

## Included Files

| File | Description |
|:-----|:------------|
| `start_git_manager.bat` | **[Launcher]** The entry point for Git Manager Pro. |
| `start_install.bat` | **[Launcher]** The entry point for the Dependency Installer. |
| `manage_git_pro.py` | The core Python script for Git operations (V4). |
| `auto_install.py` | The core Python script for Pip operations. |

---

## Usage Guide

### Prerequisites

1. **Git** must be installed and added to your system PATH.
2. Place these scripts inside your `ComfyUI/custom_nodes/` folder (Recommended) or the ComfyUI root folder.

### 1. Git Manager Pro

Double-click `start_git_manager.bat` to launch the menu.

- **[1] Auto Update All**: Updates every Git repository found in the target directory.
- **[2] Interactive Update**: Asks for confirmation (Y/N) before updating each repository.
- **[3] Auto Update with Exclusions**: Allows you to type folder names (e.g., `NodeA NodeB`) to skip them for this session.
- **[4] Convert and Update**: Requires a list file (e.g., `repo_list.txt`) containing lines like `- FolderName` followed by the Git URL. Converts plain folders to Git repos.
- **[6] Time Machine (Git Reset)**: ⚠️ **DANGER**
  - Reverts all repositories to a specific timestamp (Format: `YYYY-MM-DD HH:MM:SS`).
  - **Warning**: This discards all local changes and commits made after that time. Use this only to recover a working environment after a broken update.

### 2. Auto Dependency Installer

Double-click `start_install.bat`.

1. The script will automatically detect your Python environment (System or ComfyUI Portable).
2. It scans all subdirectories for `requirements.txt`.
3. It attempts to install dependencies and provides a colored summary report upon completion.

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

# Reset all nodes to yesterday noon
python manage_git_pro.py --reset-timestamp "2025-11-27 12:00:00"
```

---

## Disclaimer

- The **Time Machine** feature performs a `git reset --hard`. Data loss is expected for uncommitted changes. Always backup your `custom_nodes` folder before major operations.
- This tool is provided "as is" to help the community.

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