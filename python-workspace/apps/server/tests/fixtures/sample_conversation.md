---
title: "Google Gemini"
platform: Gemini
url: https://gemini.google.com/u/1/app/463f3760401337a7?hl=zh-TW
exported: 2025-12-08T10:49:42.094Z
---

# Google Gemini

## 使用者

```python

"""Content extension workflow step for research and knowledge gap filling."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from llama_index.core.workflow import Event, step

if TYPE_CHECKING:

    from blog_agent.workflows.extractor import ExtractEvent

from blog_agent.services.llm_service import get_llm_service

from blog_agent.services.tavily_service import get_tavily_service

from blog_agent.services.vector_store import VectorStore

from blog_agent.storage.models import ContentExtract

from blog_agent.utils.errors import ExternalServiceError

from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)

class ExtendEvent(Event):

    """Event containing extended content."""

    content_extract: ContentExtract  # Updated with extended content

    conversation_log_id: str

    conversation_log_metadata: Optional[Dict[str, Any]] = None

    research_results: List[Dict[str, Any]] = []  # Research results from Tavily/KB

    knowledge_gaps: List[Dict[str, Any]] = []  # Identified knowledge gaps

class ContentExtender:

    """Content extension step for identifying gaps and researching additional information."""

    def __init__(

        self,

        llm_service=None,

        tavily_service=None,

        vector_store: Optional[VectorStore] = None,

    ):

        """Initialize content extender."""

        self.llm_service = llm_service or get_llm_service()

        self.tavily_service = tavily_service or get_tavily_service()

        self.vector_store = vector_store or VectorStore()

    @step

    async def extend(self, ev: "ExtractEvent") -> ExtendEvent:  # type: ignore

        """

        Extend content by identifying knowledge gaps and researching additional information.



        Steps:

        1. Identify knowledge gaps in the content

        2. Query knowledge base first (if available) (FR-018, T069)

        3. Use Tavily search for gaps not covered by KB (T066)

        4. Integrate research results naturally into content (T067)

        """

        try:

            content_extract = ev.content_extract

            conversation_log_id = ev.conversation_log_id

            # Step 1: Identify knowledge gaps (T065)

            knowledge_gaps = await self._identify_knowledge_gaps(content_extract)

            logger.info("Identified knowledge gaps", count=len(knowledge_gaps))

            if not knowledge_gaps:

                # No gaps found, return original content

                return ExtendEvent(

                    content_extract=content_extract,

                    conversation_log_id=conversation_log_id,

                    conversation_log_metadata=ev.conversation_log_metadata or {},

                    research_results=[],

                    knowledge_gaps=[],

                )

            # Step 2 & 3: Research gaps (KB first, then Tavily) (T069)

            research_results = await self._research_gaps(knowledge_gaps)

            # Step 4: Integrate research into content (T067)

            extended_content = await self._integrate_research(

                content_extract, knowledge_gaps, research_results

            )

            # Update content extract with extended content

            extended_extract = ContentExtract(

                id=content_extract.id,

                conversation_log_id=content_extract.conversation_log_id,

                key_insights=content_extract.key_insights,

                core_concepts=content_extract.core_concepts,

                filtered_content=extended_content,

            )

            return ExtendEvent(

                content_extract=extended_extract,

                conversation_log_id=conversation_log_id,

                conversation_log_metadata=ev.conversation_log_metadata or {},

                research_results=research_results,

                knowledge_gaps=knowledge_gaps,

            )

        except ExternalServiceError:

            # Re-raise external service errors (FR-019)

            raise

        except Exception as e:

            logger.error("Content extension failed", error=str(e), exc_info=True)

            raise

    async def _identify_knowledge_gaps(

        self, content_extract: ContentExtract

    ) -> List[Dict[str, Any]]:

        """

        Identify areas in content that lack sufficient context or detail (T065).



        Returns:

            List of knowledge gaps, each with:

            - type: Type of gap (e.g., "missing_context", "unclear_concept", "missing_background")

            - description: Description of the gap

            - location: Where in the content the gap appears

            - query: Search query to find information about this gap

        """

        prompt = f"""請分析以下內容，找出缺少足夠上下文或細節的區域。

核心觀點：

{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

核心概念：

{', '.join(content_extract.core_concepts)}

內容：

{content_extract.filtered_content}

請找出以下類型的知識缺口：

1. 缺少必要的背景知識

2. 概念或術語未充分解釋

3. 缺少相關的技術細節

4. 缺少實際範例或應用場景

5. 缺少相關的歷史或發展脈絡

請以 JSON 格式輸出，格式如下：

{{

  "gaps": [

    {{

      "type": "類型（如：missing_context、unclear_concept等）",

      "description": "缺口描述",

      "location": "在內容中的位置或相關段落",

      "query": "用於搜尋相關資訊的查詢字串",

      "priority": "優先級（high/medium/low）"

    }}

  ]

}}

只輸出 JSON，不要額外說明。"""

        try:

            response = await self.llm_service.generate_structured(

                prompt,

                output_schema={

                    "type": "object",

                    "properties": {

                        "gaps": {

                            "type": "array",

                            "items": {

                                "type": "object",

                                "properties": {

                                    "type": {"type": "string"},

                                    "description": {"type": "string"},

                                    "location": {"type": "string"},

                                    "query": {"type": "string"},

                                    "priority": {"type": "string"},

                                },

                                "required": ["type", "description", "location", "query", "priority"],

                            },

                        }

                    },

                    "required": ["gaps"],

                },

            )

            gaps = response.get("gaps", [])

            logger.info("Identified knowledge gaps", count=len(gaps))

            return gaps

        except Exception as e:

            logger.warning("Failed to identify knowledge gaps", error=str(e))

            return []

    async def _research_gaps(

        self, knowledge_gaps: List[Dict[str, Any]]

    ) -> List[Dict[str, Any]]:

        """

        Research knowledge gaps using KB first, then Tavily (T066, T069).



        Args:

            knowledge_gaps: List of identified knowledge gaps



        Returns:

            List of research results, each with:

            - gap: The original gap information

            - source: "knowledge_base" or "tavily"

            - results: Research results from the source

        """

        research_results = []

        for gap in knowledge_gaps:

            query = gap.get("query", "")

            if not query:

                continue

            gap_results = {

                "gap": gap,

                "source": None,

                "results": [],

            }

            # Step 1: Try knowledge base first (T069, FR-018)

            kb_results = await self._query_knowledge_base(query)

            if kb_results:

                gap_results["source"] = "knowledge_base"

                gap_results["results"] = kb_results

                logger.info(

                    "Found KB results for gap",

                    query=query,

                    results_count=len(kb_results),

                )

            else:

                # Step 2: Use Tavily if KB has no results (T066)

                try:

                    tavily_results = await self.tavily_service.search(

                        query=query,

                        max_results=3,  # Limit results per gap

                        search_depth="advanced",

                    )

                    if tavily_results:

                        gap_results["source"] = "tavily"

                        gap_results["results"] = tavily_results

                        logger.info(

                            "Found Tavily results for gap",

                            query=query,

                            results_count=len(tavily_results),

                        )

                except ExternalServiceError as e:

                    # Tavily failure should stop processing (FR-019)

                    logger.error("Tavily search failed during gap research", query=query, error=str(e))

                    raise

            if gap_results["results"]:

                research_results.append(gap_results)

        return research_results

    async def _query_knowledge_base(self, query: str) -> List[Dict[str, Any]]:

        """

        Query personal knowledge base if available (T068, FR-018).



        Args:

            query: Search query



        Returns:

            List of knowledge base results, empty if KB not available or no results

        """

        try:

            # For now, we need to generate an embedding for the query

            # In a full implementation, we'd use an embedding service (e.g., OpenAI embeddings)

            # For now, return empty list (KB integration is optional, FR-018)

            # TODO: Implement embedding generation and KB query when KB is available

            # Example: query_embedding = await embedding_service.generate_embedding(query)

            #          return await self.vector_store.query_knowledge_base(query, query_embedding)

            logger.debug("Knowledge base query attempted", query=query)

            return []

        except Exception as e:

            logger.warning("Knowledge base query failed", query=query, error=str(e))

            return []

    async def _integrate_research(

        self,

        content_extract: ContentExtract,

        knowledge_gaps: List[Dict[str, Any]],

        research_results: List[Dict[str, Any]],

    ) -> str:

        """

        Integrate research results naturally into content (T067).



        Args:

            content_extract: Original content extract

            knowledge_gaps: Identified knowledge gaps

            research_results: Research results from KB/Tavily



        Returns:

            Extended content with research integrated naturally

        """

        if not research_results:

            # No research to integrate, return original content

            return content_extract.filtered_content

        # Build research context for LLM

        research_context = "\n\n研究補充資訊：\n"

        for result in research_results:

            gap = result["gap"]

            source = result["source"]

            results = result["results"]

            research_context += f"\n缺口：{gap.get('description', '')}\n"

            research_context += f"來源：{source}\n"

            if source == "tavily":

                for r in results[:2]:  # Use top 2 results per gap

                    research_context += f"- {r.get('title', '')}: {r.get('content', '')[:200]}...\n"

                    research_context += f"  來源：{r.get('url', '')}\n"

            elif source == "knowledge_base":

                for r in results[:2]:

                    research_context += f"- {r.get('content', '')[:200]}...\n"

        prompt = f"""請將以下研究補充資訊自然地整合到原始內容中。

原始內容：

{content_extract.filtered_content}

{research_context}

要求：

1. 保持原始內容的結構和風格

2. 自然地將補充資訊融入相關段落

3. 不要重複已有的資訊

4. 使用 Markdown 格式

5. 在適當的地方添加引用或說明來源

6. 確保整合後的內容流暢連貫

請直接輸出整合後的完整內容，不要額外說明。"""

        try:

            extended_content = await self.llm_service.generate(prompt)

            logger.info("Research integrated into content", original_length=len(content_extract.filtered_content), extended_length=len(extended_content))

            return extended_content.strip()

        except Exception as e:

            logger.warning("Failed to integrate research", error=str(e))

            # Return original content if integration fails

            return content_extract.filtered_content

```

我是 llama index 新手，但是以前有寫過一段時間 RAG（手動 vector store + prompt)，上面的程式碼是我參考某個專案的，為什麼我感覺像是比較複雜的組 prompt 和上下文補充

## Gemini

這是一個非常敏銳的觀察！你的感覺完全正確：**這段程式碼本質上就是「進階的 Prompt Engineering」加上「流程控制（Orchestration）」**。

既然你有手刻 RAG 的經驗，你可能習慣的是「Traditional RAG」（或是 Naive RAG），也就是 `Query -> Embedding -> Vector Search -> Context Stuffing -> LLM Answer` 的一條龍直線流程。

但你現在看到的這段程式碼，屬於 LlamaIndex 較新的 **`Workflows` (Agentic RAG)** 範疇。

讓我幫你拆解一下，為什麼它會給你這種感覺，以及這樣做的目的是什麼。

### 1. 為什麼這看起來不像傳統 RAG？

傳統 RAG 通常關注的是**「如何檢索（Retrieval）」**，而這段程式碼關注的是**「如何思考與決策（Reasoning & Flow）」**。

- 傳統 RAG (Retrieve-then-Generate): 使用者問問題 -> 系統直接去資料庫找相關文件 -> 丟給 LLM 回答。
- 缺點： 系統很盲目。如果使用者問的問題資料庫裡沒有，或者問題需要推理（例如：「這篇文章缺了什麼？」），傳統 RAG 做不到。

**這段程式碼 (Agentic Workflow):**

- 它是 多步驟的 ，而且包含 自我反思（Self-Reflection） 。
- 它不是直接回答問題，而是先「讀」文章，然後「想」哪裡有缺口，再去「查」資料，最後「寫」進去。

### 2. 這段程式碼的三個核心動作（其實就是 Prompt Engineering）

你感覺到的「複雜的組 Prompt」，其實是因為這裡用了 **Flow Engineering（流程工程）** 的概念。開發者不相信 LLM 能一次把事情做對，所以拆成三個明確的 Prompt 步驟：

1. 自我反思 ( _identify_knowledge_gaps )： - 動作： 這裡沒有做任何檢索。它純粹是把文章丟給 LLM，用 Prompt 問：「你覺得這篇文章缺了什麼背景知識？」。 - 你的感覺： 對，這就是 Context Stuffing（把文章塞進去）+ Prompting。
2. 工具使用與路由 ( _research_gaps )： - 動作： 根據上一步找出的「缺口」，決定要去哪裡找資料。 - 邏輯： 先查 Knowledge Base (KB)，沒有的話再查 Tavily (Web Search)。 - 差異： 傳統 RAG 通常只查 Vector DB。這裡加入了一個 Python 邏輯層來決定「查什麼」和「去哪查」。
3. 資訊整合 ( _integrate_research )： - 動作： 把查到的新資料（Research Results）和原文（Content）再次塞進 Prompt。 - Prompt： 「請把這些新資料自然地寫進原文裡」。 - 你的感覺： 這又是 Context Stuffing。

### 3. 那為什麼要用 LlamaIndex 的 `Workflow`？

既然都是寫 Python 邏輯和組 Prompt，為什麼不直接寫個 script 就好？為什麼要繼承 `Event` 和 `step`？

LlamaIndex Workflows 在這裡提供的價值是**「架構（Scaffolding）」**：

1. 事件驅動 (Event-Driven)： - 你可以看到 async def extend(self, ev: "ExtractEvent") 。這意味著這個步驟是鬆散耦合的。如果未來你想在「找出缺口」和「搜尋」中間插一個「人工審核」步驟，你只需要攔截 Event，不需要重寫整個大函式。
2. 狀態管理： - 它幫你管理了 ExtendEvent 這個物件在不同步驟間的傳遞，你不需要自己維護一堆全域變數或複雜的參數傳遞。
3. 異步處理與容錯： - 在 _research_gaps 這種涉及外部 API (Tavily) 的地方，Workflow 架構通常能更好地處理併發（Concurrency）和錯誤重試。

### 總結：你的直覺是對的

這段程式碼展示了 RAG 的演進方向：**從「檢索增強（Retrieval Augmented）」轉向「代理工作流（Agentic Workflow）」**。

- 過去 (Naive RAG): 重點在於 Vector DB 的切塊 (Chunking) 和搜尋演算法。
- 現在 (Agentic RAG): 重點在於 Prompt 的串接邏輯、讓 LLM 檢視自己的輸出（找出缺口），以及動態決定何時該搜尋。

**給手刻 RAG 老手的建議：**
不要把這看作是 Retrieval 程式碼，把它看作是一個**狀態機（State Machine）**。這段程式碼的核心不在於 `vector_store`（那部分在程式碼裡甚至還沒實作完），而在於它如何透過 Prompt 引導 LLM 像人類研究員一樣工作：**閱讀 -> 發現問題 -> 搜尋 -> 寫作**。

**Next Step:**
如果你想體驗這種 Workflow 的威力，建議你試著把 `_query_knowledge_base` 裡面的 `# TODO` 實作出來（接上你熟悉的 Vector Search）。你會發現，有了前面的「缺口分析 (Gap Analysis)」步驟，你的搜尋 query 會比直接拿使用者的問題去搜精準得多。

## 使用者

self.llm_service 其實只是 openai api wrapper, llama index 可以取代這件事嗎？還是說現在這個作法就好了

## Gemini

這是一個非常好的架構設計問題。

簡單的回答是：**是的，LlamaIndex 完全可以（而且建議）取代這個 wrapper。**

其實你現在看到的寫法，是一種「半路出家」的狀態：使用了 LlamaIndex 的 `Workflow` 架構來控流程，但核心的 LLM 呼叫卻還是用自己手刻的 Wrapper。

若改用 LlamaIndex 原生的 LLM 介面，會有以下幾個巨大的優勢，特別是在你處理 `_identify_knowledge_gaps` 這種需要「結構化輸出（Structured Output）」的場景。

以下我將對比 **「目前的作法」** 與 **「LlamaIndex 原生作法」** 的差異：

---

### 1. 處理結構化輸出 (最大的差異)

你目前的程式碼在 `_identify_knowledge_gaps` 裡做了兩件辛苦的事：

1. Prompt Engineering: 在 Prompt 裡手寫 JSON Schema ( output_schema=... )，並要求 LLM「只輸出 JSON」。
2. Parsing: 你拿到字串後，雖然沒顯示出來，但在 llm_service 內部一定有一個 json.loads() 的動作，而且通常還要處理 LLM 沒吐乾淨 Markdown code block 的例外狀況。

**LlamaIndex Native (`structured_predict`) 的作法：**
LlamaIndex 深度整合了 **Pydantic**。你只需要定義 Python Class，它會自動幫你生成 Prompt 的 schema 部分，並自動幫你把回傳結果轉成 Python 物件（不僅僅是 Dict）。

Python
**

```
from pydantic import BaseModel, Field
from typing import List
from llama_index.core.llms import LLM

# 1. 定義你的資料結構 (Pydantic)
class KnowledgeGap(BaseModel):
    type: str = Field(..., description="缺口類型，如 missing_context")
    description: str = Field(..., description="缺口描述")
    location: str
    query: str
    priority: str

class KnowledgeGapResponse(BaseModel):
    gaps: List[KnowledgeGap]

# 2. 在你的類別中直接使用
class ContentExtender:
    def __init__(self, llm: LLM = None, ...):
        # LlamaIndex 會自動從 Settings 抓，或你可以傳入特定的 LLM
        self.llm = llm or Settings.llm

    async def _identify_knowledge_gaps(self, content_extract) -> List[dict]:
        prompt_template = "分析以下內容並找出缺口: {content} ..."

        # --- 魔法發生在這裡 ---
        # LlamaIndex 會自動處理 Function Calling / JSON Mode
        # 並且直接回傳 KnowledgeGapResponse 物件
        response = await self.llm.structured_predict(
            KnowledgeGapResponse,
            prompt_template,
            content=content_extract.filtered_content
        )

        # 這裡的 response.gaps 已經是乾淨的 List[KnowledgeGap] 物件了
        return [gap.model_dump() for gap in response.gaps]
```

優點：** 程式碼變乾淨，不用在 Prompt 裡手寫 JSON 格式，且型別檢查（Type Checking）更安全。

### 2. 模型的抽換性 (Model Agnostic)

- 目前的作法： 你的 llm_service 是一個 OpenAI wrapper。如果你老闆明天說：「嘿，為了省錢/隱私，我們把這部分換成 Claude 3.5 Sonnet 或是本地跑 Llama 3」，你得去重寫那個 wrapper。
- LlamaIndex 作法： 你只需要在初始化時換一行設定：

Python
**

```
# 切換模型完全不需要改動 ContentExtender 的程式碼
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.ollama import Ollama

# 換成 Claude
llm = Anthropic(model="claude-3-5-sonnet")
# 或是換成 Local Llama3
llm = Ollama(model="llama3")

extender = ContentExtender(llm=llm)
```

LlamaIndex 幫你平整化了不同 API 之間的差異（例如 OpenAI 叫 `messages`，Anthropic 格式略有不同），統一用 `chat`, `complete`, `structured_predict` 呼叫。

### 3. Observability (可觀測性) 與 Callbacks

這在 Agentic Workflow 中至關重要。

- 目前的作法： 你只能看到 logger.info 印出來的東西。如果你想知道這一步用了多少 Token？花費多少錢？Prompt 實際長什麼樣？你必須自己在 wrapper 裡埋點。
- LlamaIndex 作法： LlamaIndex 有全域的 Callback 系統。如果你用了原生的 LLM 物件，你可以直接整合 Arize Phoenix 或 LangSmith 。

當你執行 Workflow 時，你會看到一個漂亮的 Dashboard，顯示：
`Start Event` -> `LLM Call (Identify Gaps)` -> `Function Call` -> `End Event`。
每一層的 Latency、Token usage 都清清楚楚。如果你用自己的 wrapper，LlamaIndex 的追蹤工具就會「斷片」，看不到 wrapper 內部發生什麼事。

### 結論：該保留還是替換？

建議：替換掉。**

目前的寫法有點「為了用 LlamaIndex 而用 LlamaIndex」。你只用了它的殼（Event/Workflow），卻丟棄了它最強大的肌肉（LLM 抽象層與結構化輸出）。

**什麼時候才需要保留你的 wrapper？**
除非你的 wrapper 做了非常特殊的**非標準邏輯**，例如：

1. 特殊的企業內部權限認證（非標準 Bearer token）。
2. 非常複雜的 Rate Limiter 或 Cost Router（比如動態根據當下負載切換 Azure/OpenAI）。
3. 你有很重的 Legacy code 依賴這個 service。

如果沒有上述情況，直接使用 LlamaIndex 的 `Settings.llm` 或 `OpenAI` 類別，並配合 Pydantic 做結構化輸出，會讓你的程式碼更 Pythonic 且更易於維護。

### Next Step

你可以嘗試先改寫 `_identify_knowledge_gaps` 函式。不要手寫 JSON prompt，試著定義一個 `Pydantic` model，然後用 `await self.llm.structured_predict(MyModel, prompt)` 跑跑看，你會發現世界變得清爽很多。
