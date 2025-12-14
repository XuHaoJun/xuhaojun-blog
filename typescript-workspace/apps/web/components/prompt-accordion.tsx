"use client";

import { useState } from "react";
import { create } from "@bufbuild/protobuf";
import type { ConversationMessage, PromptSuggestion, PromptMeta } from "@blog-agent/proto-gen";
import { PromptMetaSchema } from "@blog-agent/proto-gen";
import { PromptCard } from "./prompt-card";
import { cn } from "@/lib/utils";

interface PromptAccordionProps {
  conversationMessages: ConversationMessage[];
  promptSuggestions: PromptSuggestion[];
  className?: string;
}

interface AccordionItemProps {
  messageIndex: number;
  message: ConversationMessage;
  promptSuggestion: PromptSuggestion;
  isOpen: boolean;
  onToggle: () => void;
}

function AccordionItem({ messageIndex, message, promptSuggestion, isOpen, onToggle }: AccordionItemProps) {
  const promptMeta: PromptMeta = create(PromptMetaSchema, {
    originalPrompt: promptSuggestion.originalPrompt,
    analysis: promptSuggestion.analysis,
    betterCandidates: promptSuggestion.betterCandidates || [],
    expectedEffect: promptSuggestion.expectedEffect || "",
  });

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full px-4 py-4 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors touch-manipulation"
        aria-expanded={isOpen}
        aria-controls={`accordion-content-${messageIndex}`}
      >
        <div className="flex items-center gap-3 flex-1">
          <span className="text-2xl" role="img" aria-label="提示詞優化建議">
            💡
          </span>
          <span className="font-medium text-gray-900 dark:text-white">
            查看此訊息的 Prompt 技巧
          </span>
        </div>
        <svg
          className={cn(
            "w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform duration-200",
            isOpen && "rotate-180"
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      <div
        id={`accordion-content-${messageIndex}`}
        className={cn(
          "overflow-hidden transition-all duration-300 ease-in-out",
          isOpen
            ? "max-h-[5000px] opacity-100"
            : "max-h-0 opacity-0"
        )}
      >
        <div
          className={cn(
            "px-4 pb-4 transition-transform duration-300",
            isOpen ? "translate-y-0" : "-translate-y-2"
          )}
        >
          <PromptCard promptMeta={promptMeta} />
        </div>
      </div>
    </div>
  );
}

export function PromptAccordion({
  conversationMessages,
  promptSuggestions,
  className,
}: PromptAccordionProps) {
  const [openIndices, setOpenIndices] = useState<Set<number>>(new Set());

  const toggleIndex = (index: number) => {
    setOpenIndices((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  // Find user messages with associated prompt suggestions
  const messagesWithPrompts = conversationMessages
    .map((msg, index) => {
      if (msg.role === "user") {
        const matchingPrompt = promptSuggestions.find(
          (ps) => ps.originalPrompt === msg.content || ps.originalPrompt.trim() === msg.content.trim()
        );
        return matchingPrompt ? { index, message: msg, promptSuggestion: matchingPrompt } : null;
      }
      return null;
    })
    .filter((item): item is { index: number; message: ConversationMessage; promptSuggestion: PromptSuggestion } => item !== null);

  if (messagesWithPrompts.length === 0) {
    return null;
  }

  return (
    <div className={cn("lg:hidden", className)}>
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            💡 Prompt 診斷室
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            點擊展開查看各訊息的 Prompt 優化建議
          </p>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {messagesWithPrompts.map(({ index, message, promptSuggestion }) => (
            <AccordionItem
              key={index}
              messageIndex={index}
              message={message}
              promptSuggestion={promptSuggestion}
              isOpen={openIndices.has(index)}
              onToggle={() => toggleIndex(index)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

