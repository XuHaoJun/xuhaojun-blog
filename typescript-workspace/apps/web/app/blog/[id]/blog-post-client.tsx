"use client";

import { useState, useEffect } from "react";
import type { BlogPost, ConversationMessage, PromptSuggestion } from "@blog-agent/proto-gen";
import { ConversationViewer } from "@/components/conversation-viewer";
import { PromptSidebar } from "@/components/prompt-sidebar";
import { PromptAccordion } from "@/components/prompt-accordion";
import { OptimizedContentViewer } from "@/components/optimized-content-viewer";
import { useIntersectionObserver } from "@/hooks/use-intersection-observer";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@blog-agent/ui/components/tabs";

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
  const [activeTab, setActiveTab] = useState<"original" | "optimized">("original");

  // Check if optimized content is available
  const hasOptimizedContent = blogPost.content && blogPost.content.trim().length > 0;

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

  // Use Intersection Observer to track active message (desktop only, only for original tab)
  const activeMessageIndex = useIntersectionObserver(messageIndicesWithPrompts, {
    enabled: messageIndicesWithPrompts.length > 0 && activeTab === "original",
  }) as number | undefined;

  const [hoveredMessageIndex, setHoveredMessageIndex] = useState<number | undefined>();
  // Track the last valid user message index to maintain sidebar content when hovering over AI messages
  const [lastValidUserMessageIndex, setLastValidUserMessageIndex] = useState<number | undefined>();

  // Determine which message to show in sidebar
  // Priority: hovered user message > active message > last valid user message
  const sidebarMessageIndex = (() => {
    // If hovering over a user message, use it
    if (hoveredMessageIndex !== undefined) {
      const hoveredMessage = conversationMessages[hoveredMessageIndex];
      if (hoveredMessage?.role === "user") {
        return hoveredMessageIndex;
      }
    }
    // Otherwise, use active message from intersection observer
    if (activeMessageIndex !== undefined) {
      return activeMessageIndex;
    }
    // Fallback to last valid user message to maintain content
    return lastValidUserMessageIndex;
  })();

  // Update last valid user message index when active message changes
  useEffect(() => {
    if (activeMessageIndex !== undefined) {
      const activeMessage = conversationMessages[activeMessageIndex];
      if (activeMessage?.role === "user") {
        setLastValidUserMessageIndex(activeMessageIndex);
      }
    }
  }, [activeMessageIndex, conversationMessages]);

  // Handle message hover - update hover state and last valid index for user messages
  const handleMessageHover = (index: number) => {
    const message = conversationMessages[index];
    setHoveredMessageIndex(index);
    // Update last valid user message index when hovering over user messages
    if (message?.role === "user") {
      setLastValidUserMessageIndex(index);
    }
  };

  const handleMessageLeave = () => {
    setHoveredMessageIndex(undefined);
    // Keep lastValidUserMessageIndex unchanged to maintain sidebar content
  };

  // Reset scroll position when switching tabs
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [activeTab]);

  // Original content view (with prompt suggestions)
  const originalContentView = (
    <div className="flex flex-col lg:flex-row gap-8">
      {/* Left Column - Original Conversation (70% on desktop, 100% on mobile) */}
      <article className="flex-1 lg:w-[70%]">
        <ConversationViewer
          messages={conversationMessages}
          conversationLogId={blogPost.conversationLogId}
          onMessageHover={handleMessageHover}
          onMessageLeave={handleMessageLeave}
          activeMessageIndex={sidebarMessageIndex}
        />

        {/* Mobile Accordion - Shows below content on mobile */}
        {promptSuggestions.length > 0 && (
          <div className="mt-8 lg:hidden">
            <PromptAccordion
              conversationMessages={conversationMessages}
              promptSuggestions={promptSuggestions}
              conversationLogId={blogPost.conversationLogId}
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
          conversationLogId={blogPost.conversationLogId}
        />
      )}
    </div>
  );

  // Optimized content view (without prompt suggestions)
  const optimizedContentView = (
    <div className="w-full">
      <OptimizedContentViewer content={blogPost.content || ""} />
    </div>
  );

  return (
    <Tabs
      value={activeTab}
      onValueChange={(value) => setActiveTab(value as "original" | "optimized")}
      className="w-full"
    >
      <TabsList className="mb-6">
        <TabsTrigger value="original">原版</TabsTrigger>
        {hasOptimizedContent && <TabsTrigger value="optimized">優化版</TabsTrigger>}
      </TabsList>

      <TabsContent value="original" className="mt-0">
        {originalContentView}
      </TabsContent>

      {hasOptimizedContent && (
        <TabsContent value="optimized" className="mt-0">
          {optimizedContentView}
        </TabsContent>
      )}
    </Tabs>
  );
}

