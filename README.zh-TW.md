# Git Manager Pro: 最強大的 ComfyUI 節點自動化管理工具

<div align="center">
    <strong>繁體中文</strong> | <a href="README.md"><strong>English</strong></a>
</div>

---

## 簡介

歡迎使用 **Git Manager Pro**。這是一套專為 AI 工程師與 ComfyUI 玩家設計的腳本集合，旨在解決手動管理 `custom_nodes` 的痛點。

無論您使用的是系統 Python 環境或是 **ComfyUI 便攜版 (Portable/Embedded)**，本工具都能自動偵測、並支援輸入激活命令啟動虛擬環境。

---

**2025/12/10 更新：** 新增 macOS 與 Linux 原生支援！已加入 `.sh` 啟動腳本，並更新 Unix 環境專用的操作說明文件。

## 核心功能

### 工具 1： Git Manager Pro (`manage_git_pro.py`)

最強大的版本控制管理中樞。

- **批次更新 (Git Pull)**： 一鍵更新所有節點，並支援子模組 (Submodules) 遞歸更新。
- **智慧轉換 (Convert)**： 偵測非 Git 資料夾 (解壓或複製的節點)，並根據清單自動將其「轉正」為 Git 專案,方便日後更新。
- **臨時排除 (Exclusion)**： 在更新時，可手動輸入名稱以暫時略過特定節點（例如正在開發中或不想升級的 `ComfyUI-Manager`）。
- **時光回溯 (Time Machine)**： **[新功能]** 批量將所有節點強制回退 (Reset) 到指定的時間點，當某次更新導致環境崩潰時的救命稻草。
- **安全檢查** 自動略過未設定上游追蹤 (Upstream) 的專案，保護您的本地修改不被覆蓋。

### 工具 2： Auto Installer (`auto_installer.py`)

- **批次複製專案 (Batch Git Clone)**： 讀取包含 Git URL 的清單檔案，自動將它們批次下載 (Clone) 到目標目錄。
- **批次依賴安裝**： 掃描所有資料夾中的 `requirements.txt` 並自動安裝缺失的 Python 套件。
- **即時串流輸出**： 在終端機中即時顯示下載與安裝進度。
- **衝突報告**： 執行結束後，自動生成安裝失敗與版本衝突的摘要報告。

---

## 檔案說明

| 檔案名稱 | 說明 |
|:---------|:-----|
| `GitManagerPro.bat` | **[啟動器]** Git Manager Pro 的互動式選單入口 (更新/重置)。 |
| `Auto_Installer.bat` | **[啟動器]** Auto Installer 的互動式選單入口 (複製/安裝)。 |
| `GitManagerPro.sh` | **[啟動器]** 適用於 **macOS/Linux** 的 Git Manager Pro 啟動入口。 |
| `Auto_Installer.sh` | **[啟動器]** 適用於 **macOS/Linux** 的 Auto Installer 啟動入口。 |
| `manage_git_pro.py` | 執行 Git 相關操作的核心 Python 腳本 (V4)。 |
| `auto_installer.py` | 執行 Clone 與 Pip 安裝相關操作的核心 Python 腳本。 |

---

## 使用指南

### 前置需求

1. 電腦必須安裝 **Git** 並已加入環境變數 (PATH)。
2. 使用前，請複製這些腳本放入 `ComfyUI/custom_nodes/` 資料夾中，使用後再移除。

### 1. Git Manager Pro (版本管理)

雙擊執行 `GitManagerPro.bat`,選擇對應功能:

- **[1] Auto Update All (全自動更新)**: 掃描並更新所有發現的 Git 專案。
- **[2] Interactive Update (互動模式)**: 針對每個專案逐一詢問 (Y/N) 是否更新。
- **[3] Auto Update with Exclusions (排除特定資料夾)**: 輸入資料夾名稱 (如 `NodeA NodeB`)，本次執行將完全忽略它們。
- **[4] Convert and Update (新增/修復專案)**: 需要提供一個清單檔案 (如 `repo_list.txt`)，格式為 `- 資料夾名稱` 下一行接 Git URL。
- **[6] Time Machine (Git Reset)**: ⚠️ **危險操作**
  - 將所有專案回溯到指定的時間點 (格式: `YYYY-MM-DD HH:MM:SS`)。
  - **警告**: 此操作會**丟棄**該時間點之後所有的本地修改與提交，僅在環境損壞需要救援時使用（請同時留意節點預設的 Python 套件版本是否經過變更，必要時重新安裝依賴項）。

### 2. Auto Installer (複製與安裝)

雙擊執行 `Auto_Installer.bat` 啟動選單。

#### **模式 1： 批次複製專案 (Batch Git Clone)**

適合建立新環境時，一次性的批次安裝大量節點。

1. 選擇選項 `1`。
2. 輸入目標根目錄 (例如 `custom_nodes`)。若目錄不存在，腳本將自動建立。
3. 輸入包含 Git URL 的 `.txt` 檔案路徑 (每行一個網址)。
4. 腳本將自動下載所有專案，若目標資料夾已存在則會自動略過。

#### **模式 2： 批次安裝依賴 (Batch Install Dependencies)**

掃描並安裝所有節點的需求套件。

1. 選擇選項 `2`。
2. **虛擬環境檢查 (Virtual Environment Check)**：腳本會詢問您是否需要先激活特定的環境 (如 conda 或 venv)。
   > ⚠️ **重要提示**: 如果您使用的是 **非攜帶版 (Non-Portable)** 的 ComfyUI，請務必在提示時輸入激活指令 (例如 `conda activate comfyui`)，以確保依賴項安裝到正確的環境中。
3. 腳本自動偵測您的 Python 環境 (系統或便攜版)。
4. 掃描所有子目錄的 `requirements.txt`。
5. 開始安裝，並在結束時以顏色標示成功與失敗的項目。

---

### 3. macOS 與 Linux 用戶支援

我們新增了專為 Unix 系統設計的 Shell 腳本（`.sh`）。功能與 Windows 版本一致，但針對終端機環境進行了優化。

#### 首次設定

在初次執行腳本前，必須賦予執行權限。請在腳本目錄下的終端機執行：

```bash
chmod +x GitManagerPro.sh Auto_Installer.sh
```

#### 啟動 Git Manager Pro（版本管理）

```bash
./GitManagerPro.sh
```

#### 啟動 Auto Installer（安裝工具）

```bash
./Auto_Installer.sh
```

#### 智慧環境偵測

Linux/macOS 腳本設計為自動偵測您的 Python 設定，優先順序如下：

1. **虛擬環境（venv）**：自動檢查當前或上層目錄是否存在 `venv` 或 `.venv` 資料夾。

2. **系統 Python**：若未發現虛擬環境，則退回使用系統的 `python3`。

**注意**：如果您使用的是 Conda，請確保在執行腳本前已激活環境（`conda activate environment_name`），或直接在已激活的 Conda Shell 中執行腳本即可。

---

## 進階設定

### 永久黑名單 (Permanent Blacklist)

您可以編輯 `manage_git_pro.py`，將希望**永遠忽略**的資料夾名稱加入清單：

```python
# 在 manage_git_pro.py 內
MANUAL_EXCLUDE_LIST = [
    "__pycache__", ".git", "archive_models", "temp_backup"
]
```

### 自動化整合 (CLI)

您可以在自己的腳本中直接呼叫 Python 核心，支援完整參數：

```bash
# 全自動更新，跳過轉換步驟，強制使用繁體中文介面
python manage_git_pro.py --directory "B:\ComfyUI\custom_nodes" --mode auto --skip-convert --lang CHT

# 從清單批次複製專案
python auto_installer.py --clone --lang CHT

# 將所有節點重置回昨天中午的狀態
python manage_git_pro.py --reset-timestamp "2025-11-27 12:00:00"
```

---

## 免責聲明

時光回溯 (Time Machine) 功能執行的是 `git reset --hard`，未提交的修改資料將全部遺失；在進行重大操作前，請務必備份 `custom_nodes` 資料夾。

本工具旨在輔助開發與管理，請根據自身風險評估使用。

---

## 授權條款

本專案為開源專案，供社群自由使用。

---

## 貢獻

歡迎提交貢獻、問題回報或功能建議!請隨時查看 issues 頁面。

---

## 聯絡方式

如有問題或需要支援，請在儲存庫中開啟 issue。

---

<div align="center">
用 ❤️ 為 ComfyUI 社群打造
</div>