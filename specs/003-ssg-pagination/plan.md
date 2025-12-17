# Implementation Plan: SSG Pagination

**Branch**: `003-ssg-pagination` | **Date**: 2025-12-17 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/003-ssg-pagination/spec.md`

## Summary

將首頁從一次載入全部文章改為 Hugo 風格的靜態分頁 (`/page/1`, `/page/2`, ...)，首頁 `/` 作為第一頁的別名。使用 Next.js App Router 的 `generateStaticParams()` 在建置時生成所有分頁靜態頁面。

## Technical Context

**Language/Version**: TypeScript 5.9, Node.js 24  
**Primary Dependencies**: Next.js 16 (App Router), React 19, shadcn/ui pagination component  
**Storage**: N/A (靜態網站，資料來自 gRPC API)  
**Testing**: Vitest (待加入)  
**Target Platform**: 靜態網站 (Next.js static export)  
**Project Type**: Web application (monorepo with pnpm workspaces)  
**Performance Goals**: < 1s 頁面載入時間, Lighthouse 90+ 分數  
**Constraints**: 建置時必須能連接 gRPC 服務取得文章資料  
**Scale/Scope**: 預估 < 1000 篇文章，每頁 10 篇

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 原則 1: MVP 導向開發
- [x] 功能是否先實現最小可行版本？ → 僅實作核心分頁功能，不含進階過濾或搜尋
- [x] 是否優先實現核心工作流？ → 專注於 `/page/[n]` 路由與首頁別名
- [x] 是否避免在驗證前添加非必要功能？ → 不新增分類、標籤篩選等功能

### 原則 2: 可測試性優先
- [x] 是否規劃單元測試（目標覆蓋率 ≥ 70%）？ → 分頁計算邏輯可測試
- [x] 每個工作流步驟是否可獨立測試？ → 分頁邏輯獨立於 UI 元件
- [x] 是否規劃 Mock/Stub 隔離外部依賴？ → gRPC client 可 mock
- [x] 測試是否納入 CI/CD 流程？ → 沿用現有 CI 設定

### 原則 3: 品質優先
- [x] 是否配置 linter（ESLint/Prettier）？ → 沿用現有設定
- [x] 是否規劃型別定義（TypeScript）？ → 完整 TypeScript 型別
- [x] 是否規劃完整的錯誤處理？ → 404 處理、API 錯誤處理
- [x] 是否規劃結構化日誌記錄？ → 沿用 console.error 於建置時

### 原則 4: 簡約設計
- [x] 是否避免過度設計？ → 直接使用 Next.js 內建 SSG 機制
- [x] 是否優先使用簡單直接的解決方案？ → 不引入額外 state management
- [x] 新依賴是否有明確理由？ → 不新增依賴，使用現有 shadcn pagination
- [x] 複雜度是否與問題規模成正比？ → 簡單的分頁計算 + 路由結構

### 原則 5: 正體中文優先
- [x] 使用者介面是否使用正體中文？ → 沿用現有中文 UI
- [x] 文件是否以正體中文撰寫？ → 本計畫以正體中文撰寫
- [x] 程式碼註解是否以正體中文為主？ → 維持現有風格

## Project Structure

### Documentation (this feature)

```text
specs/003-ssg-pagination/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no API changes)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
typescript-workspace/apps/web/
├── app/
│   ├── page.tsx                    # 首頁 (渲染第一頁，作為 /page/1 別名)
│   ├── page/
│   │   └── [pageNumber]/
│   │       └── page.tsx            # 分頁路由 (/page/1, /page/2, ...)
│   └── blog/
│       └── [id]/
│           └── page.tsx            # 現有文章頁面 (不變)
├── components/
│   ├── blog-post-list.tsx          # 新增：文章列表元件 (從 page.tsx 抽取)
│   └── blog-pagination.tsx         # 新增：分頁導覽元件 (包裝 shadcn pagination)
└── lib/
    ├── grpc-client.ts              # 現有 gRPC client (不變)
    └── pagination.ts               # 新增：分頁計算工具函式
```

**Structure Decision**: 採用現有 Next.js App Router 結構，新增 `/page/[pageNumber]` 動態路由。抽取共用元件以避免首頁與分頁重複程式碼。

## Complexity Tracking

> No constitution violations - no complexity justification needed.

