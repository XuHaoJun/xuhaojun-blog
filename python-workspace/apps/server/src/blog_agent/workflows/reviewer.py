"""Content review workflow step for quality enhancement."""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from uuid import UUID, uuid4

from llama_index.core import PromptTemplate
from llama_index.core.workflow import Event, step
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.config import config
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

# Import at runtime for Pydantic model_rebuild()
from blog_agent.workflows.memory_manager import ConversationMemoryManager

logger = get_logger(__name__)


class ReviewEvent(Event):
    """Event containing review findings."""

    review_findings: ReviewFindings
    content_extract: ContentExtract
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None
    errors: List[str] = []  # Issues that cannot be auto-corrected (T062)
    prompt_suggestions: List[PromptSuggestion] = []  # T079: Include prompt suggestions from parallel branch (支援多個)
    memory: Optional[ConversationMemoryManager] = None  # Optional memory manager for conversation history


# Rebuild model to resolve forward references
ReviewEvent.model_rebuild()


class ContentReviewer:
    """Content review step for identifying issues and suggesting improvements."""

    def __init__(self, llm: Optional[Union[Ollama, OpenAI]] = None, tavily_service=None):
        """Initialize content reviewer."""
        self.llm = llm or get_llm()
        self.fact_check_method = config.FACT_CHECK_METHOD.upper()
        
        # Only initialize Tavily service if method is TAVILY
        if self.fact_check_method == "TAVILY":
            if not config.TAVILY_API_KEY:
                raise ValueError("TAVILY_API_KEY is required when FACT_CHECK_METHOD is 'TAVILY'")
            self.tavily_service = tavily_service or get_tavily_service()
        else:
            self.tavily_service = None

    @step
    async def review(self, ev: ExtractEvent) -> ReviewEvent:  # type: ignore
        """Review extracted content for errors, inconsistencies, and unclear explanations."""
        try:
            content_extract = ev.content_extract
            conversation_log_id = ev.conversation_log_id
            memory = ev.memory  # Get memory from event

            # Perform comprehensive review
            logical_gaps = await self._detect_logical_gaps(content_extract)
            factual_inconsistencies = await self._detect_factual_inconsistencies(content_extract)
            unclear_explanations = await self._detect_unclear_explanations(content_extract)
            fact_checking_needs = await self._detect_fact_checking_needs(content_extract)  # FR-010
            
            # Perform fact-checking based on configured method
            fact_check_results = []
            if fact_checking_needs:
                if self.fact_check_method == "TAVILY":
                    fact_check_results = await self._fact_check_via_tavily(fact_checking_needs)
                else:  # LLM method (default)
                    fact_check_results = await self._fact_check_via_llm(fact_checking_needs)
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
                memory=memory,
            )

        except Exception as e:
            logger.error("Content review failed", error=str(e), exc_info=True)
            raise

    async def _detect_logical_gaps(self, content_extract: ContentExtract) -> List[Dict[str, Any]]:
        """Detect logical gaps with a constructive, editorial mindset (T055)."""
        # Soul Alignment: 像一位聰明的朋友一樣，指出論證哪裡跳躍太快，幫助使用者完善思考。
        template_str = """你是一位資深且思維嚴謹的編輯夥伴。請協助審視以下內容的邏輯推演過程，目標是讓論證更加無懈可擊。

核心觀點：
{key_insights}

核心概念：
{core_concepts}

內容：
{content}

請分析論證結構，找出可能會讓讀者感到困惑或論證不足的地方（Gaps）：
1. **推論跳躍**：是否有結論缺乏充分的前提鋪墊？
2. **因果斷裂**：A 到 B 的推導是否缺乏必要連結？
3. **隱藏假設**：是否依賴了未經證明的假設？

請不要為了挑剔而挑剔，只列出真正影響內容說服力的邏輯問題。"""

        try:
            key_insights_str = "\n".join("- " + insight for insight in content_extract.key_insights)
            core_concepts_str = ", ".join(content_extract.core_concepts)
            
            # Convert template string to PromptTemplate object
            prompt_tmpl = PromptTemplate(template_str)
            
            response = await self.llm.astructured_predict(
                LogicalGapsResponse,
                prompt_tmpl,
                key_insights=key_insights_str,
                core_concepts=core_concepts_str,
                content=content_extract.filtered_content,
            )

            gaps = [gap.model_dump() for gap in response.gaps]
            logger.info("Detected logical gaps", count=len(gaps))
            return gaps

        except Exception as e:
            logger.warning("Failed to detect logical gaps", error=str(e))
            return []

    async def _detect_factual_inconsistencies(
        self, content_extract: ContentExtract
    ) -> List[Dict[str, Any]]:
        """Detect factual inconsistencies with a constructive, editorial mindset (T056)."""
        # Soul Alignment: 像一位嚴謹的編輯夥伴，協助找出可能誤導讀者的事實問題。
        template_str = """你是一位資深且思維嚴謹的編輯夥伴。請協助審視以下內容，找出可能影響內容可信度的事實不一致或矛盾。

核心觀點：
{key_insights}

核心概念：
{core_concepts}

內容：
{content}

請找出以下類型的事實問題：
1. **前後矛盾的陳述**：內容中是否有相互衝突的聲稱？
2. **與已知事實不符的聲稱**：是否有明顯與公認事實不符的內容？
3. **數據或統計資料的不一致**：數字或統計是否前後不一致？
4. **時間線或因果關係的矛盾**：時間順序或因果關係是否有邏輯矛盾？

請不要為了挑剔而挑剔，只列出真正影響內容可信度的事實問題。"""

        try:
            key_insights_str = "\n".join("- " + insight for insight in content_extract.key_insights)
            core_concepts_str = ", ".join(content_extract.core_concepts)
            
            # Convert template string to PromptTemplate object
            prompt_tmpl = PromptTemplate(template_str)
            
            response = await self.llm.astructured_predict(
                FactualInconsistenciesResponse,
                prompt_tmpl,
                key_insights=key_insights_str,
                core_concepts=core_concepts_str,
                content=content_extract.filtered_content,
            )

            inconsistencies = [inc.model_dump() for inc in response.inconsistencies]
            logger.info("Detected factual inconsistencies", count=len(inconsistencies))
            return inconsistencies

        except Exception as e:
            logger.warning("Failed to detect factual inconsistencies", error=str(e))
            return []

    async def _detect_unclear_explanations(
        self, content_extract: ContentExtract
    ) -> List[Dict[str, Any]]:
        """Detect unclear explanations with a constructive, editorial mindset (T057)."""
        # Soul Alignment: 像一位體貼的編輯夥伴，協助找出可能讓讀者困惑的地方。
        template_str = """你是一位資深且思維嚴謹的編輯夥伴。請協助審視以下內容，找出可能讓讀者感到困惑或需要進一步澄清的解釋。

核心觀點：
{key_insights}

核心概念：
{core_concepts}

內容：
{content}

請找出以下類型的不清楚之處：
1. **術語未定義或解釋不清**：是否有專業術語或概念未充分解釋？
2. **步驟說明不夠詳細**：流程或步驟是否缺少關鍵細節？
3. **概念解釋過於抽象**：是否有概念需要更具體的說明或範例？
4. **缺少必要的背景知識**：是否假設了讀者可能不具備的背景知識？
5. **範例或類比不夠清楚**：範例或類比是否足夠具體和易懂？

請不要為了挑剔而挑剔，只列出真正影響讀者理解的不清楚之處。"""

        try:
            key_insights_str = "\n".join("- " + insight for insight in content_extract.key_insights)
            core_concepts_str = ", ".join(content_extract.core_concepts)
            
            # Convert template string to PromptTemplate object
            prompt_tmpl = PromptTemplate(template_str)
            
            response = await self.llm.astructured_predict(
                UnclearExplanationsResponse,
                prompt_tmpl,
                key_insights=key_insights_str,
                core_concepts=core_concepts_str,
                content=content_extract.filtered_content,
            )

            unclear_points = [point.model_dump() for point in response.unclear_points]
            logger.info("Detected unclear explanations", count=len(unclear_points))
            return unclear_points

        except Exception as e:
            logger.warning("Failed to detect unclear explanations", error=str(e))
            return []

    async def _detect_fact_checking_needs(
        self, content_extract: ContentExtract
    ) -> List[str]:
        """Detect claims specifically requiring verification based on importance and risk (FR-010, T060)."""
        # Soul Alignment: 專注於真正重要（Material）的聲稱，而非瑣碎細節。
        prompt = f"""請分析以下內容，找出需要進行外部驗證的關鍵事實聲稱。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

內容：
{content_extract.filtered_content}

請找出以下類型的聲稱（優先考慮若錯誤會誤導讀者或造成損害的項目）：
1. **具體且關鍵的數據/統計**（非通用常識）
2. **特定的歷史事件歸因**
3. **科學、醫療或技術上的明確斷言**
4. **關於特定人物或組織的行為描述**

請忽略一般常識或明顯的主觀意見。以列表形式輸出，每一行一個聲稱。"""

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
        """Generate high-value, actionable suggestions to elevate the content."""
        # Soul Alignment: 不要只修補錯誤，要提升品質。
        # 避免 "preachy" 或 "condescending" (居高臨下) 的語氣。
        prompt = f"""作為一位致力於讓內容更卓越的專業編輯，請根據發現的問題提供改進建議。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

已識別的問題概況：
- 邏輯需要加強處：{len(issues.get('logical_gaps', []))}
- 需釐清的事實：{len(issues.get('factual_inconsistencies', []))}
- 解釋不夠清晰處：{len(issues.get('unclear_explanations', []))}

請提供 3-5 個**高價值且具體的行動建議**。建議方向：
1. **提升清晰度**：如何讓複雜概念對讀者更友善？（而不僅僅是說「解釋清楚」）
2. **強化論證**：如何填補邏輯缺口以增強說服力？
3. **增加深度**：如果有事實模糊，建議如何補充背景資訊或數據。

語氣要求：真誠、直接、建設性，像與聰明的同事討論一樣。只輸出建議列表。"""

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
        if not self.tavily_service:
            raise ValueError("Tavily service is not initialized. FACT_CHECK_METHOD must be 'TAVILY'.")
        
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
                
                # Soul Alignment: Calibrated Uncertainty.
                # 不只問「是否支持」，要問「證據的強度與細節」。
                template_str = """請像一位嚴謹的研究員分析以下聲稱。根據提供的來源，評估該聲稱的可信度。

聲稱：
{claim}

來源資訊：
{sources_text}

請進行細緻的證據權衡（Epistemic Calibration）：
1. **證據支持度**：來源是強烈支持、部分支持、反駁，還是僅僅相關但未直接證實？
2. **細微差別 (Nuance)**：聲稱是否過於簡化？來源是否有特定的上下文限制？
3. **信心校準**：如果來源資訊不足或有衝突，請誠實表達不確定性 (Uncertainty)。

請基於證據進行分析，避免過度推斷。請提供結構化的分析結果。"""

                try:
                    # Convert template string to PromptTemplate object
                    prompt_tmpl = PromptTemplate(template_str)
                    
                    analysis_response = await self.llm.astructured_predict(
                        FactCheckAnalysisResponse,
                        prompt_tmpl,
                        claim=claim,
                        sources_text=sources_text,
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
                    
                except Exception as llm_error:
                    # Fallback to simple verification if LLM analysis fails
                    logger.warning(
                        "LLM fact-check analysis failed, using simple verification",
                        claim=claim,
                        error=str(llm_error),
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

    async def _fact_check_via_llm(
        self, fact_checking_needs: List[str]
    ) -> List[str]:
        """
        Perform fact-checking using LLM only (without external APIs).
        
        Uses LLM's knowledge to analyze whether claims are verified, contradicted,
        unclear, or unverifiable.
        
        Args:
            fact_checking_needs: List of claims that need fact-checking
            
        Returns:
            List of fact-check results (formatted strings with verification status)
        """
        fact_check_results = []

        for claim in fact_checking_needs[:5]:  # Limit to top 5 claims to avoid overload
            try:
                # Soul Alignment: Calibrated Uncertainty.
                # 不只問「是否正確」，要問「證據的強度與細微差別」。
                template_str = """請像一位嚴謹的研究員，基於你的知識分析以下聲稱。評估該聲稱的可信度與證據強度。

聲稱：
{claim}

請進行細緻的證據權衡（Epistemic Calibration）：
1. **證據支持度**：這個聲稱是強烈支持、部分支持、被反駁，還是無法確定？（verified/contradicted/unclear/unverifiable）
2. **細微差別 (Nuance)**：聲稱是否過於簡化？是否有特定的上下文限制或條件？
3. **信心校準**：如果資訊不足或有衝突，請誠實表達不確定性 (Uncertainty)。信心程度如何？（high/medium/low）
4. **關鍵證據或理由**：支持或反駁這個聲稱的關鍵證據是什麼？
5. **已知的矛盾資訊**：是否有任何已知的矛盾資訊？

請基於證據進行分析，避免過度推斷。請提供結構化的分析結果。"""

                try:
                    # Convert template string to PromptTemplate object
                    prompt_tmpl = PromptTemplate(template_str)
                    
                    analysis_response = await self.llm.astructured_predict(
                        FactCheckAnalysisResponse,
                        prompt_tmpl,
                        claim=claim,
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
                        f"  關鍵證據：{evidence}"
                    )
                    
                    if analysis.contradictions:
                        contradictions_text = "; ".join(analysis.contradictions[:2])
                        result_text += f"\n  矛盾資訊：{contradictions_text}"
                    
                    fact_check_results.append(result_text)
                    
                    logger.info(
                        "Fact-check completed with LLM",
                        claim=claim,
                        status=status,
                        confidence=confidence,
                    )
                    
                except Exception as llm_error:
                    # Fallback if LLM analysis fails
                    logger.warning(
                        "LLM fact-check analysis failed",
                        claim=claim,
                        error=str(llm_error),
                    )
                    fact_check_results.append(
                        f"? 檢查失敗：{claim} (無法進行分析：{str(llm_error)})"
                    )

            except Exception as e:
                logger.warning("Fact-check failed for claim", claim=claim, error=str(e))
                fact_check_results.append(f"? 檢查失敗：{claim} (錯誤：{str(e)})")

        return fact_check_results

