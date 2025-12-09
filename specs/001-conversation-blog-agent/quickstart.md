# Quick Start Guide: AI Conversation to Blog Agent System

**Date**: 2025-12-07  
**Feature**: 001-conversation-blog-agent

## 前置需求

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- uv (Python 套件管理器)
- pnpm (Node.js 套件管理器)

## 安裝步驟

### 1. 安裝依賴工具

```bash
# 安裝 uv (Python)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安裝 pnpm (Node.js)
npm install -g pnpm
```

### 2. 設定開發環境

```bash
# 複製專案
git clone <repository-url>
cd xuhaojun-blog

# 啟動 PostgreSQL + pgvector
docker-compose up -d db

# 設定 Python 環境
cd python-workspace/apps/server
uv sync --extra dev

# 設定 TypeScript 環境
cd ../typescript-workspace
pnpm install
```

### 3. 設定環境變數

建立 `.env` 檔案：

```bash
# Python Server (.env in python-workspace/apps/server/)
DATABASE_URL=postgresql://postgres:test@localhost:5432/blog_agent
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key

# TypeScript CLI (.env in typescript-workspace/apps/cli/)
GRPC_SERVER_URL=http://localhost:50051
```

### 4. 初始化資料庫

```bash
# 執行資料庫遷移
cd python-workspace/apps/server
uv run python -m blog_agent.storage.migrations.init_db
```

### 5. 生成 Protocol Buffers 程式碼

```bash
# 從專案根目錄執行
./scripts/generate-proto.sh
```

## 使用方式

### 準備對話紀錄檔案

1. **建立對話紀錄目錄**（如果尚未存在）：
```bash
mkdir -p conversations
```

2. **檔案命名規則**：
   - 格式：`YYYY-MM-DD_HH-MM-SS_Model_Provider.ext`
   - 範例：`2025-12-07_15-30-59_Gemini_Google_Gemini.md`
   - 說明：
     - `YYYY-MM-DD_HH-MM-SS`：日期時間戳記（ISO 8601 格式，使用底線分隔）
     - `Model`：AI 模型名稱（如 Gemini、GPT-4、Claude）
     - `Provider`：服務提供者（如 Google_Gemini、OpenAI、Anthropic）
     - `ext`：檔案副檔名（`.md`、`.json`、`.csv`、`.txt`）

3. **將對話紀錄檔案放入 `conversations/` 目錄**

### CLI 基本使用

```bash
# 處理對話紀錄（從 conversations/ 目錄）
cd typescript-workspace/apps/cli
pnpm start process --file ../../../conversations/2025-12-07_15-30-59_Gemini_Google_Gemini.md --format markdown

# 強制重新處理（即使檔案未更新）
pnpm start process --file ../../conversations/2025-12-07_15-30-59_Gemini_Google_Gemini.md --format markdown --force

# 列出所有已處理的對話紀錄
pnpm start list

# 取得生成的部落格文章
pnpm start get-blog --id <blog-post-id>
```

### 檔案更新處理邏輯

- **自動更新檢測**：系統會自動檢測檔案內容是否變更（使用 SHA-256 hash）
- **未更新時**：如果檔案內容未變更，系統會跳過處理並提示（除非使用 `--force`）
- **已更新時**：如果檔案內容已變更，系統會自動重新處理並生成新的部落格文章
- **強制處理**：使用 `--force` 參數可強制重新處理，即使檔案內容未變更

### 啟動 gRPC Server

```bash
# 在一個終端機
cd python-workspace/apps/server
uv run python -m blog_agent.main
```

### 範例：處理 Gemini 匯出的對話紀錄

```bash
# 1. 將對話紀錄檔案放入 conversations/ 目錄
cp 2025-12-07_15-30-59_Gemini_Google_Gemini.md conversations/

# 2. 處理對話紀錄
cd typescript-workspace/apps/cli
pnpm start process \
  --file-path ../../conversations/2025-12-07_15-30-59_Gemini_Google_Gemini.md \
  --format markdown

# 輸出會顯示處理 ID 與生成的部落格文章 ID
# Processing ID: abc123...
# Blog Post ID: def456...

# 3. 如果檔案未更新，再次處理會跳過（除非使用 --force）
pnpm start process \
  --file-path ../../conversations/2025-12-07_15-30-59_Gemini_Google_Gemini.md \
  --format markdown
# 輸出：File unchanged, skipping processing. Use --force to regenerate.

# 4. 強制重新處理
pnpm start process \
  --file-path ../../conversations/2025-12-07_15-30-59_Gemini_Google_Gemini.md \
  --format markdown \
  --force
```

## 專案結構說明

```
python-workspace/apps/server/
├── src/blog_agent/
│   ├── workflows/          # LlamaIndex 工作流步驟
│   ├── services/           # 外部服務整合 (LLM, Tavily)
│   ├── parsers/            # 對話紀錄解析器
│   └── storage/            # 資料持久層

typescript-workspace/apps/cli/
├── src/
│   ├── commands/           # CLI 命令
│   └── client/             # gRPC client
```

## 開發工作流

### 1. 修改 Python 工作流

```bash
cd python-workspace/apps/server
# 編輯 workflows/blog_workflow.py
uv run pytest tests/  # 執行測試
```

### 2. 修改 TypeScript CLI

```bash
cd typescript-workspace/apps/cli
# 編輯 src/commands/process.ts
pnpm test  # 執行測試
```

### 3. 重新生成 Protocol Buffers

修改 `share/proto/blog_agent.proto` 後：

```bash
./scripts/generate-proto.sh
```

## 測試

### Python 測試

```bash
cd python-workspace/apps/server
uv run pytest tests/unit/
uv run pytest tests/integration/
```

### TypeScript 測試

```bash
cd typescript-workspace/apps/cli
pnpm test
```

## 疑難排解

### PostgreSQL 連線失敗

```bash
# 檢查 Docker 容器狀態
docker-compose ps

# 檢查資料庫日誌
docker-compose logs db
```

### gRPC 連線失敗

```bash
# 確認 server 是否運行
curl http://localhost:50051/health  # 如果實作 health check

# 檢查防火牆設定
```

### 依賴安裝問題

```bash
# Python: 清除快取並重新安裝
cd python-workspace/apps/server
uv cache clean
uv sync --extra dev

# TypeScript: 清除 node_modules
cd typescript-workspace
rm -rf node_modules
pnpm install
```

## 下一步

- 閱讀 [data-model.md](./data-model.md) 了解資料結構
- 閱讀 [contracts/blog_agent.proto](./contracts/blog_agent.proto) 了解 API 定義
- 查看範例對話紀錄: `2025-12-07_15-30-59_Gemini_Google_Gemini.md`

