"use client";

import { MyReactMarkdown } from "./my-react-markdown";

interface OptimizedContentViewerProps {
  content: string;
}

export function OptimizedContentViewer({ content }: OptimizedContentViewerProps) {
  // Handle empty or null content
  if (!content || content.trim().length === 0) {
    return (
      <div className="prose prose-lg dark:prose-invert max-w-none font-serif">
        <p className="text-muted-foreground">優化內容不可用</p>
      </div>
    );
  }

  try {
    return (
      <div className="prose prose-lg dark:prose-invert max-w-none font-serif">
        <MyReactMarkdown content={content} />
      </div>
    );
  } catch (error) {
    // Fallback for malformed Markdown
    console.error("Failed to render optimized content:", error);
    return (
      <div className="prose prose-lg dark:prose-invert max-w-none font-serif">
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
          <p className="text-destructive font-semibold">內容渲染錯誤</p>
          <p className="text-sm text-muted-foreground mt-2">
            無法正確渲染優化內容，請查看原始內容。
          </p>
        </div>
        <pre className="mt-4 overflow-x-auto rounded-lg bg-muted p-4 text-sm">
          {content}
        </pre>
      </div>
    );
  }
}
