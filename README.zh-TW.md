# Git Manager Pro: 最強大的 ComfyUI 節點自動化管理工具

<div align="center">
    <strong>繁體中文</strong> | <a href="README.md"><strong>English</strong></a>
</div>

---

## 簡介

歡迎使用 **Git Manager Pro**。這是一套專為 AI 工程師與 ComfyUI 玩家設計的腳本集合，旨在解決手動管理 `custom_nodes` 的痛點。

對 Auto Installer 而言，無論您使用系統 Python、venv、Conda 或 **ComfyUI 便攜版
(Portable/Embedded)**，啟動器都會選擇明確的 Python 目標，並透過偵測到的 bootstrap 直譯器呼叫核心程式。
啟動器不會在自身程序內執行 shell 激活命令。

---

**2025-12-10 更新：** 新增 Unix `.sh` 啟動腳本。原生啟動器行為已在 Windows `cmd.exe` 與
Linux/WSL Bash 驗證；macOS 相容性仍尚未驗證。

## 核心功能

### 工具 1： Git Manager Pro (`manage_git_pro.py`)

最強大的版本控制管理中樞。

- **批次更新 (Git Pull)**： 一鍵更新所有節點，並支援子模組 (Submodules) 遞歸更新。
- **即時串流輸出**： 更新過程中直接在終端機顯示 Git Pull 的詳細進度與訊息。
- **智慧轉換 (Convert)**： 偵測非 Git 資料夾 (解壓或複製的節點)，並根據清單自動將其「轉正」為 Git 專案,方便日後更新。
- **臨時排除 (Exclusion)**： 在更新時，可手動輸入名稱以暫時略過特定節點（例如正在開發中或不想升級的 `ComfyUI-Manager`）。
- **時光回溯 (Time Machine)**： **[新功能]** 批量將所有節點強制回退 (Reset) 到指定的時間點，當某次更新導致環境崩潰時的救命稻草。
- **安全檢查** 自動略過未設定上游追蹤 (Upstream) 的專案，保護您的本地修改不被覆蓋。

### 工具 2： Auto Installer (`auto_installer.py`)

- **批次複製專案 (Batch Git Clone)**： 讀取包含 Git URL 的清單檔案，自動將它們批次下載 (Clone) 到目標目錄。
- **批次依賴安裝**： 掃描所有資料夾中的 `requirements.txt` 並安裝其中的 Python 套件。
- **即時串流輸出**： 在終端機中即時顯示下載與安裝進度。
- **失敗摘要**： 執行結束後，自動生成略過與失敗項目的受限制摘要報告。

---

## 檔案說明

| 檔案名稱 | 說明 |
|:---------|:-----|
| `GitManagerPro.bat` | **[啟動器]** Git Manager Pro 的互動式選單入口 (更新/重置)。 |
| `Auto_Installer.bat` | **[啟動器]** Auto Installer 的互動式選單入口 (複製/安裝)。 |
| `GitManagerPro.sh` | **[啟動器]** Unix 入口；Linux/WSL 已驗證，macOS 尚未驗證。 |
| `Auto_Installer.sh` | **[啟動器]** Unix 入口；Linux/WSL 已驗證，macOS 尚未驗證。 |
| `manage_git_pro.py` | 執行 Git 相關操作的核心 Python 腳本 (V4)。 |
| `auto_installer.py` | 執行 Clone 與 Pip 安裝相關操作的核心 Python 腳本。 |

---

## 使用指南

### 前置需求

1. 電腦必須安裝 **Git** 並已加入環境變數 (PATH)。
2. 請讓啟動器與對應的 Python 腳本放在一起，並從專案目錄執行。Auto Installer 會依啟動器位置
   找到核心程式，也可以使用完整路徑啟動。
3. Auto Installer 需要可用的 Python bootstrap；會先檢查嵌入式／專案內 Python 與 venv，再退回系統
   直譯器。若明確提供目標資料夾，不需要把檔案複製到 `ComfyUI/custom_nodes/`。

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
2. 從結構化選單選擇且只能選擇一個目標：目前 Python、指定 Python 執行檔、venv 目錄、Conda 環境名稱或 Conda prefix。選擇 `取消` 會回到主選單且不啟動子程序。
3. 工具會在安裝前驗證目標，並以結構化 selector 呼叫 `auto_installer.py --install`；啟動器不會評估或
   source 激活命令。
4. 掃描所有子目錄的 `requirements.txt`。
5. 開始安裝，並在結束時以顏色標示成功與失敗的項目；子程序非零狀態會立即向上傳遞。

---

### 3. Unix 用戶支援（Linux/WSL；macOS 尚未驗證）

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

已驗證的 Linux/WSL Auto Installer 腳本固定以自身目錄為基準，並自動偵測 Python 設定，優先順序如下：

1. **便攜或專案內 Python**：自動檢查啟動器旁邊或上層目錄的嵌入式 Python 與 `venv`/`.venv`。

2. **系統 Python**：若未發現本地 bootstrap，則退回 `python3`（再退回 `python`）。

使用 Conda 時，請在安裝選單選擇 `Conda 環境名稱` 或 `Conda prefix`。啟動器會以結構化參數傳遞選擇，不需要先激活 shell，也不把已激活的 shell 視為目標身份證明。

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

# 安裝到啟動此腳本的 Python
python auto_installer.py --install --use-current-python --lang CHT

# 安裝到指定的直譯器或 venv
python auto_installer.py --install --python-executable "C:\\Tools\\Python\\python.exe" --lang CHT
python auto_installer.py --install --venv "C:\\ComfyUI\\.venv" --lang CHT

# 透過已驗證的 Conda 環境名稱或 prefix 安裝
python auto_installer.py --install --conda-env comfyui --lang CHT
python auto_installer.py --install --conda-prefix "C:\\Conda\\envs\\comfyui" --lang CHT

# 將所有節點重置回昨天中午的狀態
python manage_git_pro.py --reset-timestamp "2025-11-27 12:00:00"
```

直接安裝命令必須提供且只能提供一個環境選擇器。在掃描任何 `requirements.txt` 之前，工具會
驗證所選 Python 的執行檔、版本、prefix 與 pip 是否存在；目標無效或身份不符時，不會執行安裝
子程序。Auto Installer 的 Batch 與 Unix 啟動器提供相同的 selector 契約，並固定從啟動器目錄呼叫
核心；不會激活或修改呼叫端 shell。

### 非互動自動化

自動化呼叫端可以明確提供所有輸入。目標資料夾必須已存在；非互動複製不會建立資料夾或顯示提示，
安裝則必須提供且只能提供一個已驗證的 GMP-002 環境 selector。

```bash
# 不顯示提示，並寫入機器可讀結果檔
python auto_installer.py --clone --non-interactive \
  --target-directory "C:\\ComfyUI\\custom_nodes" \
  --clone-list "C:\\jobs\\repos.txt" --json "C:\\jobs\\clone-result.json"

# 不顯示提示；stdout 僅輸出 JSON，人類可讀進度改輸出至 stderr
python auto_installer.py --install --non-interactive \
  --target-directory "C:\\ComfyUI\\custom_nodes" \
  --use-current-python --json -
```

退出碼固定為：`0` 成功或全部略過、`2` 使用方式/輸入錯誤、`3` 目標驗證失敗、`4` 至少一個項目失敗、
`5` 互動取消，以及 `6` 機器輸出或 broken pipe 失敗。JSON 結果具有 schema 版本，只包含受限制的項目
狀態、計數、安全標籤與錯誤分類；不會包含憑證、私有 URL、絕對路徑或原始 Git/pip 輸出。`--json -`
會保留 stdout 給單一 JSON 文件；指定 JSON 路徑時，作業完成後會以原子方式替換檔案。

Schema 版本 1 維持精簡且穩定。頂層欄位為 `schema_version`（整數，固定為 `1`）、`operation`
（`clone` 或 `install`）、`status`（`success`、`usage_error`、`environment_error`、
`partial_failure`、`failure`、`cancelled` 或 `output_error`）、`exit_code`（整數）、`counts`
（`attempted`、`succeeded`、`failed`、`skipped` 整數）與 `items`（陣列）。每個項目包含
`item_id`（例如 `item-0001`）、`label`（受限制的安全識別字串）、`state`（`succeeded`、`failed`
或 `skipped`）、`attempts`（整數）及 `error_category`（null 或 `clone_failed`、`install_failed`、
`requirements_missing`、`already_exists`、`timeout`、`spawn_failed`、`input_invalid`、
`environment_invalid`、`cancelled`、`output_failed`、`broken_pipe` 其中之一）。Schema 不含時間戳、
絕對路徑、原始子程序記錄、憑證或私有 URL 元件。

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
