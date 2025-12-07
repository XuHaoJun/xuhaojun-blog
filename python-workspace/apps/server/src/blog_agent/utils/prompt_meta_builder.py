"""Utility for building PromptMeta from PromptSuggestion (UI/UX support)."""

from blog_agent.storage.models import PromptCandidate, PromptSuggestion


def build_prompt_meta(prompt_suggestion: PromptSuggestion) -> dict:
    """
    T085b: Build PromptMeta dictionary from PromptSuggestion for UI/UX display.
    
    Converts a PromptSuggestion model into a dictionary structure that matches
    the PromptMeta proto message format for frontend display.
    
    Args:
        prompt_suggestion: The PromptSuggestion model to convert
        
    Returns:
        Dictionary with keys: original_prompt, analysis, better_candidates, expected_effect
    """
    # Convert PromptCandidate objects to dictionaries
    candidates = [
        {
            "type": candidate.type,
            "prompt": candidate.prompt,
            "reasoning": candidate.reasoning,
        }
        for candidate in prompt_suggestion.better_candidates
    ]
    
    return {
        "original_prompt": prompt_suggestion.original_prompt,
        "analysis": prompt_suggestion.analysis,
        "better_candidates": candidates,
        "expected_effect": prompt_suggestion.expected_effect or "",
    }

