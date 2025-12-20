"use client";

import { useEffect, useRef, useState } from "react";
import { create } from "@bufbuild/protobuf";
import type { ConversationMessage, PromptSuggestion, PromptMeta } from "@blog-agent/proto-gen";
import { PromptMetaSchema } from "@blog-agent/proto-gen";
import { PromptCard } from "./prompt-card";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@blog-agent/ui/components/scroll-area";
import { Lightbulb } from "lucide-react";

interface PromptSidebarProps {
  conversationMessages: ConversationMessage[];
  promptSuggestions: PromptSuggestion[];
  activeMessageIndex?: number;
  className?: string;
  conversationLogId?: string;
}

export function PromptSidebar({
  conversationMessages,
  promptSuggestions,
  activeMessageIndex,
  className,
  conversationLogId,
}: PromptSidebarProps) {
  const sidebarRef = useRef<HTMLDivElement>(null);
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
        setIsAnimating(true);
        
        const timer = setTimeout(() => {
          setDisplayPromptMeta(newPromptMeta);
          setDisplayMessageNumber(messageNumber);
          setIsAnimating(false);
          previousOriginalPromptRef.current = newPromptMeta.originalPrompt;
        }, 250);

        return () => clearTimeout(timer);
      } else {
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
      // Find the viewport of ScrollArea to scroll
      const viewport = sidebarRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (viewport) {
        viewport.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  }, [activeMessageIndex]);

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
      className={cn(
        "hidden lg:block w-full lg:w-[30%] lg:sticky lg:top-8 lg:self-start lg:h-[calc(100vh-4rem)]",
        className
      )}
    >
      <ScrollArea className="h-full w-full pr-4" ref={sidebarRef}>
        <div className="space-y-6 pb-8">
          <div className="flex items-center gap-2 px-1">
            <Lightbulb className="w-5 h-5 text-primary" />
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              Prompt 診斷室
            </h2>
          </div>

          {!activePromptSuggestion ? (
            <div className="bg-muted/30 rounded-xl border border-dashed border-muted-foreground/20 p-8 text-center animate-in fade-in duration-500">
              <p className="text-sm text-muted-foreground leading-relaxed">
                捲動文章以查看對應的<br />
                <span className="font-semibold text-foreground/80">Prompt 優化建議</span>
              </p>
            </div>
          ) : (
            displayPromptMeta && (
              <div 
                className={cn(
                  "transition-all duration-500 ease-in-out",
                  isAnimating 
                    ? "opacity-0 translate-y-4 scale-95 blur-sm" 
                    : "opacity-100 translate-y-0 scale-100 blur-0"
                )}
              >
                <PromptCard 
                  promptMeta={displayPromptMeta} 
                  messageNumber={displayMessageNumber}
                  onScrollToMessage={handleScrollToMessage}
                  messages={conversationMessages}
                  conversationLogId={conversationLogId}
                  activeMessageIndex={activeMessageIndex}
                />
              </div>
            )
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}
