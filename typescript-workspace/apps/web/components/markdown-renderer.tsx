"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ContentBlock } from "@blog-agent/proto-gen";
import { ContentBlock as ContentBlockComponent } from "./content-block";
import rehypePrismPlus from 'rehype-prism-plus';

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
  // If we have content blocks, render them with their associated prompt metadata
  // Otherwise, just render the content as markdown
  if (contentBlocks.length > 0) {
    return (
      <div className="space-y-8">
        {contentBlocks.map((block) => (
          <ContentBlockComponent
            key={block.id}
            block={block}
            isActive={block.id === activeBlockId}
            onHover={() => onBlockHover?.(block.id)}
            onLeave={onBlockLeave}
          />
        ))}
      </div>
    );
  }

  // Fallback to rendering the full content as markdown
  return (
    <div className="prose prose-lg dark:prose-invert max-w-none font-serif">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypePrismPlus]}>{content}</ReactMarkdown>
    </div>
  );
}

