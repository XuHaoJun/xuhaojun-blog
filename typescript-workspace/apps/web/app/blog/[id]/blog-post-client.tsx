"use client";

import { useState } from "react";
import type { BlogPost, ConversationMessage, PromptSuggestion } from "@blog-agent/proto-gen";
import { ConversationViewer } from "@/components/conversation-viewer";
import { PromptSidebar } from "@/components/prompt-sidebar";
import { PromptAccordion } from "@/components/prompt-accordion";
import { useIntersectionObserver } from "@/hooks/use-intersection-observer";

interface BlogPostClientProps {
  blogPost: BlogPost;
  conversationMessages: ConversationMessage[];
  promptSuggestions: PromptSuggestion[];
}

export function BlogPostClient({
  blogPost,
  conversationMessages,
  promptSuggestions,
}: BlogPostClientProps) {
  // Find message indices that have associated prompt suggestions
  // Match by comparing original_prompt with user message content
  const messageIndicesWithPrompts = conversationMessages
    .map((msg, index) => {
      if (msg.role === "user") {
        const hasMatchingPrompt = promptSuggestions.some(
          (ps) => ps.originalPrompt === msg.content || ps.originalPrompt.trim() === msg.content.trim()
        );
        return hasMatchingPrompt ? index : null;
      }
      return null;
    })
    .filter((idx): idx is number => idx !== null);

  // Use Intersection Observer to track active message (desktop only)
  const activeMessageIndex = useIntersectionObserver(messageIndicesWithPrompts, {
    enabled: messageIndicesWithPrompts.length > 0,
  }) as number | undefined;

  const [hoveredMessageIndex, setHoveredMessageIndex] = useState<number | undefined>();

  // Determine which message to show in sidebar (hover takes priority)
  const sidebarMessageIndex = hoveredMessageIndex !== undefined ? hoveredMessageIndex : activeMessageIndex;

  return (
    <div className="flex flex-col lg:flex-row gap-8">
      {/* Left Column - Original Conversation (70% on desktop, 100% on mobile) */}
      <article className="flex-1 lg:w-[70%]">
        <ConversationViewer
          messages={conversationMessages}
          onMessageHover={(index) => setHoveredMessageIndex(index)}
          onMessageLeave={() => setHoveredMessageIndex(undefined)}
          activeMessageIndex={sidebarMessageIndex}
        />

        {/* Mobile Accordion - Shows below content on mobile */}
        {promptSuggestions.length > 0 && (
          <div className="mt-8 lg:hidden">
            <PromptAccordion
              conversationMessages={conversationMessages}
              promptSuggestions={promptSuggestions}
            />
          </div>
        )}
      </article>

      {/* Right Column - Prompt Sidebar (30% on desktop, hidden on mobile) */}
      {promptSuggestions.length > 0 && (
        <PromptSidebar
          conversationMessages={conversationMessages}
          promptSuggestions={promptSuggestions}
          activeMessageIndex={sidebarMessageIndex}
        />
      )}
    </div>
  );
}

