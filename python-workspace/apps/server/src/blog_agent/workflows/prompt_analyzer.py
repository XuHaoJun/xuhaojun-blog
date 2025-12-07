"""Prompt analysis workflow step for optimization suggestions."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from llama_index.core.workflow import Event, step

if TYPE_CHECKING:
    from blog_agent.workflows.extractor import ExtractEvent, ExtractStartEvent

from blog_agent.services.llm_service import get_llm_service
from blog_agent.storage.models import Message, PromptSuggestion
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class PromptAnalysisEvent(Event):
    """Event containing prompt analysis results."""

    prompt_suggestion: PromptSuggestion
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None


class PromptAnalyzer:
    """Prompt analysis step for analyzing user prompts and suggesting improvements."""

    def __init__(self, llm_service=None):
        """Initialize prompt analyzer."""
        self.llm_service = llm_service or get_llm_service()

    @step
    async def analyze(self, ev: "ExtractStartEvent") -> PromptAnalysisEvent:  # type: ignore
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
                prompt_suggestion = PromptSuggestion(
                    conversation_log_id=conversation_log_id,
                    original_prompt="",
                    analysis="未找到使用者提示詞",
                    better_candidates=["", "", ""],  # Ensure at least 3 empty strings to satisfy FR-012
                    reasoning="對話紀錄中沒有使用者提示詞可供分析",
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
            better_candidates = await self._generate_alternative_prompts(primary_prompt, messages)
            
            # Ensure we have at least 3 candidates (FR-012)
            if len(better_candidates) < 3:
                logger.warning(
                    "Generated fewer than 3 prompt candidates, generating more",
                    count=len(better_candidates),
                    conversation_log_id=conversation_log_id,
                )
                additional_candidates = await self._generate_additional_candidates(
                    primary_prompt, messages, needed=3 - len(better_candidates)
                )
                better_candidates.extend(additional_candidates)
            
            # Ensure we have at least 3 candidates (use fallback if needed)
            if len(better_candidates) < 3:
                fallback = await self._generate_fallback_alternatives(primary_prompt)
                better_candidates.extend(fallback)
                better_candidates = better_candidates[:10]  # Limit to 10
            
            # T077: Generate reasoning for why alternatives are better (FR-013)
            reasoning = await self._generate_reasoning(primary_prompt, better_candidates, messages)
            
            prompt_suggestion = PromptSuggestion(
                conversation_log_id=conversation_log_id,
                original_prompt=primary_prompt,
                analysis=effectiveness_analysis,
                better_candidates=better_candidates[:10],  # Limit to 10, but ensure at least 3
                reasoning=reasoning,
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
            prompt_suggestion = PromptSuggestion(
                conversation_log_id=ev.conversation_log_id,
                original_prompt="",
                analysis=f"分析失敗：{str(e)}",
                better_candidates=["", "", ""],  # Ensure at least 3 to satisfy FR-012
                reasoning="無法生成提示詞建議",
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
            response = await self.llm_service.generate(prompt)
            # Try to parse JSON response
            import json
            prompts = json.loads(response.strip())
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

        response = await self.llm_service.generate(evaluation_prompt)
        return response.strip()

    async def _generate_alternative_prompts(
        self, original_prompt: str, messages: List[Message]
    ) -> List[str]:
        """
        T076: Generate at least 3 alternative prompt candidates (FR-012).
        
        Generates improved versions of the original prompt with different
        approaches or structures.
        """
        context_summary = self._summarize_conversation_context(messages)
        
        generation_prompt = f"""請根據以下原始提示詞，生成至少 3 個改進版本的提示詞候選。

原始提示詞：
{original_prompt}

對話上下文：
{context_summary}

要求：
1. 生成至少 3 個不同的改進版本
2. 每個版本應該採用不同的策略或結構
3. 改進版本應該更清晰、更具體、更有效
4. 可以嘗試不同的提示詞技巧（如：角色扮演、步驟分解、範例引導等）
5. 每個候選應該完整且可以直接使用

請以 JSON 陣列格式返回，例如：["改進版本1", "改進版本2", "改進版本3", ...]

請只輸出 JSON 陣列，不要額外說明。"""

        try:
            response = await self.llm_service.generate(generation_prompt)
            import json
            candidates = json.loads(response.strip())
            if isinstance(candidates, list):
                # Filter and clean candidates
                cleaned = [c for c in candidates if isinstance(c, str) and len(c) > 20]
                return cleaned[:10]  # Limit to 10 candidates
        except Exception as e:
            logger.warning("Failed to parse alternative prompts", error=str(e))
        
        # Fallback: generate simple alternatives
        return await self._generate_fallback_alternatives(original_prompt)

    async def _generate_additional_candidates(
        self, original_prompt: str, messages: List[Message], needed: int
    ) -> List[str]:
        """Generate additional prompt candidates if we don't have enough."""
        context_summary = self._summarize_conversation_context(messages)
        
        generation_prompt = f"""請根據以下原始提示詞，再生成 {needed} 個不同的改進版本。

原始提示詞：
{original_prompt}

對話上下文：
{context_summary}

要求：
1. 生成 {needed} 個與之前不同的改進版本
2. 嘗試不同的提示詞技巧或結構
3. 每個候選應該完整且可以直接使用

請以 JSON 陣列格式返回，例如：["改進版本1", "改進版本2", ...]

請只輸出 JSON 陣列，不要額外說明。"""

        try:
            response = await self.llm_service.generate(generation_prompt)
            import json
            candidates = json.loads(response.strip())
            if isinstance(candidates, list):
                return [c for c in candidates if isinstance(c, str) and len(c) > 20]
        except Exception as e:
            logger.warning("Failed to generate additional candidates", error=str(e))
        
        return []

    async def _generate_fallback_alternatives(self, original_prompt: str) -> List[str]:
        """Generate simple fallback alternatives if LLM generation fails."""
        alternatives = []
        
        # Strategy 1: Add structure
        alt1 = f"""請根據以下要求完成任務：

任務：{original_prompt}

要求：
1. 提供詳細且完整的回答
2. 包含具體的範例或說明
3. 確保回答清晰易懂"""
        alternatives.append(alt1)
        
        # Strategy 2: Add context and steps
        alt2 = f"""我需要完成以下任務：{original_prompt}

請按照以下步驟進行：
1. 先理解任務的核心需求
2. 提供詳細的分析和說明
3. 給出具體的建議或解決方案"""
        alternatives.append(alt2)
        
        # Strategy 3: Role-based
        alt3 = f"""作為一位專業的顧問，請幫助我完成以下任務：

{original_prompt}

請提供專業、詳細且實用的建議。"""
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

        response = await self.llm_service.generate(reasoning_prompt)
        return response.strip()

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

