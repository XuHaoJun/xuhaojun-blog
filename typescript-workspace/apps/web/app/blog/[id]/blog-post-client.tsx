"use client";

import { useState } from "react";
import type { BlogPost, ContentBlock } from "@blog-agent/proto-gen";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { PromptSidebar } from "@/components/prompt-sidebar";
import { useIntersectionObserver } from "@/hooks/use-intersection-observer";

interface BlogPostClientProps {
  blogPost: BlogPost;
  contentBlocks: ContentBlock[];
}

export function BlogPostClient({
  blogPost,
  contentBlocks,
}: BlogPostClientProps) {
  // Extract block IDs that have prompt metadata
  const blockIds = contentBlocks
    .filter((block) => block.promptMeta)
    .map((block) => block.id);

  // Use Intersection Observer to track active block
  const activeBlockId = useIntersectionObserver(blockIds, {
    enabled: blockIds.length > 0,
  });

  const [hoveredBlockId, setHoveredBlockId] = useState<string | undefined>();

  // Determine which block to show in sidebar (hover takes priority)
  const sidebarBlockId = hoveredBlockId || activeBlockId;

  return (
    <div className="flex flex-col lg:flex-row gap-8">
      {/* Left Column - Article Content (70% on desktop) */}
      <article className="flex-1 lg:w-[70%]">
        <div className="prose prose-lg dark:prose-invert max-w-none">
          <MarkdownRenderer
            content={blogPost.content || ""}
            contentBlocks={contentBlocks}
            activeBlockId={sidebarBlockId}
            onBlockHover={(blockId) => setHoveredBlockId(blockId)}
            onBlockLeave={() => setHoveredBlockId(undefined)}
          />
        </div>
      </article>

      {/* Right Column - Prompt Sidebar (30% on desktop, hidden on mobile) */}
      {blockIds.length > 0 && (
        <PromptSidebar
          contentBlocks={contentBlocks}
          activeBlockId={sidebarBlockId}
        />
      )}
    </div>
  );
}

