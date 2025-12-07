<!--
Sync Impact Report:
Version: 0.1.0 (initial creation)
Date: 2025-12-07
Changes:
  - Initial constitution creation
  - Principles: MVP導向、可測試性、品質優先、簡約設計、正體中文優先
  - Templates: 
    ✅ plan-template.md - Updated Constitution Check section with specific principles
    ✅ spec-template.md - Already aligned with MVP principles (no changes needed)
    ✅ tasks-template.md - Already aligned with MVP principles (no changes needed)
  - Follow-up: None
-->

# 專案憲章 (Project Constitution)

**專案名稱**: xuhaojun-blog  
**版本**: 0.1.0  
**批准日期**: 2025-12-07  
**最後修訂日期**: 2025-12-07

---

## 概述

本憲章定義了 xuhaojun-blog 專案的核心原則與治理規範。本專案旨在建立一個使用 LlamaIndex Agent 工作流的部落格系統，能夠自動處理對話紀錄、進行內容審閱、延伸與糾錯，並生成高品質的部落格文章。

---

## 核心原則

### 原則 1: MVP 導向開發 (MVP-First Development)

**規則**:
- 所有功能開發必須先實現最小可行版本，驗證核心價值後再擴展
- 優先實現核心工作流：內容萃取 → 審閱 → 編輯 → 輸出
- 禁止在驗證核心價值前添加非必要功能
- 每個功能迭代必須可獨立交付並產生價值

**理由**: 確保專案快速驗證核心假設，避免資源浪費在未經驗證的功能上。

---

### 原則 2: 可測試性優先 (Testability First)

**規則**:
- 所有核心功能必須具備單元測試，測試覆蓋率目標 ≥ 70%
- Agent 工作流的每個步驟必須可獨立測試
- 使用 Mock/Stub 隔離外部依賴（API、檔案系統等）
- 測試必須在 CI/CD 流程中自動執行
- 測試失敗時禁止合併程式碼

**理由**: 確保程式碼品質與可維護性，降低重構風險，支援持續整合。

---

### 原則 3: 品質優先 (Quality First)

**規則**:
- 程式碼必須通過 linter 檢查（ESLint/Prettier for JavaScript）
- 所有公開 API 必須有明確的型別定義（TypeScript 或 JSDoc）
- 錯誤處理必須完整，禁止吞掉例外
- 日誌記錄必須結構化，包含足夠的上下文資訊
- 程式碼審查必須通過至少一人審核才能合併

**理由**: 維持程式碼庫的長期可維護性，降低技術債累積。

---

### 原則 4: 簡約設計 (Simplicity Over Complexity)

**規則**:
- 禁止過度設計（overdesign），優先使用簡單直接的解決方案
- 只有在明確需要時才引入新依賴或架構模式
- 優先使用標準庫和成熟工具，避免自造輪子
- 架構決策必須有明確理由，禁止「未來可能用到」的預先設計
- 複雜度必須與問題規模成正比

**理由**: 降低維護成本，提高開發速度，避免不必要的抽象層。

---

### 原則 5: 正體中文優先 (Traditional Chinese First)

**規則**:
- 所有使用者介面、文件、註解、變數命名（如適用）優先使用正體中文
- 技術術語可使用英文，但必須提供中文說明
- API 回應與錯誤訊息必須提供正體中文版本
- README 與技術文件必須以正體中文撰寫
- 程式碼註解以正體中文為主，必要時輔以英文

**理由**: 提升專案可讀性與可維護性，符合目標使用者語言習慣。

---

## 治理規範

### 版本管理

- **版本格式**: 遵循語義化版本 (SemVer): `MAJOR.MINOR.PATCH`
  - **MAJOR**: 向後不相容的原則變更或移除
  - **MINOR**: 新增原則或重大擴展
  - **PATCH**: 澄清、修正、非語義性改進

### 修訂程序

1. 提出修訂建議（透過 Issue 或 Pull Request）
2. 至少一名核心維護者審查
3. 更新憲章版本號與最後修訂日期
4. 同步更新相關模板文件（plan-template.md, spec-template.md, tasks-template.md）
5. 在 Sync Impact Report 中記錄變更

### 合規審查

- 所有 Pull Request 必須符合本憲章的所有原則
- 定期（每季度）審查專案是否符合憲章規範
- 發現違規時必須修正或提出修訂憲章的提案

---

## 技術棧指引

### 核心技術
- **語言**: JavaScript/TypeScript
- **框架**: LlamaIndex (Python) 或 LlamaIndex.js (JavaScript)
- **工作流**: LlamaIndex Workflows 或 AgentRunner
- **測試**: Jest 或 Vitest
- **文件格式**: Markdown

### 依賴管理
- 最小化依賴數量
- 優先使用穩定版本，避免使用 beta/alpha 版本
- 定期更新依賴以修補安全漏洞

---

## 附錄

### 相關文件
- `.specify/templates/plan-template.md` - 計畫模板
- `.specify/templates/spec-template.md` - 規格模板
- `.specify/templates/tasks-template.md` - 任務模板

### 修訂歷史
- **0.1.0** (2025-12-07): 初始版本建立
