"""Prompt analysis workflow step for optimization suggestions."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

from llama_index.core import PromptTemplate
from llama_index.core.workflow import Event, step
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.services.llm import get_llm
from blog_agent.storage.models import Message, PromptCandidate, PromptSuggestion
from blog_agent.utils.logging import get_logger
from blog_agent.workflows.extractor import ExtractEvent, ExtractStartEvent
from blog_agent.workflows.schemas import PromptCandidatesResponse
from blog_agent.workflows.memory_manager import ConversationMemoryManager

if TYPE_CHECKING:
    from blog_agent.workflows.memory_manager import ConversationMemoryManager

logger = get_logger(__name__)


class PromptAnalysisEvent(Event):
    """Event containing prompt analysis results."""

    prompt_suggestions: List[PromptSuggestion]  # 支援多個 user prompts
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None
    memory: Optional["ConversationMemoryManager"] = None  # Optional memory manager for conversation history


class PromptAnalyzer:
    """Prompt analysis step for analyzing user prompts and suggesting improvements."""

    def __init__(self, llm: Optional[Union[Ollama, OpenAI]] = None):
        """Initialize prompt analyzer."""
        self.llm = llm or get_llm()

    @step
    async def analyze(self, ev: ExtractStartEvent) -> PromptAnalysisEvent:  # type: ignore
        """
        Analyze user prompts from conversation logs and suggest improvements.
        
        This step extracts user prompts, evaluates their effectiveness, and generates
        at least 3 alternative prompt candidates with reasoning (FR-012, FR-013).
        
        This runs in parallel with the main workflow, starting from ExtractStartEvent
        to access the original messages.
        
        變更：現在為每個 user prompt 產生一個 PromptSuggestion，而不是只分析第一個。
        """
        try:
            messages = ev.messages
            conversation_log_id = ev.conversation_log_id
            conversation_log_metadata = ev.conversation_log_metadata or {}
            
            # Get or create memory manager
            memory = ev.memory
            if memory is None:
                memory = ConversationMemoryManager.from_messages(messages)
            
            # T074: Extract user prompts from conversation logs
            user_prompts = await self._extract_user_prompts(messages)
            
            if not user_prompts:
                logger.info("No user prompts found in conversation", conversation_log_id=conversation_log_id)
                # Return empty suggestions list if no prompts found
                return PromptAnalysisEvent(
                    prompt_suggestions=[],
                    conversation_log_id=conversation_log_id,
                    conversation_log_metadata=conversation_log_metadata,
                )
            
            # Analyze each user prompt and generate a suggestion for each
            prompt_suggestions = []
            
            for idx, user_prompt in enumerate(user_prompts):
                try:
                    logger.info(
                        "Analyzing user prompt",
                        prompt_index=idx + 1,
                        total_prompts=len(user_prompts),
                        conversation_log_id=conversation_log_id,
                    )
                    
                    # Safety & Intent Check: Check for harmful content before optimization
                    is_safe, safety_level, safety_message = await self._check_prompt_safety(user_prompt, messages, memory)
                    
                    if not is_safe or safety_level in ["high_risk", "medium_risk"]:
                        logger.warning(
                            "Harmful content detected, skipping optimization or providing safety guidance",
                            safety_level=safety_level,
                            prompt_index=idx + 1,
                            conversation_log_id=conversation_log_id,
                        )
                        # Create a safety-focused suggestion instead of optimizing
                        safety_analysis = f"""安全性評估：{safety_message}

此提示詞涉及安全風險（風險等級：{safety_level}），不適合進行優化。

建議：
- 如果涉及敏感話題（如自殺、醫療、法律），請尋求專業協助
- 如果涉及非法活動，請勿繼續
- 請重新思考您的需求，使用安全且合法的方式達成目標"""
                        
                        # Create safety guidance candidates instead of optimization
                        safety_candidates = [
                            PromptCandidate(
                                type="safety-guidance",
                                prompt="此提示詞涉及安全風險，無法提供優化建議。請重新思考您的需求，使用安全且合法的方式達成目標。",
                                reasoning="安全優先：檢測到有害內容，提供安全引導而非優化建議",
                            )
                        ]
                        
                        prompt_suggestion = PromptSuggestion(
                            conversation_log_id=conversation_log_id,
                            original_prompt=user_prompt,
                            analysis=safety_analysis,
                            better_candidates=safety_candidates,
                            reasoning="由於檢測到安全風險，無法提供優化建議。請重新思考您的需求。",
                            expected_effect="此提示詞涉及安全風險，建議重新思考需求。",
                        )
                        prompt_suggestions.append(prompt_suggestion)
                        continue
                    
                    # T075: Evaluate prompt effectiveness
                    effectiveness_analysis = await self._evaluate_prompt_effectiveness(user_prompt, messages, memory)
                    
                    # T076: Generate at least 3 alternative prompt candidates (FR-012)
                    # T077a: Generate structured PromptCandidate objects instead of plain strings
                    better_candidates = await self._generate_structured_alternative_prompts(user_prompt, messages, memory)
                    
                    # Ensure we have at least 3 candidates (FR-012)
                    if len(better_candidates) < 3:
                        logger.warning(
                            "Generated fewer than 3 prompt candidates, generating more",
                            count=len(better_candidates),
                            prompt_index=idx + 1,
                            conversation_log_id=conversation_log_id,
                        )
                        additional_candidates = await self._generate_additional_structured_candidates(
                            user_prompt, messages, memory, needed=3 - len(better_candidates)
                        )
                        better_candidates.extend(additional_candidates)
                    
                    # Ensure we have at least 3 candidates (use fallback if needed)
                    if len(better_candidates) < 3:
                        fallback = await self._generate_fallback_structured_alternatives(user_prompt)
                        better_candidates.extend(fallback)
                        better_candidates = better_candidates[:10]  # Limit to 10
                    
                    # T077: Generate reasoning for why alternatives are better (FR-013)
                    # Extract prompt strings for reasoning generation
                    candidate_prompts = [c.prompt for c in better_candidates]
                    reasoning = await self._generate_reasoning(user_prompt, candidate_prompts, messages, memory)
                    
                    # T077b: Generate expected_effect description
                    expected_effect = await self._generate_expected_effect(user_prompt, better_candidates, messages, memory)
                    
                    prompt_suggestion = PromptSuggestion(
                        conversation_log_id=conversation_log_id,
                        original_prompt=user_prompt,
                        analysis=effectiveness_analysis,
                        better_candidates=better_candidates[:10],  # Limit to 10, but ensure at least 3
                        reasoning=reasoning,
                        expected_effect=expected_effect,  # T077b: Add expected effect
                    )
                    
                    prompt_suggestions.append(prompt_suggestion)
                    
                    logger.info(
                        "Prompt analysis completed for one prompt",
                        prompt_index=idx + 1,
                        candidates_count=len(better_candidates),
                        conversation_log_id=conversation_log_id,
                    )
                except Exception as e:
                    logger.error(
                        "Failed to analyze prompt",
                        prompt_index=idx + 1,
                        prompt_preview=user_prompt[:50],
                        error=str(e),
                        conversation_log_id=conversation_log_id,
                        exc_info=True,
                    )
                    # Continue with next prompt instead of failing completely
                    continue
            
            logger.info(
                "Prompt analysis completed for all prompts",
                total_prompts=len(user_prompts),
                suggestions_generated=len(prompt_suggestions),
                conversation_log_id=conversation_log_id,
            )
            
            return PromptAnalysisEvent(
                prompt_suggestions=prompt_suggestions,
                conversation_log_id=conversation_log_id,
                conversation_log_metadata=conversation_log_metadata,
                memory=memory,
            )
            
        except Exception as e:
            logger.error("Prompt analysis failed", error=str(e), exc_info=True)
            # Return empty suggestions list on error
            memory = ev.memory
            if memory is None:
                memory = ConversationMemoryManager.from_messages(ev.messages)
            return PromptAnalysisEvent(
                prompt_suggestions=[],
                conversation_log_id=ev.conversation_log_id,
                conversation_log_metadata=ev.conversation_log_metadata or {},
                memory=memory,
            )

    async def _extract_user_prompts(self, messages: List[Message]) -> List[str]:
        """
        T074: Extract user prompts from conversation logs.
        
        This method extracts prompts that were sent by the user (role="user")
        from the conversation messages.
        """
        # Extract all user messages
        user_messages = [
            msg.content.strip()
            for msg in messages
            if msg.role == "user" and msg.content.strip()
        ]
        
        # Filter out very short messages (likely not substantial prompts)
        prompts = [msg for msg in user_messages if len(msg) > 10]
        
        return prompts

    async def _extract_prompts_via_llm(self, content: str) -> List[str]:
        """Extract user prompts from content using LLM."""
        prompt = f"""請從以下對話內容中提取所有使用者（user）的提示詞或問題。

對話內容：
{content[:2000]}  # Limit content length

要求：
1. 只提取使用者發送的提示詞或問題
2. 每個提示詞應該完整且有意義
3. 如果沒有找到使用者提示詞，返回空列表
4. 以 JSON 陣列格式返回，例如：["提示詞1", "提示詞2"]

請只輸出 JSON 陣列，不要額外說明。"""

        try:
            response = await self.llm.acomplete(prompt)
            # Try to parse JSON response
            prompts = json.loads(response.text.strip())
            if isinstance(prompts, list):
                return [p for p in prompts if isinstance(p, str) and len(p) > 10]
        except Exception as e:
            logger.warning("Failed to extract prompts via LLM", error=str(e))
        
        return []

    async def _check_prompt_safety(
        self, prompt: str, messages: List[Message], memory: Optional[ConversationMemoryManager] = None
    ) -> Tuple[bool, str, str]:
        """
        Check if a prompt contains harmful content or attempts to bypass safety restrictions.
        
        Returns:
            tuple: (is_safe, safety_level, safety_message)
            - is_safe: True if prompt is safe to optimize, False if harmful
            - safety_level: "safe", "low_risk", "medium_risk", "high_risk"
            - safety_message: Description of safety concerns if any
        """
        context_summary = await self._summarize_conversation_context(messages, memory)
        
        safety_check_prompt = f"""請評估以下使用者提示詞的安全性。

使用者提示詞：
{prompt}

對話上下文摘要：
{context_summary}

請評估：
1. 該提示詞是否試圖繞過安全限制或 AI 的使用政策？
2. 是否涉及有害內容，例如：
   - 生化武器、化學武器製造
   - CSAM（兒童性虐待材料）
   - 破壞基礎設施或非法活動
   - 自殺或自我傷害
   - 未經授權的醫療或法律建議
3. 是否涉及其他敏感或有害話題？

請以 JSON 格式返回評估結果：
{{
  "is_safe": true/false,
  "safety_level": "safe" | "low_risk" | "medium_risk" | "high_risk",
  "safety_message": "安全性評估說明",
  "concerns": ["具體的安全疑慮列表"]
}}

請只輸出 JSON，不要額外說明。"""

        try:
            response = await self.llm.acomplete(safety_check_prompt)
            response_text = response.text.strip()
            
            # Try to extract JSON from response
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            
            safety_result = json.loads(response_text)
            is_safe = safety_result.get("is_safe", True)
            safety_level = safety_result.get("safety_level", "safe")
            safety_message = safety_result.get("safety_message", "")
            
            return (is_safe, safety_level, safety_message)
        except Exception as e:
            logger.warning("Failed to perform safety check, defaulting to safe", error=str(e))
            # Default to safe if check fails
            return (True, "safe", "")

    async def _evaluate_prompt_effectiveness(
        self, prompt: str, messages: List[Message], memory: Optional[ConversationMemoryManager] = None
    ) -> str:
        """
        T075: Evaluate prompt effectiveness with intent alignment and safety assessment.
        
        Analyzes the given prompt from three levels:
        1. Immediate desires (what the user is asking for)
        2. Underlying goals (what the user really wants to achieve)
        3. Missing background expectations (unstated assumptions)
        
        Also includes safety assessment to detect harmful content.
        """
        # Extract context from messages for better analysis
        context_summary = await self._summarize_conversation_context(messages, memory)
        
        evaluation_prompt = f"""請以一位資深 AI 互動專家的角度，深度分析以下使用者提示詞。

使用者提示詞：
{prompt}

對話上下文摘要：
{context_summary}

請分析以下三個層次：
1. **即時慾望**：使用者表面上要求什麼？
2. **底層目標**：使用者真正想要達成的結果是什麼？（例如：使用者問「如何修改這段 code」，底層目標可能是「修復 bug」或「優化效能」，而不僅僅是改語法）
3. **缺失的背景期望**：有哪些使用者沒說，但預設希望 AI 遵守的標準？（例如：正確性、安全性、不破壞現有架構）

請基於這三個層次的落差，指出目前 Prompt 的主要弱點。

請提供詳細的分析，以正體中文撰寫。"""

        response = await self.llm.acomplete(evaluation_prompt)
        return response.text.strip()

    async def _generate_structured_alternative_prompts(
        self, original_prompt: str, messages: List[Message], memory: Optional[ConversationMemoryManager] = None
    ) -> List[PromptCandidate]:
        """
        T076, T077a: Generate at least 3 structured alternative prompt candidates (FR-012).
        
        Generates improved versions of the original prompt with different
        approaches or structures, returning structured PromptCandidate objects.
        """
        context_summary = await self._summarize_conversation_context(messages, memory)
        
        template_str = """你是一位精通 Prompt Engineering 的專家朋友。請根據使用者的原始提示詞與其「底層目標」，構思至少 3 個不同的優化策略。

原始提示詞：
{original_prompt}

上下文：
{context_summary}

不要死板地套用固定模板。請根據問題的性質選擇最適合的策略，例如：
- 如果任務複雜，可能適合「思維鏈 (chain-of-thought)」或「拆解步驟 (step-by-step)」
- 如果需要特定風格，可能適合「角色設定 (expert-persona)」或「語氣指導 (tone-guidance)」
- 如果容易產生幻覺，可能需要「要求引用來源 (source-citation)」或「校準不確定性 (calibrated-uncertainty)」
- 如果是程式碼，可能需要「提供邊界案例 (edge-cases)」或「輸入輸出範例 (few-shot)」
- 如果用戶希望保持簡潔，可以提供「極簡版 (minimalist)」，只修正關鍵邏輯，保留用戶原本語氣
- 如果需要結構化輸出，可以使用「結構化格式 (structured)」
- 如果需要創意或特定情境，可以使用「情境設定 (scenario-based)」

要求：
1. 生成至少 3 個候選 Prompt，每個使用不同的策略
2. 每個候選應該包含：
   - type: 策略類型（使用描述性的名稱，如 "few-shot", "chain-of-thought", "expert-persona", "minimalist" 等）
   - prompt: 完整的改進後提示詞（避免使用「作為一個世界級的專家...」這類過度 AI 化的語言）
   - reasoning: 為什麼選擇這個策略，以及這個版本如何更好地達成用戶的底層目標（簡短說明，包含語氣變化說明）
3. 確保至少有一個候選是 "minimalist" 類型，只修正關鍵邏輯，保留用戶原本語氣
4. 改進版本應該更清晰、更具體、更有效，但不要過度說教或家長式
5. 每個候選應該完整且可以直接使用"""

        try:
            # Convert template string to PromptTemplate object
            prompt_tmpl = PromptTemplate(template_str)
            
            # Try to use astructured_predict first
            try:
                response = await self.llm.astructured_predict(
                    PromptCandidatesResponse,
                    prompt_tmpl,
                    original_prompt=original_prompt,
                    context_summary=context_summary,
                )
                
                # Convert to PromptCandidate objects
                candidates = []
                for item in response.candidates:
                    try:
                        candidate = PromptCandidate(
                            type=item.type,
                            prompt=item.prompt,
                            reasoning=item.reasoning,
                        )
                        if len(candidate.prompt) > 20:  # Filter out too short prompts
                            candidates.append(candidate)
                    except Exception as e:
                        logger.warning("Failed to create PromptCandidate", error=str(e), data=item)
                        continue
                
                if len(candidates) >= 3:
                    return candidates[:10]  # Limit to 10 candidates
            except Exception as e:
                # astructured_predict failed, fall through to JSON parsing
                logger.debug("astructured_predict failed, using JSON parsing fallback", error=str(e))
            
            # Fallback: Use JSON mode with manual parsing
            # Format the template for fallback
            formatted_prompt = template_str.format(
                original_prompt=original_prompt,
                context_summary=context_summary,
            )
            json_prompt = f"""{formatted_prompt}

請以 JSON 格式返回，格式如下：
{{
  "candidates": [
    {{
      "type": "few-shot",
      "prompt": "改進後的提示詞",
      "reasoning": "為什麼選擇這個策略，以及語氣變化"
    }},
    {{
      "type": "chain-of-thought",
      "prompt": "改進後的提示詞",
      "reasoning": "為什麼選擇這個策略，以及語氣變化"
    }},
    {{
      "type": "minimalist",
      "prompt": "改進後的提示詞（保留用戶原本語氣）",
      "reasoning": "為什麼選擇這個策略，以及語氣變化"
    }}
  ]
}}

請只輸出 JSON，不要額外說明。注意：type 可以是任何描述性的策略名稱，不限定於上述範例。"""
            
            response = await self.llm.acomplete(json_prompt)
            response_text = response.text.strip()
            
            # Try to extract JSON from response (may be wrapped in markdown code blocks)
            # Remove markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            
            parsed_response = json.loads(response_text)
            response_obj = PromptCandidatesResponse(**parsed_response)
            
            # Convert to PromptCandidate objects
            candidates = []
            for item in response_obj.candidates:
                try:
                    candidate = PromptCandidate(
                        type=item.type,
                        prompt=item.prompt,
                        reasoning=item.reasoning,
                    )
                    if len(candidate.prompt) > 20:  # Filter out too short prompts
                        candidates.append(candidate)
                except Exception as e:
                    logger.warning("Failed to create PromptCandidate", error=str(e), data=item)
                    continue
            
            if len(candidates) >= 3:
                return candidates[:10]  # Limit to 10 candidates
                
        except Exception as e:
            logger.warning("Failed to generate structured alternative prompts", error=str(e))
        
        # Fallback: generate simple structured alternatives
        return await self._generate_fallback_structured_alternatives(original_prompt)

    async def _generate_additional_structured_candidates(
        self, original_prompt: str, messages: List[Message], memory: Optional[ConversationMemoryManager], needed: int
    ) -> List[PromptCandidate]:
        """Generate additional structured prompt candidates if we don't have enough."""
        context_summary = await self._summarize_conversation_context(messages, memory)
        
        template_str = """請根據以下原始提示詞，再生成 {needed} 個不同的改進版本，使用與之前不同的策略。

原始提示詞：
{original_prompt}

對話上下文：
{context_summary}

要求：
1. 生成 {needed} 個與之前不同的改進版本
2. 每個版本使用不同的動態策略（如 few-shot、expert-persona、edge-cases、scenario-based、constraint-based 等，避免重複已使用的策略）
3. 每個候選應該包含：
   - type: 策略類型（描述性名稱）
   - prompt: 完整的改進後提示詞（避免過度 AI 化的語言）
   - reasoning: 為什麼選擇這個策略，以及語氣變化說明
4. 每個候選應該完整且可以直接使用"""

        try:
            # Convert template string to PromptTemplate object
            prompt_tmpl = PromptTemplate(template_str)
            
            # Try to use astructured_predict first
            try:
                response = await self.llm.astructured_predict(
                    PromptCandidatesResponse,
                    prompt_tmpl,
                    original_prompt=original_prompt,
                    context_summary=context_summary,
                    needed=needed,
                )
                
                # Convert to PromptCandidate objects
                candidates = []
                for item in response.candidates:
                    try:
                        candidate = PromptCandidate(
                            type=item.type,
                            prompt=item.prompt,
                            reasoning=item.reasoning,
                        )
                        if len(candidate.prompt) > 20:
                            candidates.append(candidate)
                    except Exception as e:
                        logger.warning("Failed to create additional PromptCandidate", error=str(e))
                        continue
                return candidates
            except Exception as e:
                # astructured_predict failed, fall through to JSON parsing
                logger.debug("astructured_predict failed, using JSON parsing fallback", error=str(e))
            
            # Fallback: Use JSON mode with manual parsing
            # Format the template for fallback
            formatted_prompt = template_str.format(
                original_prompt=original_prompt,
                context_summary=context_summary,
                needed=needed,
            )
            json_prompt = f"""{formatted_prompt}

請以 JSON 格式返回，格式如下：
{{
  "candidates": [
    {{
      "type": "structured",
      "prompt": "改進後的提示詞",
      "reasoning": "為什麼這個版本更好"
    }}
  ]
}}

請只輸出 JSON，不要額外說明。"""
            
            response = await self.llm.acomplete(json_prompt)
            response_text = response.text.strip()
            
            # Try to extract JSON from response (may be wrapped in markdown code blocks)
            # Remove markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            
            parsed_response = json.loads(response_text)
            response_obj = PromptCandidatesResponse(**parsed_response)
            
            # Convert to PromptCandidate objects
            candidates = []
            for item in response_obj.candidates:
                try:
                    candidate = PromptCandidate(
                        type=item.type,
                        prompt=item.prompt,
                        reasoning=item.reasoning,
                    )
                    if len(candidate.prompt) > 20:
                        candidates.append(candidate)
                except Exception as e:
                    logger.warning("Failed to create additional PromptCandidate", error=str(e))
                    continue
            return candidates
        except Exception as e:
            logger.warning("Failed to generate additional structured candidates", error=str(e))
        
        return []

    async def _generate_fallback_structured_alternatives(self, original_prompt: str) -> List[PromptCandidate]:
        """Generate simple fallback structured alternatives if LLM generation fails."""
        alternatives = []
        
        # Strategy 1: Minimalist version (preserves user's original tone)
        alt1 = PromptCandidate(
            type="minimalist",
            prompt=original_prompt,  # Keep original, just ensure it's clear
            reasoning="極簡版本，保留用戶原本語氣，只確保提示詞清晰完整。適合不喜歡過度 AI 化語言的用戶。",
        )
        alternatives.append(alt1)
        
        # Strategy 2: Structured version
        alt2 = PromptCandidate(
            type="structured",
            prompt=f"""請根據以下要求完成任務：

任務：{original_prompt}

要求：
1. 提供詳細且完整的回答
2. 包含具體的範例或說明
3. 確保回答清晰易懂""",
            reasoning="使用結構化格式，明確列出任務和要求，讓 AI 更容易理解並產生完整的回答。語氣：直接明確，不帶過度修飾。",
        )
        alternatives.append(alt2)
        
        # Strategy 3: Chain-of-thought version
        alt3 = PromptCandidate(
            type="chain-of-thought",
            prompt=f"""我需要完成以下任務：{original_prompt}

請按照以下步驟進行：
1. 先理解任務的核心需求
2. 提供詳細的分析和說明
3. 給出具體的建議或解決方案""",
            reasoning="使用思維鏈方式，引導 AI 逐步思考，確保回答的邏輯性和完整性。語氣：引導式，幫助 AI 系統化思考。",
        )
        alternatives.append(alt3)
        
        return alternatives

    async def _generate_reasoning(
        self, original_prompt: str, better_candidates: List[str], messages: List[Message], memory: Optional[ConversationMemoryManager] = None
    ) -> str:
        """
        T077: Generate reasoning for why alternatives are better (FR-013).
        
        Provides detailed explanation of why each alternative prompt is better
        than the original and what improvements it offers.
        """
        context_summary = await self._summarize_conversation_context(messages, memory)
        
        reasoning_prompt = f"""請分析為什麼以下改進版本的提示詞比原始提示詞更好。

原始提示詞：
{original_prompt}

改進版本（前 3 個）：
{chr(10).join(f'{i+1}. {candidate}' for i, candidate in enumerate(better_candidates[:3]))}

對話上下文：
{context_summary}

請為每個改進版本說明：
1. 相較於原始提示詞，這個版本做了哪些改進？
2. 這些改進如何讓提示詞更有效？
3. 這個版本適合什麼樣的使用場景？

請提供詳細的分析，以正體中文撰寫，結構清晰。"""

        response = await self.llm.acomplete(reasoning_prompt)
        return response.text.strip()

    async def _generate_expected_effect(
        self, original_prompt: str, better_candidates: List[PromptCandidate], messages: List[Message], memory: Optional[ConversationMemoryManager] = None
    ) -> str:
        """
        T077b: Generate expected effect description (UI/UX support).
        
        Explains what effect using the optimized prompts will have on the AI's response quality.
        """
        context_summary = await self._summarize_conversation_context(messages, memory)
        
        # Extract candidate types and prompts for analysis
        candidate_summary = "\n".join(
            f"- {c.type}: {c.prompt[:100]}..." for c in better_candidates[:3]
        )
        
        effect_prompt = f"""請說明使用以下優化後的提示詞，預期會對 AI 的回答產生什麼效果。

原始提示詞：
{original_prompt}

優化後的提示詞候選（前 3 個）：
{candidate_summary}

對話上下文：
{context_summary}

請說明：
1. 使用這些優化提示詞後，AI 的回答品質會如何提升？
2. 回答會變得更具體、更完整、還是更符合需求？
3. 這些優化如何幫助獲得更好的結果？

請提供簡潔明瞭的說明（100-200字），以正體中文撰寫。"""

        try:
            response = await self.llm.acomplete(effect_prompt)
            return response.text.strip()[:500]  # Limit length
        except Exception as e:
            logger.warning("Failed to generate expected effect", error=str(e))
            return "使用優化後的提示詞可以獲得更清晰、更具體、更符合需求的 AI 回答。"

    async def _summarize_conversation_context(
        self, messages: List[Message], memory: Optional[ConversationMemoryManager] = None
    ) -> str:
        """
        Summarize conversation context for prompt analysis using ChatSummaryMemoryBuffer.
        
        Uses ChatSummaryMemoryBuffer to automatically summarize conversation history
        when it exceeds token limits, preserving important context like user names,
        key settings, and conversation goals.
        
        Args:
            messages: List of Message objects
            memory: Optional ConversationMemoryManager instance. If None, creates a new one from messages.
        
        Returns:
            String representation of conversation context (with summaries if needed)
        """
        # If messages are very short, return simple summary
        if len(messages) <= 2:
            return f"對話包含 {len(messages)} 條訊息"
        
        # Use memory manager if provided, otherwise create from messages
        if memory is None:
            memory = ConversationMemoryManager.from_messages(messages)
        
        # Get summarized context from memory
        try:
            context = memory.get_summarized_context()
            logger.debug("Retrieved summarized context from memory", context_length=len(context))
            return context
        except Exception as e:
            logger.warning("Failed to get summarized context from memory, using fallback", error=str(e))
            # Fallback to simple truncation on error
            assistant_responses = [
                msg.content[:200]
                for msg in messages
                if msg.role == "assistant"
            ]
            if assistant_responses:
                return f"對話包含 {len(messages)} 條訊息，AI 回應摘要：{assistant_responses[0]}..."
            else:
                return f"對話包含 {len(messages)} 條訊息"

