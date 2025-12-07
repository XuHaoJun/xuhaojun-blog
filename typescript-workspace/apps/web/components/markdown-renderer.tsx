"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ContentBlock } from "@blog-agent/proto-gen";

interface MarkdownRendererProps {
  content: string;
  contentBlocks?: ContentBlock[];
}

export function MarkdownRenderer({
  content,
  contentBlocks = [],
}: MarkdownRendererProps) {
  // If we have content blocks, render them with their associated prompt metadata
  // Otherwise, just render the content as markdown
  if (contentBlocks.length > 0) {
    return (
      <div className="space-y-6">
        {contentBlocks.map((block) => (
          <div key={block.id} id={`block-${block.id}`} className="content-block">
            <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose">
              {block.text}
            </ReactMarkdown>
            {block.promptMeta && (
              <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  💡 此段落有對應的 Prompt 優化建議（將在 Phase 11 實作）
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  // Fallback to rendering the full content as markdown
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose">
      {content}
    </ReactMarkdown>
  );
}

