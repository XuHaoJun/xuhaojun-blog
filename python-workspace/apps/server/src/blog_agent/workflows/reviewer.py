"""Content review workflow step for quality enhancement."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID, uuid4

from llama_index.core.workflow import Event, step

if TYPE_CHECKING:
    from blog_agent.workflows.extractor import ExtractEvent

from blog_agent.services.llm_service import get_llm_service
from blog_agent.storage.models import ContentExtract, ReviewFindings
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class ReviewEvent(Event):
    """Event containing review findings."""

    review_findings: ReviewFindings
    content_extract: ContentExtract
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None
    errors: List[str] = []  # Issues that cannot be auto-corrected (T062)


class ContentReviewer:
    """Content review step for identifying issues and suggesting improvements."""

    def __init__(self, llm_service=None):
        """Initialize content reviewer."""
        self.llm_service = llm_service or get_llm_service()

    @step
    async def review(self, ev: "ExtractEvent") -> ReviewEvent:  # type: ignore
        """Review extracted content for errors, inconsistencies, and unclear explanations."""
        try:
            content_extract = ev.content_extract
            conversation_log_id = ev.conversation_log_id

            # Perform comprehensive review
            logical_gaps = await self._detect_logical_gaps(content_extract)
            factual_inconsistencies = await self._detect_factual_inconsistencies(content_extract)
            unclear_explanations = await self._detect_unclear_explanations(content_extract)
            fact_checking_needs = await self._detect_fact_checking_needs(content_extract)  # FR-010

            # Combine all issues
            issues = {
                "logical_gaps": logical_gaps,
                "factual_inconsistencies": factual_inconsistencies,
                "unclear_explanations": unclear_explanations,
            }

            # Generate improvement suggestions
            improvement_suggestions = await self._generate_improvement_suggestions(
                content_extract, issues
            )

            # Identify errors that cannot be auto-corrected (T062)
            errors = await self._identify_uncorrectable_errors(issues, fact_checking_needs)

            # Ensure content_extract_id is a valid UUID
            # Note: content_extract.id should be set when ContentExtract is saved to DB
            # If not set, we use a temporary UUID that will need to be updated
            content_extract_id: UUID
            if content_extract.id:
                content_extract_id = content_extract.id
            else:
                # Generate temporary UUID - this should be updated when ContentExtract is saved
                # TODO: Ensure ContentExtract is saved before review step
                content_extract_id = uuid4()
                logger.warning(
                    "ContentExtract ID not set, using temporary UUID",
                    temp_id=str(content_extract_id),
                )

            review_findings = ReviewFindings(
                content_extract_id=content_extract_id,
                issues=issues,
                improvement_suggestions=improvement_suggestions,
                fact_checking_needs=fact_checking_needs,
            )

            return ReviewEvent(
                review_findings=review_findings,
                content_extract=content_extract,
                conversation_log_id=conversation_log_id,
                conversation_log_metadata=ev.conversation_log_metadata or {},
                errors=errors,
            )

        except Exception as e:
            logger.error("Content review failed", error=str(e), exc_info=True)
            raise

    async def _detect_logical_gaps(self, content_extract: ContentExtract) -> List[Dict[str, Any]]:
        """Detect logical gaps in the content (T055)."""
        prompt = f"""請分析以下內容，找出邏輯上的斷層或缺失。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

核心概念：
{', '.join(content_extract.core_concepts)}

內容：
{content_extract.filtered_content}

請找出以下類型的邏輯問題：
1. 概念之間的跳躍（缺少中間步驟）
2. 論證鏈中的斷層
3. 前提假設未明確說明
4. 結論與前提不一致

請以 JSON 格式輸出，格式如下：
{{
  "gaps": [
    {{
      "type": "類型（如：概念跳躍、論證斷層等）",
      "description": "問題描述",
      "location": "在內容中的位置或相關段落",
      "severity": "嚴重程度（high/medium/low）"
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
                                    "severity": {"type": "string"},
                                },
                                "required": ["type", "description", "location", "severity"],
                            },
                        }
                    },
                    "required": ["gaps"],
                },
            )

            gaps = response.get("gaps", [])
            logger.info("Detected logical gaps", count=len(gaps))
            return gaps

        except Exception as e:
            logger.warning("Failed to detect logical gaps", error=str(e))
            return []

    async def _detect_factual_inconsistencies(
        self, content_extract: ContentExtract
    ) -> List[Dict[str, Any]]:
        """Detect factual inconsistencies in the content (T056)."""
        prompt = f"""請分析以下內容，找出事實上的不一致或矛盾。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

核心概念：
{', '.join(content_extract.core_concepts)}

內容：
{content_extract.filtered_content}

請找出以下類型的事實問題：
1. 前後矛盾的陳述
2. 與已知事實不符的聲稱
3. 數據或統計資料的不一致
4. 時間線或因果關係的矛盾

請以 JSON 格式輸出，格式如下：
{{
  "inconsistencies": [
    {{
      "type": "類型（如：前後矛盾、事實不符等）",
      "description": "問題描述",
      "claim1": "第一個矛盾的聲稱",
      "claim2": "與之矛盾的聲稱",
      "severity": "嚴重程度（high/medium/low）"
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
                        "inconsistencies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "claim1": {"type": "string"},
                                    "claim2": {"type": "string"},
                                    "severity": {"type": "string"},
                                },
                                "required": ["type", "description", "claim1", "claim2", "severity"],
                            },
                        }
                    },
                    "required": ["inconsistencies"],
                },
            )

            inconsistencies = response.get("inconsistencies", [])
            logger.info("Detected factual inconsistencies", count=len(inconsistencies))
            return inconsistencies

        except Exception as e:
            logger.warning("Failed to detect factual inconsistencies", error=str(e))
            return []

    async def _detect_unclear_explanations(
        self, content_extract: ContentExtract
    ) -> List[Dict[str, Any]]:
        """Detect unclear explanations in the content (T057)."""
        prompt = f"""請分析以下內容，找出不清楚或需要澄清的解釋。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

核心概念：
{', '.join(content_extract.core_concepts)}

內容：
{content_extract.filtered_content}

請找出以下類型的不清楚之處：
1. 術語未定義或解釋不清
2. 步驟說明不夠詳細
3. 概念解釋過於抽象
4. 缺少必要的背景知識
5. 範例或類比不夠清楚

請以 JSON 格式輸出，格式如下：
{{
  "unclear_points": [
    {{
      "type": "類型（如：術語未定義、步驟不清等）",
      "description": "問題描述",
      "location": "在內容中的位置或相關段落",
      "suggestion": "如何改進的建議",
      "severity": "嚴重程度（high/medium/low）"
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
                        "unclear_points": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "location": {"type": "string"},
                                    "suggestion": {"type": "string"},
                                    "severity": {"type": "string"},
                                },
                                "required": ["type", "description", "location", "suggestion", "severity"],
                            },
                        }
                    },
                    "required": ["unclear_points"],
                },
            )

            unclear_points = response.get("unclear_points", [])
            logger.info("Detected unclear explanations", count=len(unclear_points))
            return unclear_points

        except Exception as e:
            logger.warning("Failed to detect unclear explanations", error=str(e))
            return []

    async def _detect_fact_checking_needs(
        self, content_extract: ContentExtract
    ) -> List[str]:
        """Detect claims that need fact-checking (FR-010, T060)."""
        prompt = f"""請分析以下內容，找出需要事實查核的聲稱。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

內容：
{content_extract.filtered_content}

請找出以下類型的聲稱，這些需要外部驗證：
1. 具體的數據或統計資料
2. 歷史事件或日期
3. 科學事實或研究結果
4. 技術規格或標準
5. 其他可驗證的事實聲稱

請以列表形式輸出，每個需要查核的聲稱一行。只輸出聲稱內容，不要額外說明。"""

        try:
            response = await self.llm_service.generate(prompt)

            # Parse response into list
            claims = [
                line.strip()
                for line in response.split("\n")
                if line.strip()
                and not line.strip().startswith("#")
                and len(line.strip()) > 10  # Filter out very short lines
            ]

            logger.info("Detected fact-checking needs", count=len(claims))
            return claims[:20]  # Limit to 20 claims

        except Exception as e:
            logger.warning("Failed to detect fact-checking needs", error=str(e))
            return []

    async def _generate_improvement_suggestions(
        self, content_extract: ContentExtract, issues: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement suggestions based on identified issues."""
        prompt = f"""根據以下發現的問題，生成具體的改進建議。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

發現的問題：
邏輯斷層：{len(issues.get('logical_gaps', []))} 個
事實不一致：{len(issues.get('factual_inconsistencies', []))} 個
不清楚的解釋：{len(issues.get('unclear_explanations', []))} 個

請生成 3-5 個具體的改進建議，每個建議一行。建議應該：
1. 針對具體問題
2. 提供可行的解決方案
3. 優先處理嚴重問題

只輸出建議列表，不要額外說明。"""

        try:
            response = await self.llm_service.generate(prompt)

            # Parse response into list
            suggestions = [
                line.strip()
                for line in response.split("\n")
                if line.strip()
                and not line.strip().startswith("#")
                and (line.strip().startswith("-") or line.strip()[0].isdigit())
            ]

            # Clean up list markers
            suggestions = [
                s.lstrip("- ").lstrip("• ").lstrip("* ").strip()
                for s in suggestions
                if len(s.strip()) > 10
            ]

            logger.info("Generated improvement suggestions", count=len(suggestions))
            return suggestions[:10]  # Limit to 10 suggestions

        except Exception as e:
            logger.warning("Failed to generate improvement suggestions", error=str(e))
            return []

    async def _identify_uncorrectable_errors(
        self, issues: Dict[str, Any], fact_checking_needs: List[str]
    ) -> List[str]:
        """Identify errors that cannot be auto-corrected (T062)."""
        errors = []

        # High severity logical gaps that require human intervention
        high_severity_gaps = [
            gap.get("description", "")
            for gap in issues.get("logical_gaps", [])
            if gap.get("severity") == "high"
        ]
        if high_severity_gaps:
            errors.append(
                f"發現 {len(high_severity_gaps)} 個高嚴重性的邏輯斷層，需要人工審查"
            )

        # Factual inconsistencies that cannot be automatically resolved
        high_severity_inconsistencies = [
            inc.get("description", "")
            for inc in issues.get("factual_inconsistencies", [])
            if inc.get("severity") == "high"
        ]
        if high_severity_inconsistencies:
            errors.append(
                f"發現 {len(high_severity_inconsistencies)} 個高嚴重性的事實不一致，需要人工驗證"
            )

        # Fact-checking needs that require external verification
        if fact_checking_needs:
            errors.append(
                f"發現 {len(fact_checking_needs)} 個需要外部事實查核的聲稱，需要人工驗證"
            )

        logger.info("Identified uncorrectable errors", count=len(errors))
        return errors

