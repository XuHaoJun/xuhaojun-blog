"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";

interface DiffHighlighterProps {
  original: string;
  optimized: string;
  className?: string;
}

/**
 * Simple diff highlighter that shows additions in the optimized text
 * Highlights words/phrases that appear in optimized but not in original
 */
export function DiffHighlighter({
  original,
  optimized,
  className,
}: DiffHighlighterProps) {
  const highlightedText = useMemo(() => {
    // Simple word-based diff algorithm
    // Split into words (preserving punctuation)
    const originalWords = original.toLowerCase().split(/\s+/);
    const optimizedWords = optimized.split(/(\s+)/);

    // Create a set of original words for quick lookup
    const originalWordSet = new Set(originalWords);

    // Highlight words that are new or significantly different
    return optimizedWords.map((word, idx) => {
      const wordLower = word.toLowerCase().trim();
      const isNewWord =
        wordLower.length > 0 &&
        !originalWordSet.has(wordLower) &&
        /[\u4e00-\u9fa5a-zA-Z]/.test(wordLower); // Only highlight meaningful words

      if (isNewWord) {
        return (
          <mark
            key={idx}
            className="bg-green-200 dark:bg-green-900/50 text-green-900 dark:text-green-100 px-1 rounded"
          >
            {word}
          </mark>
        );
      }
      return <span key={idx}>{word}</span>;
    });
  }, [original, optimized]);

  return (
    <div className={cn("font-mono text-sm leading-relaxed", className)}>
      {highlightedText}
    </div>
  );
}

