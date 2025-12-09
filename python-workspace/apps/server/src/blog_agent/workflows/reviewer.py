"""Content review workflow step for quality enhancement."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from llama_index.core.workflow import Event, step

# Try to import LLM classes - they may be in separate packages
if TYPE_CHECKING:
    from llama_index.llms.ollama import Ollama
    from llama_index.llms.openai import OpenAI
else:
    try:
        from llama_index.llms.ollama import Ollama
    except ImportError:
        try:
            from llama_index_llms_ollama import Ollama
        except ImportError:
            Ollama = None

    try:
        from llama_index.llms.openai import OpenAI
    except ImportError:
        try:
            from llama_index_llms_openai import OpenAI
        except ImportError:
            OpenAI = None

from blog_agent.services.llm import get_llm
from blog_agent.services.tavily_service import get_tavily_service
from blog_agent.storage.models import ContentExtract, PromptSuggestion, ReviewFindings
from blog_agent.utils.errors import ExternalServiceError
from blog_agent.utils.logging import get_logger
from blog_agent.workflows.extractor import ExtractEvent
from blog_agent.workflows.schemas import (
    FactCheckAnalysisResponse,
    FactualInconsistenciesResponse,
    LogicalGapsResponse,
    UnclearExplanationsResponse,
)

logger = get_logger(__name__)


class ReviewEvent(Event):
    """Event containing review findings."""

    review_findings: ReviewFindings
    content_extract: ContentExtract
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None
    errors: List[str] = []  # Issues that cannot be auto-corrected (T062)
    prompt_suggestion: Optional[PromptSuggestion] = None  # T079: Include prompt suggestion from parallel branch


# Rebuild model to resolve forward references
ReviewEvent.model_rebuild()


class ContentReviewer:
    """Content review step for identifying issues and suggesting improvements."""

    def __init__(self, llm: Optional[Union[Ollama, OpenAI]] = None, tavily_service=None):
        """Initialize content reviewer."""
        self.llm = llm or get_llm()
        self.tavily_service = tavily_service or get_tavily_service()

    @step
    async def review(self, ev: ExtractEvent) -> ReviewEvent:  # type: ignore
        """Review extracted content for errors, inconsistencies, and unclear explanations."""
        try:
            content_extract = ev.content_extract
            conversation_log_id = ev.conversation_log_id

            # Perform comprehensive review
            logical_gaps = await self._detect_logical_gaps(content_extract)
            factual_inconsistencies = await self._detect_factual_inconsistencies(content_extract)
            unclear_explanations = await self._detect_unclear_explanations(content_extract)
            fact_checking_needs = await self._detect_fact_checking_needs(content_extract)  # FR-010
            
            # Perform fact-checking via Tavily if needs detected (T072)
            fact_check_results = []
            if fact_checking_needs:
                fact_check_results = await self._fact_check_via_tavily(fact_checking_needs)
                # Store fact-check results in issues for reference
                # The original fact_checking_needs list is preserved for ReviewFindings

            # Combine all issues
            issues = {
                "logical_gaps": logical_gaps,
                "factual_inconsistencies": factual_inconsistencies,
                "unclear_explanations": unclear_explanations,
                "fact_check_results": fact_check_results,  # Store Tavily fact-check results (T072)
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
        prompt_template = """請分析以下內容，找出邏輯上的斷層或缺失。

核心觀點：
{key_insights}

核心概念：
{core_concepts}

內容：
{content}

請找出以下類型的邏輯問題：
1. 概念之間的跳躍（缺少中間步驟）
2. 論證鏈中的斷層
3. 前提假設未明確說明
4. 結論與前提不一致"""

        try:
            key_insights_str = "\n".join("- " + insight for insight in content_extract.key_insights)
            core_concepts_str = ", ".join(content_extract.core_concepts)
            
            # Format the prompt template first
            formatted_prompt = prompt_template.format(
                key_insights=key_insights_str,
                core_concepts=core_concepts_str,
                content=content_extract.filtered_content,
            )
            
            # Try to use structured_predict if available
            if hasattr(self.llm, 'structured_predict'):
                try:
                    response = await self.llm.structured_predict(
                        LogicalGapsResponse,
                        formatted_prompt,
                    )
                    gaps = [gap.model_dump() for gap in response.gaps]
                    logger.info("Detected logical gaps", count=len(gaps))
                    return gaps
                except (AttributeError, TypeError) as e:
                    logger.debug("structured_predict failed, using fallback", error=str(e))
            
            # Fallback: return empty list if structured_predict not available
            logger.warning("structured_predict not available for logical gaps detection")
            return []

        except Exception as e:
            logger.warning("Failed to detect logical gaps", error=str(e))
            return []

    async def _detect_factual_inconsistencies(
        self, content_extract: ContentExtract
    ) -> List[Dict[str, Any]]:
        """Detect factual inconsistencies in the content (T056)."""
        prompt_template = """請分析以下內容，找出事實上的不一致或矛盾。

核心觀點：
{key_insights}

核心概念：
{core_concepts}

內容：
{content}

請找出以下類型的事實問題：
1. 前後矛盾的陳述
2. 與已知事實不符的聲稱
3. 數據或統計資料的不一致
4. 時間線或因果關係的矛盾"""

        try:
            key_insights_str = "\n".join("- " + insight for insight in content_extract.key_insights)
            core_concepts_str = ", ".join(content_extract.core_concepts)
            
            # Format the prompt template first
            formatted_prompt = prompt_template.format(
                key_insights=key_insights_str,
                core_concepts=core_concepts_str,
                content=content_extract.filtered_content,
            )
            
            # Try to use structured_predict if available
            if hasattr(self.llm, 'structured_predict'):
                try:
                    response = await self.llm.structured_predict(
                        FactualInconsistenciesResponse,
                        formatted_prompt,
                    )
                    inconsistencies = [inc.model_dump() for inc in response.inconsistencies]
                    logger.info("Detected factual inconsistencies", count=len(inconsistencies))
                    return inconsistencies
                except (AttributeError, TypeError) as e:
                    logger.debug("structured_predict failed, using fallback", error=str(e))
            
            # Fallback: return empty list if structured_predict not available
            logger.warning("structured_predict not available for factual inconsistencies detection")
            return []

        except Exception as e:
            logger.warning("Failed to detect factual inconsistencies", error=str(e))
            return []

    async def _detect_unclear_explanations(
        self, content_extract: ContentExtract
    ) -> List[Dict[str, Any]]:
        """Detect unclear explanations in the content (T057)."""
        prompt_template = """請分析以下內容，找出不清楚或需要澄清的解釋。

核心觀點：
{key_insights}

核心概念：
{core_concepts}

內容：
{content}

請找出以下類型的不清楚之處：
1. 術語未定義或解釋不清
2. 步驟說明不夠詳細
3. 概念解釋過於抽象
4. 缺少必要的背景知識
5. 範例或類比不夠清楚"""

        try:
            key_insights_str = "\n".join("- " + insight for insight in content_extract.key_insights)
            core_concepts_str = ", ".join(content_extract.core_concepts)
            
            # Format the prompt template first
            formatted_prompt = prompt_template.format(
                key_insights=key_insights_str,
                core_concepts=core_concepts_str,
                content=content_extract.filtered_content,
            )
            
            # Try to use structured_predict if available
            if hasattr(self.llm, 'structured_predict'):
                try:
                    response = await self.llm.structured_predict(
                        UnclearExplanationsResponse,
                        formatted_prompt,
                    )
                    unclear_points = [point.model_dump() for point in response.unclear_points]
                    logger.info("Detected unclear explanations", count=len(unclear_points))
                    return unclear_points
                except (AttributeError, TypeError) as e:
                    logger.debug("structured_predict failed, using fallback", error=str(e))
            
            # Fallback: return empty list if structured_predict not available
            logger.warning("structured_predict not available for unclear explanations detection")
            return []

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
            response = await self.llm.acomplete(prompt)

            # Parse response into list
            claims = [
                line.strip()
                for line in response.text.split("\n")
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
            response = await self.llm.acomplete(prompt)

            # Parse response into list
            suggestions = [
                line.strip()
                for line in response.text.split("\n")
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

    async def _fact_check_via_tavily(
        self, fact_checking_needs: List[str]
    ) -> List[str]:
        """
        Perform fact-checking using Tavily API with LLM analysis (T072).
        
        Uses Tavily to find sources, then LLM to analyze whether sources actually
        support or contradict the claim.
        
        Args:
            fact_checking_needs: List of claims that need fact-checking
            
        Returns:
            List of fact-check results (formatted strings with verification status)
        """
        fact_check_results = []

        for claim in fact_checking_needs[:5]:  # Limit to top 5 claims to avoid API overload
            try:
                # Step 1: Get sources from Tavily
                result = await self.tavily_service.fact_check(claim, max_results=5)
                sources = result.get("sources", [])
                sources_count = len(sources)
                
                if sources_count == 0:
                    fact_check_results.append(
                        f"✗ 無法驗證：{claim} (未找到相關來源)"
                    )
                    logger.info(
                        "Fact-check: no sources found",
                        claim=claim,
                    )
                    continue
                
                # Step 2: Use LLM to analyze whether sources support/contradict the claim
                sources_text = "\n\n".join(
                    [
                        f"來源 {i+1}: {src.get('title', '無標題')}\n"
                        f"URL: {src.get('url', '無URL')}\n"
                        f"內容摘要: {src.get('content', '無內容')[:500]}"
                        for i, src in enumerate(sources)
                    ]
                )
                
                analysis_prompt = f"""請分析以下聲稱是否被提供的來源所驗證、反駁，或無法確定。

聲稱：
{claim}

來源資訊：
{sources_text}

請仔細分析：
1. 這些來源是否支持這個聲稱？（verified/contradicted/unclear/unverifiable）
2. 信心程度如何？（high/medium/low）
3. 關鍵證據是什麼？
4. 是否有任何矛盾或反駁的資訊？
5. 分析理由

請提供結構化的分析結果。"""

                # Try to use structured_predict if available
                if hasattr(self.llm, 'structured_predict'):
                    try:
                        analysis_response = await self.llm.structured_predict(
                            FactCheckAnalysisResponse,
                            analysis_prompt,
                        )
                        
                        analysis = analysis_response.analysis
                        status = analysis.verification_status
                        confidence = analysis.confidence
                        evidence = analysis.evidence[:200] if analysis.evidence else "無"
                        
                        # Format result based on verification status
                        if status == "verified":
                            status_icon = "✓"
                            status_text = "驗證通過"
                        elif status == "contradicted":
                            status_icon = "✗"
                            status_text = "被反駁"
                        elif status == "unclear":
                            status_icon = "?"
                            status_text = "無法確定"
                        else:  # unverifiable
                            status_icon = "✗"
                            status_text = "無法驗證"
                        
                        result_text = (
                            f"{status_icon} {status_text}：{claim}\n"
                            f"  信心程度：{confidence}\n"
                            f"  來源數量：{sources_count}\n"
                            f"  關鍵證據：{evidence}"
                        )
                        
                        if analysis.contradictions:
                            contradictions_text = "; ".join(analysis.contradictions[:2])
                            result_text += f"\n  矛盾資訊：{contradictions_text}"
                        
                        fact_check_results.append(result_text)
                        
                        logger.info(
                            "Fact-check completed with LLM analysis",
                            claim=claim,
                            status=status,
                            confidence=confidence,
                            sources_count=sources_count,
                        )
                        continue  # Success, move to next claim
                        
                    except (AttributeError, TypeError) as llm_error:
                        # structured_predict may not work with this LLM
                        logger.debug(
                            "structured_predict failed for fact-check, using simple verification",
                            claim=claim,
                            error=str(llm_error),
                        )
                
                # Fallback to simple verification if structured_predict not available or failed
                logger.warning(
                    "LLM fact-check analysis not available, using simple verification",
                    claim=claim,
                )
                fact_check_results.append(
                    f"? 部分驗證：{claim} (找到 {sources_count} 個相關來源，但無法進行深度分析)"
                )

            except ExternalServiceError as e:
                # Tavily failure should stop processing (FR-019)
                logger.error("Tavily fact-check failed", claim=claim, error=str(e))
                raise
            except Exception as e:
                logger.warning("Fact-check failed for claim", claim=claim, error=str(e))
                fact_check_results.append(f"? 檢查失敗：{claim} (錯誤：{str(e)})")

        return fact_check_results

