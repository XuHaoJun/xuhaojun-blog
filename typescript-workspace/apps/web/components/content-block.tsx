"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ContentBlock as ContentBlockType } from "@blog-agent/proto-gen";
import { cn } from "@/lib/utils";
import rehypePrismPlus from "rehype-prism-plus";

interface ContentBlockProps {
  block: ContentBlockType;
  onHover?: () => void;
  onLeave?: () => void;
  isActive?: boolean;
}

export function ContentBlock({ block, onHover, onLeave, isActive = false }: ContentBlockProps) {
  return (
    <div
      id={`block-${block.id}`}
      className={cn(
        "content-block relative group transition-all duration-300",
        isActive &&
          "ring-2 ring-blue-500 dark:ring-blue-400 ring-offset-2 dark:ring-offset-gray-900 rounded-lg bg-blue-50/50 dark:bg-blue-900/10"
      )}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
    >
      {/* Anchor icon - appears on hover */}
      {block.promptMeta && (
        <div className="absolute -left-8 top-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:scale-110">
          <span className="text-2xl" role="img" aria-label="提示詞優化建議">
            💡
          </span>
        </div>
      )}

      {/* Content */}
      <div className="prose prose-lg dark:prose-invert max-w-none font-serif transition-colors duration-300">
        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypePrismPlus]}>
          {block.text}
        </ReactMarkdown>
      </div>
    </div>
  );
}
