# Cook.ai 後端專案

此目錄包含 Cook.ai 專案的 Python 後端，它使用 Flask 和一個精密的多層級 AI Agent 架構建置。

## 開始使用

請遵循以下步驟來設定並執行後端服務。

### 1. 設定虛擬環境

在專案根目錄 (`Cook.ai/`)，建立並啟用 Python 虛擬環境。

```bash
# 建立 venv
python3 -m venv venv

# 啟用 venv
source venv/bin/activate
```

### 2. 安裝依賴套件

從 `requirements.txt` 檔案中安裝所有必要的 Python 套件。

```bash
pip install -r backend/requirements.txt
```

### 3. 設定環境變數

在 `backend` 目錄下建立一個 `.env` 檔案。此檔案用於儲存金鑰等機密資訊。

```bash
# backend/.env
OPENAI_API_KEY='sk-Your-Secret-Key-Goes-Here'
```

## 如何執行 Agent

AI Agent 系統的主要入口是總協調器 (`main orchestrator`)。若要以互動模式執行它：

1.  切換到 `backend` 目錄：
    ```bash
    cd backend
    ```
2.  執行總協調器模組：
    ```bash
    python -m app.agents.main_orchestrator
    ```

腳本將會提示您輸入查詢以開始互動。

---

## 架構與重要規則

我們建立了一個可擴展、由註冊表驅動的多層級 Agent 架構。

### 核心規則：Agent 註冊表 (The "Specification")

-   **位置**: `backend/app/agents/registry.py`
-   **目的**: 此檔案是系統中所有可用 Agent 和功能的**單一事實來源 (Single Source of Truth)**。它扮演著官方「Agent 規格書」的角色。
-   **維護**: 無論是想查看所有可用的 Agent，或是要註冊一個新的 Agent，這都是**第一個且最重要的需要檢查與修改的檔案**。

### 決策者：總協調器 (Main Orchestrator)

-   **檔案**: `backend/app/agents/main_orchestrator.py`
-   **角色**: 這是最高層級的 Agent (L3) 和系統主要入口。它扮演著「總指揮」或路由器的角色。
-   **邏輯**: 它**不包含**關於它能做什麼的寫死邏輯。相反地，它會**動態地讀取 `registry.py`** 來理解它的能力，並決定如何路由使用者的查詢。

### 今日實作功能 (考題生成)

今天，我們實作了一個完整的端到端工作流程，用於從 PDF 文件生成考題。

-   **多模態文件讀取器** (`app/services/document_loader/`):
    一個可以從 PDF 檔案中解析文字和圖片的服務。它會自動將所有圖片轉換為網路安全的 PNG 格式。

-   **考題生成 Agent** (`app/agents/material_generator/`):
    一個包含題目建立邏輯的子圖 (sub-graph)。它擁有針對不同題型（選擇題、簡答題、是非題）的專門化節點，每個節點都有精細調整過的提示詞。

### 如何擴充系統 (未來擴展)

若要新增一個 Agent（例如「摘要 Agent」）：

1.  **實作邏輯**: 建立 Agent 的核心邏輯（例如，在一個新的 `app/agents/summarizer/` 目錄中）。
2.  **新增處理節點**: 在 `main_orchestrator.py` 中，新增一個處理節點（例如 `run_summarizer_node`），讓它知道如何呼叫您在第一步中建立的新 Agent。
3.  **註冊 Agent**: 在 **`app/agents/registry.py`** 檔案中，為您的新 Agent 新增一筆規格。這是讓總協調器意識到新功能的關鍵步驟。

這種由註冊表驅動的設計，使得系統高度模組化且易於擴展。