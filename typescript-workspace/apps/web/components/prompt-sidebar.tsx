"use client";

import { create } from "@bufbuild/protobuf";
import type { ConversationMessage, PromptSuggestion, PromptMeta } from "@blog-agent/proto-gen";
import { PromptMetaSchema } from "@blog-agent/proto-gen";
import { PromptCard } from "./prompt-card";
import { cn } from "@/lib/utils";

interface PromptSidebarProps {
  conversationMessages: ConversationMessage[];
  promptSuggestions: PromptSuggestion[];
  activeMessageIndex?: number;
  className?: string;
}

export function PromptSidebar({
  conversationMessages,
  promptSuggestions,
  activeMessageIndex,
  className,
}: PromptSidebarProps) {
  // Find the prompt suggestion for the active message
  const activeMessage = activeMessageIndex !== undefined 
    ? conversationMessages[activeMessageIndex] 
    : undefined;
  
  const activePromptSuggestion = activeMessage && activeMessage.role === "user"
    ? promptSuggestions.find(
        (ps) => ps.originalPrompt === activeMessage.content || ps.originalPrompt.trim() === activeMessage.content.trim()
      )
    : undefined;

  // If no active prompt suggestion, show a placeholder or nothing
  if (!activePromptSuggestion) {
    return (
      <aside
        className={cn(
          "hidden lg:block w-full lg:w-[30%] lg:sticky lg:top-8 lg:self-start",
          className
        )}
      >
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            捲動文章以查看對應的 Prompt 優化建議
          </p>
        </div>
      </aside>
    );
  }

  // Convert PromptSuggestion to PromptMeta format for PromptCard
  const promptMeta: PromptMeta = create(PromptMetaSchema, {
    originalPrompt: activePromptSuggestion.originalPrompt,
    analysis: activePromptSuggestion.analysis,
    betterCandidates: activePromptSuggestion.betterCandidates || [],
    expectedEffect: activePromptSuggestion.expectedEffect || "",
  });

  return (
    <aside
      className={cn(
        "hidden lg:block w-full lg:w-[30%] lg:sticky lg:top-8 lg:self-start lg:max-h-[calc(100vh-4rem)] lg:overflow-y-auto",
        "transition-opacity duration-300",
        className
      )}
    >
      <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          💡 Prompt 診斷室
        </h2>
        <div className="transition-all duration-300">
          <PromptCard promptMeta={promptMeta} />
        </div>
      </div>
    </aside>
  );
}

