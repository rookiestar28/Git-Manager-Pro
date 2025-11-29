# Git Manager Pro: 最強大的 ComfyUI 節點自動化管理工具

<div align="center">
    <strong>繁體中文</strong> | <a href="README.md"><strong>English</strong></a>
</div>

---

## 簡介

歡迎使用 **Git Manager Pro**。這是一套專為 AIGC 工程師與 ComfyUI 玩家設計的腳本集合,旨在解決手動管理 `custom_nodes` 的痛點。

無論您使用的是系統 Python 環境,還是 **ComfyUI 便攜版 (Portable/Embedded)**,本工具都能自動偵測並完美執行。

---

## 核心功能

### 工具 1: Git Manager Pro (`manage_git_pro.py`)

最強大的版本控制管理中樞。

- **批次更新 (Git Pull)**: 一鍵更新所有節點。支援子模組 (Submodules) 遞歸更新。
- **智慧轉換 (Convert)**: 偵測非 Git 資料夾 (解壓或複製的節點),並根據清單自動將其「轉正」為 Git 專案,方便日後更新。
- **臨時排除 (Exclusion)**: 在更新時,可手動輸入名稱以暫時略過特定節點 (例如正在開發中或不想升級的 `ComfyUI-Manager`)。
- **時光回溯 (Time Machine)**: **[新功能]** 批量將所有節點強制回退 (Reset) 到指定的時間點。當某次更新導致環境崩潰時的救命稻草。
- **安全檢查**: 自動略過未設定上游追蹤 (Upstream) 的專案,保護您的本地修改不被覆蓋。

### 工具 2: Auto Dependency Installer (`auto_installer.py`)

- **批次依賴安裝**: 掃描所有資料夾中的 `requirements.txt` 並自動安裝缺失的 Python 套件。
- **即時串流輸出**: 在終端機中即時顯示下載與安裝進度。
- **衝突報告**: 執行結束後,自動生成安裝失敗與版本衝突的摘要報告。

---

## 檔案說明

| 檔案名稱 | 說明 |
|:---------|:-----|
| `GitManagerPro.bat` | **[啟動器]** Git Manager Pro 的互動式選單入口。 |
| `Auto_Installer.bat` | **[啟動器]** 自動依賴安裝工具的入口。 |
| `manage_git_pro.py` | 執行 Git 相關操作的核心 Python 腳本 (V4)。 |
| `auto_install.py` | 執行 Pip 安裝相關操作的核心 Python 腳本。 |

---

## 使用指南

### 前置需求

1. 電腦必須安裝 **Git** 並已加入環境變數 (PATH)。
2. 建議將這些腳本直接放入您的 `ComfyUI/custom_nodes/` 資料夾中。

### 1. Git Manager Pro (版本管理)

雙擊執行 `GitManagerPro.bat`,選擇對應功能:

- **[1] Auto Update All (全自動更新)**: 掃描並更新所有發現的 Git 專案。
- **[2] Interactive Update (互動模式)**: 針對每個專案逐一詢問 (Y/N) 是否更新。
- **[3] Auto Update with Exclusions (排除特定資料夾)**: 輸入資料夾名稱 (如 `NodeA NodeB`),本次執行將完全忽略它們。
- **[4] Convert and Update (新增/修復專案)**: 需要提供一個清單檔案 (如 `repo_list.txt`),格式為 `- 資料夾名稱` 下一行接 Git URL。
- **[6] Time Machine (Git Reset)**: ⚠️ **危險操作**
  - 將所有專案回溯到指定的時間點 (格式: `YYYY-MM-DD HH:MM:SS`)。
  - **警告**: 此操作會**丟棄**該時間點之後所有的本地修改與提交。請僅在環境損壞需要救援時使用。

### 2. Auto Dependency Installer (依賴安裝)

雙擊執行 `Auto_Installer.bat`。

1. **虛擬環境檢查 (Virtual Environment Check)**：腳本會詢問您是否需要先激活特定的環境 (如 Conda 或 venv)。
   > ⚠️ **重要提示**：如果您使用的是 **非攜帶版 (Non-Portable)** 的 ComfyUI，請務必在提示時輸入激活指令 (例如 `conda activate comfyui`)，以確保依賴項安裝到正確的環境中。
2. 腳本自動偵測您的 Python 環境 (系統或便攜版)。
3. 掃描所有子目錄的 `requirements.txt`。
4. 開始安裝，並在結束時以顏色標示成功與失敗的項目。

---

## 進階設定

### 永久黑名單 (Permanent Blacklist)

您可以編輯 `manage_git_pro.py`,將希望**永遠忽略**的資料夾名稱加入清單:

```python
# 在 manage_git_pro.py 內
MANUAL_EXCLUDE_LIST = [
    "__pycache__", ".git", "archive_models", "temp_backup"
]
```

### 自動化整合 (CLI)

您可以在自己的腳本中直接呼叫 Python 核心,支援完整參數:

```bash
# 全自動更新,跳過轉換步驟,強制使用繁體中文介面
python manage_git_pro.py --directory "B:\ComfyUI\custom_nodes" --mode auto --skip-convert --lang CHT

# 將所有節點重置回昨天中午的狀態
python manage_git_pro.py --reset-timestamp "2025-11-27 12:00:00"
```

---

## 免責聲明

- **時光回溯 (Time Machine)** 功能執行的是 `git reset --hard`。對於未提交的修改,資料遺失是預期行為。在進行重大操作前,請務必備份您的 `custom_nodes` 資料夾。
- 本工具旨在輔助開發與管理,請根據自身風險評估使用。

---

## 授權條款

本專案為開源專案,供社群自由使用。

---

## 貢獻

歡迎提交貢獻、問題回報或功能建議!請隨時查看 issues 頁面。

---

## 聯絡方式

如有問題或需要支援,請在儲存庫中開啟 issue。

---

<div align="center">
    用 ❤️ 為 ComfyUI 社群打造
</div>