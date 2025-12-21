# AI Conversation to Blog Agent System

https://xuhaojun.github.io/xuhaojun-blog/

一個使用 LlamaIndex 工作流將 AI 對話紀錄轉換為結構化部落格文章的系統。系統不僅提取知識內容，還提供 Prompt Engineering 優化建議，幫助使用者學習如何更有效地與 AI 互動。

## ✨ 功能特色

### 核心功能

- **📝 對話轉部落格**: 自動將 AI 對話紀錄轉換為結構化的 Markdown 部落格文章
- **🔍 內容萃取**: 智能提取關鍵洞察與核心概念，過濾無關內容
- **✏️ 內容審閱**: 自動檢查邏輯漏洞、事實錯誤，並提供改進建議
- **📚 內容延伸**: 識別知識缺口並自動補充相關背景資訊
- **💡 Prompt 分析**: 分析使用者提問，提供至少 3 個優化候選方案
- **🎨 Side-by-Side UI**: 獨特的雙欄設計，同時展示內容與 Prompt 優化建議

### 技術特色

- **多語言架構**: Python (LlamaIndex) + TypeScript (Next.js)
- **型別安全**: gRPC 協議確保跨語言通信的型別安全
- **向量搜尋**: PostgreSQL + pgvector 支援語義搜尋
- **智能快取**: 自動檢測檔案變更，避免重複處理

## 🏗️ 系統架構

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────┐
│  TypeScript CLI │ ──gRPC──▶│  Python Server   │ ────────▶│  PostgreSQL  │
│  (Next.js Web)  │         │  (LlamaIndex)    │         │  + pgvector  │
└─────────────────┘         └──────────────────┘         └──────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │  External APIs   │
                            │  (LLM, Tavily)   │
                            └──────────────────┘
```

### 工作流程

1. **內容萃取** (Content Extractor): 從對話紀錄中提取核心觀點
2. **審閱與糾錯** (Reviewer): 檢查邏輯與事實錯誤
3. **內容延伸** (Extender): 補充背景知識與相關資訊
4. **Prompt 分析** (Prompt Analyzer): 分析並優化使用者提問
5. **最終編輯** (Editor): 生成結構化的部落格文章

## 🚀 快速開始

### 前置需求

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (Python 套件管理器)
- [pnpm](https://pnpm.io/) (Node.js 套件管理器)

### 安裝步驟

1. **安裝依賴工具**

```bash
# 安裝 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安裝 pnpm
npm install -g pnpm
```

2. **設定開發環境**

```bash
# 啟動 PostgreSQL + pgvector
docker-compose up -d db

# 設定 Python 環境
cd python-workspace/apps/server
uv sync --extra dev

# 設定 TypeScript 環境
cd ../typescript-workspace
pnpm install
```

3. **設定環境變數**

建立 `.env` 檔案：

```bash
# Python Server (.env in python-workspace/apps/server/)
DATABASE_URL=postgresql://postgres:test@localhost:5432/blog_agent
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key

# TypeScript CLI (.env in typescript-workspace/apps/cli/)
NEXT_PUBLIC_API_URL=http://localhost:50051
```

4. **初始化資料庫**

```bash
cd python-workspace/apps/server
uv run python -m blog_agent.storage.migrations.init_db
```

5. **生成 Protocol Buffers 程式碼**

```bash
./scripts/generate-proto.sh
```

## 📖 使用方式

### 準備對話紀錄檔案

1. **建立對話紀錄目錄**（如果尚未存在）：
```bash
mkdir -p conversations
```

2. **檔案命名規則**：
   - 格式：`YYYY-MM-DD_HH-MM-SS_Model_Provider.ext`
   - 範例：`2025-12-07_15-30-59_Gemini_Google_Gemini.md`
   - 說明：
     - `YYYY-MM-DD_HH-MM-SS`: 日期時間戳記（ISO 8601 格式）
     - `Model`: AI 模型名稱（如 Gemini、GPT-4、Claude）
     - `Provider`: 服務提供者（如 Google_Gemini、OpenAI、Anthropic）
     - `ext`: 檔案副檔名（`.md`、`.json`、`.csv`、`.txt`）

3. **將對話紀錄檔案放入 `conversations/` 目錄**

### CLI 基本使用

```bash
# 處理對話紀錄
cd typescript-workspace/apps/cli
pnpm start process --file ../../../conversations/2025-12-07_15-30-59_Gemini_Google_Gemini.md --format markdown

# 強制重新處理（即使檔案未更新）
pnpm start process --file ../../../conversations/2025-12-07_15-30-59_Gemini_Google_Gemini.md --format markdown --force

# 列出所有已處理的對話紀錄
pnpm start list

# 取得生成的部落格文章
pnpm start get-blog --id <blog-post-id>
```

### 檔案更新處理邏輯

- **自動更新檢測**: 系統會自動檢測檔案內容是否變更（使用 SHA-256 hash）
- **未更新時**: 如果檔案內容未變更，系統會跳過處理並提示（除非使用 `--force`）
- **已更新時**: 如果檔案內容已變更，系統會自動重新處理並生成新的部落格文章
- **強制處理**: 使用 `--force` 參數可強制重新處理，即使檔案內容未變更

### 啟動 gRPC Server

```bash
# 在一個終端機
cd python-workspace/apps/server
uv run python -m blog_agent.main
```

## 📁 專案結構

```
xuhaojun-blog/
├── python-workspace/          # Python 後端
│   └── apps/
│       └── server/            # gRPC server + LlamaIndex workflows
│           ├── src/blog_agent/
│           │   ├── workflows/ # 工作流步驟
│           │   ├── services/  # 外部服務整合
│           │   ├── parsers/   # 對話紀錄解析器
│           │   └── storage/   # 資料持久層
│           └── tests/
│
├── typescript-workspace/      # TypeScript 前端
│   ├── apps/
│   │   ├── cli/               # CLI 應用
│   │   └── web/               # Next.js Web UI (可選)
│   └── packages/
│       ├── proto-gen/         # 生成的 gRPC 程式碼
│       └── rpc-client/       # 共用的 gRPC client
│
├── share/
│   └── proto/                 # Protocol Buffers 定義
│       └── blog_agent.proto
│
├── conversations/             # 使用者原始對話紀錄存放目錄
│   └── YYYY-MM-DD_HH-MM-SS_Model_Provider.ext
│
├── specs/
│   └── 001-conversation-blog-agent/  # 功能規格文件
│       ├── spec.md           # 功能規格
│       ├── plan.md           # 實作計劃
│       ├── data-model.md     # 資料模型
│       ├── uiux.md           # UI/UX 設計
│       └── quickstart.md     # 快速開始指南
│
└── scripts/
    ├── generate-proto.sh     # 生成 Protocol Buffers 程式碼
    └── setup-dev.sh          # 開發環境設定
```

## 🎨 UI/UX 設計

系統採用 **Side-by-Side (並排/雙欄)** 設計，提供獨特的閱讀體驗：

### Desktop (70/30 雙欄)

- **左側 (70%)**: 經過整理的流暢文章內容
- **右側 (30%)**: Sticky Sidebar 顯示對應段落的 Prompt 優化建議
- **自動追蹤**: 使用 Intersection Observer API 自動切換顯示對應的 Prompt 卡片

### Mobile (行內展開)

- 採用 Accordion 模式，在文章段落間插入「💡 查看此段落的 Prompt 技巧」按鈕
- 點擊後展開顯示優化建議與候選方案

### Prompt 卡片結構

1. **🔴 原始提問**: 使用者原本的提問
2. **🧐 AI 診斷**: 對提問的簡短評語
3. **🟢 優化建議**: 3 個優化候選方案（結構化版、角色扮演版、思維鏈版）
4. **🚀 預期效果**: 解釋為什麼優化版本更好

詳細設計請參考 [uiux.md](./specs/001-conversation-blog-agent/uiux.md)

## 🧪 測試

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

## 🔧 開發工作流

### 修改 Python 工作流

```bash
cd python-workspace/apps/server
# 編輯 workflows/blog_workflow.py
uv run pytest tests/  # 執行測試
```

### 修改 TypeScript CLI

```bash
cd typescript-workspace/apps/cli
# 編輯 src/commands/process.ts
pnpm test  # 執行測試
```

### 重新生成 Protocol Buffers

修改 `share/proto/blog_agent.proto` 後：

```bash
./scripts/generate-proto.sh
```

## 📚 文件

- [功能規格](./specs/001-conversation-blog-agent/spec.md)
- [實作計劃](./specs/001-conversation-blog-agent/plan.md)
- [資料模型](./specs/001-conversation-blog-agent/data-model.md)
- [UI/UX 設計](./specs/001-conversation-blog-agent/uiux.md)
- [快速開始指南](./specs/001-conversation-blog-agent/quickstart.md)

## 🐛 疑難排解

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
```

### 依賴安裝問題

```bash
# Python: 清除快取並重新安裝
cd python-workspace
uv cache clean
uv sync

# TypeScript: 清除 node_modules
cd typescript-workspace
rm -rf node_modules
pnpm install
```

## 🎯 設計理念

這個專案不僅是簡單的內容轉換工具，更是一個**元學習（Meta-learning）**平台：

- **知識層**: 展示經過整理的知識內容
- **教學層**: 展示如何獲取知識的技術（Prompt Engineering）
- **價值**: 幫助使用者學習如何更有效地與 AI 互動

透過 Side-by-Side 的呈現方式，讀者可以同時學習內容與 Prompt Engineering 技巧，提供獨特的學習體驗。

## 📝 授權

[待補充]

## 🤝 貢獻

[待補充]

---

**專案狀態**: 開發中  
**功能分支**: `001-conversation-blog-agent`  
**建立日期**: 2025-12-07

