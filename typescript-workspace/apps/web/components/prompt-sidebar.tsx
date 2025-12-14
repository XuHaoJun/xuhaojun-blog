"use client";

import { useEffect, useRef, useState } from "react";
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
  const sidebarRef = useRef<HTMLElement>(null);
  const previousOriginalPromptRef = useRef<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [displayPromptMeta, setDisplayPromptMeta] = useState<PromptMeta | null>(null);
  const [displayMessageNumber, setDisplayMessageNumber] = useState<number | undefined>();

  // Find the prompt suggestion for the active message
  const activeMessage = activeMessageIndex !== undefined 
    ? conversationMessages[activeMessageIndex] 
    : undefined;
  
  const activePromptSuggestion = activeMessage && activeMessage.role === "user"
    ? promptSuggestions.find(
        (ps) => ps.originalPrompt === activeMessage.content || ps.originalPrompt.trim() === activeMessage.content.trim()
      )
    : undefined;

  // Calculate message number (1-based index)
  const messageNumber = activeMessageIndex !== undefined 
    ? activeMessageIndex + 1 
    : undefined;

  // Handle animation when activeMessageIndex changes
  useEffect(() => {
    if (activePromptSuggestion) {
      const newPromptMeta: PromptMeta = create(PromptMetaSchema, {
        originalPrompt: activePromptSuggestion.originalPrompt,
        analysis: activePromptSuggestion.analysis,
        betterCandidates: activePromptSuggestion.betterCandidates || [],
        expectedEffect: activePromptSuggestion.expectedEffect || "",
      });

      // If content is changing, animate transition
      const isContentChanging = previousOriginalPromptRef.current 
        && previousOriginalPromptRef.current !== newPromptMeta.originalPrompt;

      if (isContentChanging) {
        // Start fade out animation
        setIsAnimating(true);
        
        // After fade out, update content and fade in
        const timer = setTimeout(() => {
          setDisplayPromptMeta(newPromptMeta);
          setDisplayMessageNumber(messageNumber);
          setIsAnimating(false);
          previousOriginalPromptRef.current = newPromptMeta.originalPrompt;
        }, 250); // Half of animation duration

        return () => clearTimeout(timer);
      } else {
        // First load or same content, no animation needed
        setDisplayPromptMeta(newPromptMeta);
        setDisplayMessageNumber(messageNumber);
        setIsAnimating(false);
        previousOriginalPromptRef.current = newPromptMeta.originalPrompt;
      }
    } else {
      setDisplayPromptMeta(null);
      setDisplayMessageNumber(undefined);
      setIsAnimating(false);
      previousOriginalPromptRef.current = null;
    }
  }, [activeMessageIndex, activePromptSuggestion, messageNumber]);

  // Scroll sidebar to top when activeMessageIndex changes
  useEffect(() => {
    if (activeMessageIndex !== undefined && sidebarRef.current) {
      sidebarRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [activeMessageIndex]);

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

  // Scroll to message function
  const handleScrollToMessage = () => {
    if (activeMessageIndex !== undefined) {
      const element = document.getElementById(`message-${activeMessageIndex}`);
      element?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
    }
  };

  return (
    <aside
      ref={sidebarRef}
      className={cn(
        "hidden lg:block w-full lg:w-[30%] lg:sticky lg:top-8 lg:self-start lg:max-h-[calc(100vh-4rem)] lg:overflow-y-auto",
        "scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent",
        className
      )}
    >
      <div className="space-y-5 pr-2">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 px-1">
          💡 Prompt 診斷室
        </h2>
        {displayPromptMeta && (
          <div 
            className={cn(
              "transition-all duration-500 ease-in-out",
              isAnimating 
                ? "opacity-0 translate-x-4 scale-95" 
                : "opacity-100 translate-x-0 scale-100"
            )}
          >
            <PromptCard 
              promptMeta={displayPromptMeta} 
              messageNumber={displayMessageNumber}
              onScrollToMessage={handleScrollToMessage}
            />
          </div>
        )}
      </div>
    </aside>
  );
}

