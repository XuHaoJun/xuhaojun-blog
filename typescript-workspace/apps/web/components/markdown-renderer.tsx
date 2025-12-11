"use client";

import type { ContentBlock } from "@blog-agent/proto-gen";
import { ContentBlock as ContentBlockComponent } from "./content-block";
import { MyReactMarkdown } from "./my-react-markdown";

interface MarkdownRendererProps {
  content: string;
  contentBlocks?: ContentBlock[];
  activeBlockId?: string;
  onBlockHover?: (blockId: string) => void;
  onBlockLeave?: () => void;
}

export function MarkdownRenderer({
  content,
  contentBlocks = [],
  activeBlockId,
  onBlockHover,
  onBlockLeave,
}: MarkdownRendererProps) {
  // Content blocks are no longer used - system displays original conversation content instead
  // This component now only serves as a fallback for legacy content
  // Fallback to rendering the full content as markdown
  return (
    <div className="prose prose-lg dark:prose-invert max-w-none font-serif">
      <MyReactMarkdown content={content} />
    </div>
  );
}
