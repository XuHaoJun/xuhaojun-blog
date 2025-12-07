# UI/UX Design Specification: Blog Post Display with Prompt Engineering Clinic

**Date**: 2025-12-07  
**Feature**: 001-conversation-blog-agent  
**Status**: Draft  
**Source**: Gemini conversation log (2025-12-07_21-49-37_Gemini_Google_Gemini.md)

## Overview

本文件定義系統的 UI/UX 設計規範，專注於呈現「內容」與「提問優化」的 Side-by-Side 對比。這個設計不僅展示知識，還展示如何獲取知識的技術，提供元認知（Metacognition）的教學價值。

## Design Philosophy

### 核心概念

- **知識層 (The Article)**: 經過 LlamaIndex Agent 整理、潤飾後的流暢文章
- **教學層 (The Meta-Commentary)**: Prompt 診斷室，展示原始提問與優化建議
- **元學習價值**: 不僅展示「資訊（Information）」，還展示「我是如何得到這個資訊的」

### 設計目標

1. 在 Desktop 上提供最佳的 Side-by-Side 閱讀體驗
2. 在 Mobile 上提供流暢的行內展開體驗
3. 讓讀者能夠清楚理解 Prompt 優化的價值
4. 提供互動式學習體驗（複製、對比、模擬）

---

## 1. 核心版面佈局 (Layout Strategy)

### A. Desktop (寬螢幕) - 70/30 雙欄連動

#### 左側 (70%) - The Article (知識層)

- **內容**: 經過 LlamaIndex Agent 整理、潤飾後的流暢文章
- **體驗**: 讀者可以像閱讀普通 Blog 一樣閱讀這裡
- **樣式**: 
  - 黑字白底（或深色模式）
  - Serif 字體（襯線體）增加沉浸感
  - 保持最乾淨的閱讀體驗

#### 右側 (30%) - The Meta-Commentary (教學層)

- **類型**: Sticky Sidebar (固定側欄)
- **關鍵互動**: 
  - 當讀者捲動左側文章，讀到某個段落（例如由某個 Prompt 生成的部分）時，右側會自動切換顯示該段落對應的「原始提問分析」卡片
  - 使用 Intersection Observer API 偵測使用者目前「讀到哪一段」
- **視覺連結**: 
  - 左側文章旁邊可以有一個微小的錨點圖標（例如 ⚓ 或 💡）
  - 滑鼠移過去會高亮右側對應的建議

### B. Mobile (手機) - Inline Expandable (行內展開)

- **限制**: 手機沒有寬度做 Side-by-Side
- **解決方案**: 採用「手風琴 (Accordion)」或「標註 (Annotation)」模式
- **實作**: 
  - 在文章段落之間，插入一個明顯的按鈕或區塊：「💡 查看此段落的 Prompt 技巧」
  - 點擊後，向下展開顯示優化建議與 Candidates

---

## 2. 組件設計 (Component Design)

### 卡片結構 (The Prompt Clinic Card)

這張卡片應該包含四個層次，使用不同的背景色區分：

#### 1. 🔴 原始提問 (The User's Attempt)

- **樣式**: 
  - 淡紅色或灰色背景
  - 字體略小
- **標籤**: `Original Prompt`
- **內容**: 使用者原本輸入的內容
- **視覺暗示**: 
  - 加上一個 "跨掉" 的圖標或 "X" 號
  - 或者標示出問題點（例如高亮模糊的詞彙）

#### 2. 🧐 AI 診斷 (The Critique)

- **樣式**: 黃色便利貼風格
- **內容**: Agent 對這個 Prompt 的簡短評語
- **範例**: 
  - 「指令過於模糊，導致 AI 產生幻覺」
  - 「缺乏角色設定」

#### 3. 🟢 優化建議 (The Better Candidates)

- **樣式**: 鮮明的綠色或強調色邊框，這是卡片的重點
- **UI 元素**: 這是一個 Tab 切換或輪播 (Carousel)，提供 3 個選項：
  - **Tab 1**: 結構化版 (Structured)
  - **Tab 2**: 角色扮演版 (Role-Play)
  - **Tab 3**: 思維鏈版 (Chain-of-Thought)
- **內容**: 完整的優化 Prompt

#### 4. 🚀 預期效果 (Why it works)

- **樣式**: 底部的小字註解
- **內容**: 解釋為什麼用這個 Prompt 會得到左側那樣高品質的內容

### 視覺設計原則

- **對比視圖 (Diff View)**: 卡片設計成「對比視圖」的變體，清楚展示原始與優化的差異
- **顏色功能性**: 由於資訊密度高，顏色功能性要強
- **字體區分**: 
  - 文章內容：Serif 字體（襯線體）
  - 系統/Prompt 區域：Monospace 字體（等寬字體，如 Fira Code, Roboto Mono）

---

## 3. 互動體驗 (Micro-Interactions)

### Copy to Clipboard (一鍵複製)

- **位置**: 在「優化建議」的 Prompt 旁邊
- **功能**: 讓讀者覺得：「哇，這句好用，我要存起來下次用。」
- **實作**: 使用 Clipboard API

### Diff Highlighter (差異高亮)

- **功能**: 用顏色標記出「優化版」比「原始版」多出了哪些關鍵字
- **範例**: 高亮 `step-by-step`, `in JSON format` 等關鍵字
- **實作**: 使用文字比對演算法標記差異

### "Run Simulation" (模擬運行 - 進階)

- **位置**: 在優化建議卡片中
- **功能**: 點擊後，彈出一個 Modal，顯示如果用這個優化後的 Prompt，AI 實際會吐出什麼原始 Raw Data
- **價值**: 直接證明優化效果
- **實作**: 需要額外的 API 端點來執行模擬

---

## 4. 配色與視覺引導 (Color System)

### 情緒色系統

- **❌ Red/Pink**: 原始 Prompt 的弱點
- **✅ Green/Teal**: 優化 Prompt 的亮點
- **💡 Yellow/Amber**: 診斷與洞察

### 字體系統

- **文章內容 (Main Content)**: 
  - 黑字白底（或深色模式）
  - Serif 字體（襯線體）增加沉浸感
- **系統/Prompt 區域 (Meta Info)**: 
  - Monospace 字體（等寬字體，如 Fira Code, Roboto Mono）
  - 讓讀者一眼識別這是「程式碼/指令」相關的內容

### 深色模式支援

- 必須支援深色模式
- 顏色系統在深色模式下保持對比度與可讀性

---

## 5. 原型示意 (Wireframe Concept)

### Desktop 版面

```
+-------------------------------------------------------+  +-------------------------------------+
|  Main Blog Article (70%)                              |  |  Prompt Engineer Sidebar (30%)      |
|                                                       |  |  (Sticky / Follows Scroll)          |
|  ## 1. 為什麼選擇非同步爬蟲？                         |  +-------------------------------------+
|                                                       |  |                                     |
|  在處理大量數據時，同步爬蟲會因為 I/O 阻塞...         |  |  [CARD] 對應左側第一章節            |
|  (這是 Agent 根據對話生成的精華內容)                  |  |                                     |
|  ...                                                  |  |  🔴 Original User Prompt:           |
|  ...                                                  |  |  "寫個爬蟲程式。"                   |
|  [⚓] <--- 滑鼠移到這裡高亮右側卡片                   |  |                                     |
|                                                       |  |  🧐 Diagnosis:                      |
|                                                       |  |  缺乏語言、目標網站與並發要求。     |
|  ## 2. 實作 asyncio 的關鍵程式碼                      |  |                                     |
|                                                       |  |  🟢 Recommended Candidate:          |
|  以下是使用 Python aiohttp 的範例...                  |  |  "你是一名 Python 專家。請使用      |
|  ...                                                  |  |  asyncio 寫一個高併發爬蟲，         |
|                                                       |  |  目標是抓取 100 個頁面..."          |
|                                                       |  |  [Copy Button]                      |
|                                                       |  +-------------------------------------+
+-------------------------------------------------------+
```

### Mobile 版面

```
+-----------------------------------+
|  Main Blog Article (100%)         |
|                                   |
|  ## 1. 為什麼選擇非同步爬蟲？     |
|                                   |
|  在處理大量數據時，同步爬蟲...    |
|  ...                              |
|                                   |
|  [💡 查看此段落的 Prompt 技巧]    |
|  ┌─────────────────────────────┐  |
|  │ [展開的 Prompt 卡片]        │  |
|  │ 🔴 Original: "寫個爬蟲..."  │  |
|  │ 🧐 Diagnosis: ...           │  |
|  │ 🟢 Candidates: ...          │  |
|  └─────────────────────────────┘  |
|                                   |
|  ## 2. 實作 asyncio...            |
|  ...                              |
+-----------------------------------+
```

---

## 6. 技術實作細節 (Frontend Implementation)

### 資料結構

前端收到的 JSON 應該包含 `content_blocks` 陣列。每個 block 都有：

```typescript
interface ContentBlock {
  id: string;
  text: string;              // 文章內容
  prompt_meta?: {           // 對應的優化建議（可選）
    original_prompt: string;
    analysis: string;
    better_candidates: Array<{
      type: 'structured' | 'role-play' | 'chain-of-thought';
      prompt: string;
      reasoning: string;
    }>;
    expected_effect: string;
  };
}
```

### 關鍵技術

1. **Intersection Observer API**: 
   - 偵測使用者目前「讀到哪一段」
   - 自動切換右側 Sidebar 的 active 狀態
   - 實作平滑的滾動追蹤

2. **Sticky Sidebar**: 
   - 使用 CSS `position: sticky` 或 JavaScript 實作
   - 確保在滾動時保持可見

3. **Tab/Carousel 切換**: 
   - 使用 shadcn/ui 的 Tabs 組件
   - 或自訂 Carousel 組件

4. **Accordion (Mobile)**: 
   - 使用 shadcn/ui 的 Accordion 組件
   - 支援平滑展開/收合動畫

### 前端框架建議

- **Next.js 14+**: 使用 App Router
- **shadcn/ui**: 提供基礎組件（Tabs, Accordion, Button 等）
- **TailwindCSS**: 樣式管理
- **React Intersection Observer**: 簡化 Intersection Observer 的使用

---

## 7. 響應式設計斷點 (Responsive Breakpoints)

- **Desktop**: ≥ 1024px (70/30 雙欄)
- **Tablet**: 768px - 1023px (可選：60/40 或切換為單欄)
- **Mobile**: < 768px (單欄，行內展開)

---

## 8. 無障礙設計 (Accessibility)

- **鍵盤導航**: 所有互動元素必須支援鍵盤操作
- **螢幕閱讀器**: 使用適當的 ARIA 標籤
- **對比度**: 符合 WCAG AA 標準（至少 4.5:1）
- **焦點指示**: 清楚的焦點狀態

---

## 9. 效能考量 (Performance)

- **圖片優化**: 使用 Next.js Image 組件
- **程式碼分割**: 使用 React.lazy 或 Next.js 動態導入
- **虛擬滾動**: 如果文章很長，考慮使用虛擬滾動
- **Intersection Observer**: 使用節流（throttle）或防抖（debounce）優化

---

## 10. 實作優先級

### Phase 1: 基礎佈局 (P1)

- [ ] Desktop 70/30 雙欄佈局
- [ ] Sticky Sidebar 實作
- [ ] 基礎 Prompt 卡片組件
- [ ] 文章內容渲染（Markdown）

### Phase 2: 互動功能 (P1)

- [ ] Intersection Observer 整合
- [ ] 滾動追蹤與自動切換
- [ ] 錨點圖標與高亮效果
- [ ] Copy to Clipboard 功能

### Phase 3: Mobile 適配 (P2)

- [ ] Accordion 模式實作
- [ ] 響應式斷點調整
- [ ] 觸控優化

### Phase 4: 進階功能 (P3)

- [ ] Diff Highlighter
- [ ] Run Simulation (需要後端支援)
- [ ] 深色模式
- [ ] 動畫與過渡效果

---

## 11. 設計參考

### 類似設計模式

- **GitHub Diff View**: 對比視圖的參考
- **Medium 註解系統**: 行內展開的參考
- **Notion Sidebar**: Sticky sidebar 的參考

### 設計工具建議

- **Figma**: 設計稿與原型
- **Storybook**: 組件開發與測試

---

## 12. 測試考量

### 視覺回歸測試

- 使用 Chromatic 或 Percy 進行視覺回歸測試
- 確保不同斷點下的佈局正確

### 互動測試

- 使用 React Testing Library 測試互動邏輯
- 測試 Intersection Observer 的行為
- 測試 Copy to Clipboard 功能

### 無障礙測試

- 使用 axe-core 進行無障礙測試
- 鍵盤導航測試
- 螢幕閱讀器測試

---

## 總結

這個設計能完美達成需求：既展示了知識，又展示了如何獲取知識的技術，非常有價值。透過 Side-by-Side 的呈現方式，讀者可以同時學習內容與 Prompt Engineering 技巧，提供獨特的元學習體驗。

