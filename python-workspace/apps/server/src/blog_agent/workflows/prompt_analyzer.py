"""Prompt analysis workflow step for optimization suggestions."""

import json
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

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
from blog_agent.storage.models import Message, PromptCandidate, PromptSuggestion
from blog_agent.utils.logging import get_logger
from blog_agent.workflows.extractor import ExtractEvent, ExtractStartEvent
from blog_agent.workflows.schemas import PromptCandidatesResponse

logger = get_logger(__name__)


class PromptAnalysisEvent(Event):
    """Event containing prompt analysis results."""

    prompt_suggestion: PromptSuggestion
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None


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
        """
        try:
            messages = ev.messages
            conversation_log_id = ev.conversation_log_id
            conversation_log_metadata = ev.conversation_log_metadata or {}
            
            # T074: Extract user prompts from conversation logs
            user_prompts = await self._extract_user_prompts(messages)
            
            if not user_prompts:
                logger.info("No user prompts found in conversation", conversation_log_id=conversation_log_id)
                # Return empty suggestion if no prompts found
                # T077a: Use structured PromptCandidate objects instead of strings
                empty_candidates = [
                    PromptCandidate(
                        type="structured",
                        prompt="",
                        reasoning="",
                    ),
                    PromptCandidate(
                        type="role-play",
                        prompt="",
                        reasoning="",
                    ),
                    PromptCandidate(
                        type="chain-of-thought",
                        prompt="",
                        reasoning="",
                    ),
                ]
                prompt_suggestion = PromptSuggestion(
                    conversation_log_id=conversation_log_id,
                    original_prompt="",
                    analysis="未找到使用者提示詞",
                    better_candidates=empty_candidates,  # Ensure at least 3 structured candidates (FR-012)
                    reasoning="對話紀錄中沒有使用者提示詞可供分析",
                    expected_effect=None,  # T077b: No effect if no prompts
                )
                return PromptAnalysisEvent(
                    prompt_suggestion=prompt_suggestion,
                    conversation_log_id=conversation_log_id,
                    conversation_log_metadata=conversation_log_metadata,
                )
            
            # Analyze each prompt (for now, analyze the first significant prompt)
            # In a full implementation, we might analyze all prompts or the most important one
            primary_prompt = user_prompts[0] if user_prompts else ""
            
            # T075: Evaluate prompt effectiveness
            effectiveness_analysis = await self._evaluate_prompt_effectiveness(primary_prompt, messages)
            
            # T076: Generate at least 3 alternative prompt candidates (FR-012)
            # T077a: Generate structured PromptCandidate objects instead of plain strings
            better_candidates = await self._generate_structured_alternative_prompts(primary_prompt, messages)
            
            # Ensure we have at least 3 candidates (FR-012)
            if len(better_candidates) < 3:
                logger.warning(
                    "Generated fewer than 3 prompt candidates, generating more",
                    count=len(better_candidates),
                    conversation_log_id=conversation_log_id,
                )
                additional_candidates = await self._generate_additional_structured_candidates(
                    primary_prompt, messages, needed=3 - len(better_candidates)
                )
                better_candidates.extend(additional_candidates)
            
            # Ensure we have at least 3 candidates (use fallback if needed)
            if len(better_candidates) < 3:
                fallback = await self._generate_fallback_structured_alternatives(primary_prompt)
                better_candidates.extend(fallback)
                better_candidates = better_candidates[:10]  # Limit to 10
            
            # T077: Generate reasoning for why alternatives are better (FR-013)
            # Extract prompt strings for reasoning generation
            candidate_prompts = [c.prompt for c in better_candidates]
            reasoning = await self._generate_reasoning(primary_prompt, candidate_prompts, messages)
            
            # T077b: Generate expected_effect description
            expected_effect = await self._generate_expected_effect(primary_prompt, better_candidates, messages)
            
            prompt_suggestion = PromptSuggestion(
                conversation_log_id=conversation_log_id,
                original_prompt=primary_prompt,
                analysis=effectiveness_analysis,
                better_candidates=better_candidates[:10],  # Limit to 10, but ensure at least 3
                reasoning=reasoning,
                expected_effect=expected_effect,  # T077b: Add expected effect
            )
            
            logger.info(
                "Prompt analysis completed",
                conversation_log_id=conversation_log_id,
                candidates_count=len(better_candidates),
            )
            
            return PromptAnalysisEvent(
                prompt_suggestion=prompt_suggestion,
                conversation_log_id=conversation_log_id,
                conversation_log_metadata=conversation_log_metadata,
            )
            
        except Exception as e:
            logger.error("Prompt analysis failed", error=str(e), exc_info=True)
            # Return empty suggestion on error
            # T077a: Use structured PromptCandidate objects
            error_candidates = [
                PromptCandidate(
                    type="structured",
                    prompt="",
                    reasoning="分析失敗",
                ),
                PromptCandidate(
                    type="role-play",
                    prompt="",
                    reasoning="分析失敗",
                ),
                PromptCandidate(
                    type="chain-of-thought",
                    prompt="",
                    reasoning="分析失敗",
                ),
            ]
            prompt_suggestion = PromptSuggestion(
                conversation_log_id=ev.conversation_log_id,
                original_prompt="",
                analysis=f"分析失敗：{str(e)}",
                better_candidates=error_candidates,  # Ensure at least 3 structured candidates (FR-012)
                reasoning="無法生成提示詞建議",
                expected_effect=None,  # T077b: No effect on error
            )
            return PromptAnalysisEvent(
                prompt_suggestion=prompt_suggestion,
                conversation_log_id=ev.conversation_log_id,
                conversation_log_metadata=ev.conversation_log_metadata or {},
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

    async def _evaluate_prompt_effectiveness(self, prompt: str, messages: List[Message]) -> str:
        """
        T075: Evaluate prompt effectiveness.
        
        Analyzes the given prompt and provides feedback on its effectiveness,
        clarity, and potential improvements.
        """
        # Extract context from messages for better analysis
        context_summary = self._summarize_conversation_context(messages)
        
        evaluation_prompt = f"""請分析以下使用者提示詞的有效性。

使用者提示詞：
{prompt}

對話上下文摘要：
{context_summary}

請從以下角度分析提示詞的有效性：
1. 清晰度：提示詞是否清楚表達了意圖？
2. 具體性：提示詞是否足夠具體，能引導 AI 產生有用的回應？
3. 結構：提示詞的結構是否良好（是否有明確的任務、上下文、要求）？
4. 可改進之處：提示詞有哪些可以改進的地方？

請提供詳細的分析，以正體中文撰寫。"""

        response = await self.llm.acomplete(evaluation_prompt)
        return response.text.strip()

    async def _generate_structured_alternative_prompts(
        self, original_prompt: str, messages: List[Message]
    ) -> List[PromptCandidate]:
        """
        T076, T077a: Generate at least 3 structured alternative prompt candidates (FR-012).
        
        Generates improved versions of the original prompt with different
        approaches or structures, returning structured PromptCandidate objects.
        """
        context_summary = self._summarize_conversation_context(messages)
        
        prompt_template = """請根據以下原始提示詞，生成至少 3 個改進版本的提示詞候選。

原始提示詞：
{original_prompt}

對話上下文：
{context_summary}

要求：
1. 生成至少 3 個不同的改進版本，每個版本使用不同的策略
2. 必須包含以下三種類型：
   - "structured": 結構化版本（使用清晰的步驟、格式、要求）
   - "role-play": 角色扮演版本（設定角色、情境）
   - "chain-of-thought": 思維鏈版本（引導逐步思考）
3. 每個候選應該包含：
   - type: 類型（"structured"、"role-play" 或 "chain-of-thought"）
   - prompt: 完整的改進後提示詞
   - reasoning: 為什麼這個版本更好（簡短說明）
4. 改進版本應該更清晰、更具體、更有效
5. 每個候選應該完整且可以直接使用"""

        try:
            # Format the prompt template first
            formatted_prompt = prompt_template.format(
                original_prompt=original_prompt,
                context_summary=context_summary,
            )
            
            # Try to use structured_predict first
            try:
                response = await self.llm.structured_predict(
                    PromptCandidatesResponse,
                    formatted_prompt,
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
                # structured_predict failed, fall through to JSON parsing
                logger.debug("structured_predict failed, using JSON parsing fallback", error=str(e))
            
            # Fallback: Use JSON mode with manual parsing
            json_prompt = f"""{formatted_prompt}

請以 JSON 格式返回，格式如下：
{{
  "candidates": [
    {{
      "type": "structured",
      "prompt": "改進後的提示詞",
      "reasoning": "為什麼這個版本更好"
    }},
    {{
      "type": "role-play",
      "prompt": "改進後的提示詞",
      "reasoning": "為什麼這個版本更好"
    }},
    {{
      "type": "chain-of-thought",
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
        self, original_prompt: str, messages: List[Message], needed: int
    ) -> List[PromptCandidate]:
        """Generate additional structured prompt candidates if we don't have enough."""
        context_summary = self._summarize_conversation_context(messages)
        
        prompt_template = """請根據以下原始提示詞，再生成 {needed} 個不同的改進版本。

原始提示詞：
{original_prompt}

對話上下文：
{context_summary}

要求：
1. 生成 {needed} 個與之前不同的改進版本
2. 每個版本使用不同的策略（structured、role-play、chain-of-thought 或其他）
3. 每個候選應該包含：
   - type: 類型
   - prompt: 完整的改進後提示詞
   - reasoning: 為什麼這個版本更好
4. 每個候選應該完整且可以直接使用"""

        try:
            # Format the prompt template first
            formatted_prompt = prompt_template.format(
                original_prompt=original_prompt,
                context_summary=context_summary,
                needed=needed,
            )
            
            # Try to use structured_predict first
            try:
                response = await self.llm.structured_predict(
                    PromptCandidatesResponse,
                    formatted_prompt,
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
                # structured_predict failed, fall through to JSON parsing
                logger.debug("structured_predict failed, using JSON parsing fallback", error=str(e))
            
            # Fallback: Use JSON mode with manual parsing
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
        
        # Strategy 1: Structured version
        alt1 = PromptCandidate(
            type="structured",
            prompt=f"""請根據以下要求完成任務：

任務：{original_prompt}

要求：
1. 提供詳細且完整的回答
2. 包含具體的範例或說明
3. 確保回答清晰易懂""",
            reasoning="使用結構化格式，明確列出任務和要求，讓 AI 更容易理解並產生完整的回答",
        )
        alternatives.append(alt1)
        
        # Strategy 2: Chain-of-thought version
        alt2 = PromptCandidate(
            type="chain-of-thought",
            prompt=f"""我需要完成以下任務：{original_prompt}

請按照以下步驟進行：
1. 先理解任務的核心需求
2. 提供詳細的分析和說明
3. 給出具體的建議或解決方案""",
            reasoning="使用思維鏈方式，引導 AI 逐步思考，確保回答的邏輯性和完整性",
        )
        alternatives.append(alt2)
        
        # Strategy 3: Role-play version
        alt3 = PromptCandidate(
            type="role-play",
            prompt=f"""作為一位專業的顧問，請幫助我完成以下任務：

{original_prompt}

請提供專業、詳細且實用的建議。""",
            reasoning="使用角色扮演方式，設定專業角色，讓 AI 以專業角度提供更深入的建議",
        )
        alternatives.append(alt3)
        
        return alternatives

    async def _generate_reasoning(
        self, original_prompt: str, better_candidates: List[str], messages: List[Message]
    ) -> str:
        """
        T077: Generate reasoning for why alternatives are better (FR-013).
        
        Provides detailed explanation of why each alternative prompt is better
        than the original and what improvements it offers.
        """
        context_summary = self._summarize_conversation_context(messages)
        
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
        self, original_prompt: str, better_candidates: List[PromptCandidate], messages: List[Message]
    ) -> str:
        """
        T077b: Generate expected effect description (UI/UX support).
        
        Explains what effect using the optimized prompts will have on the AI's response quality.
        """
        context_summary = self._summarize_conversation_context(messages)
        
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

    def _summarize_conversation_context(self, messages: List[Message]) -> str:
        """Summarize conversation context for prompt analysis."""
        # Extract key information from messages
        assistant_responses = [
            msg.content[:200]  # First 200 chars
            for msg in messages
            if msg.role == "assistant"
        ]
        
        if assistant_responses:
            return f"對話包含 {len(messages)} 條訊息，AI 回應摘要：{assistant_responses[0]}..."
        else:
            return f"對話包含 {len(messages)} 條訊息"

