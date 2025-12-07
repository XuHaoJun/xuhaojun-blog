"use client";

import { useState } from "react";
import type { ContentBlock, PromptMeta } from "@blog-agent/proto-gen";
import { PromptCard } from "./prompt-card";
import { cn } from "@/lib/utils";

interface PromptAccordionProps {
  contentBlocks: ContentBlock[];
  className?: string;
}

interface AccordionItemProps {
  block: ContentBlock;
  isOpen: boolean;
  onToggle: () => void;
}

function AccordionItem({ block, isOpen, onToggle }: AccordionItemProps) {
  if (!block.promptMeta) {
    return null;
  }

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full px-4 py-4 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors touch-manipulation"
        aria-expanded={isOpen}
        aria-controls={`accordion-content-${block.id}`}
      >
        <div className="flex items-center gap-3 flex-1">
          <span className="text-2xl" role="img" aria-label="提示詞優化建議">
            💡
          </span>
          <span className="font-medium text-gray-900 dark:text-white">
            查看此段落的 Prompt 技巧
          </span>
        </div>
        <svg
          className={cn(
            "w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform duration-200",
            isOpen && "rotate-180"
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      <div
        id={`accordion-content-${block.id}`}
        className={cn(
          "overflow-hidden transition-all duration-300 ease-in-out",
          isOpen
            ? "max-h-[5000px] opacity-100"
            : "max-h-0 opacity-0"
        )}
      >
        <div
          className={cn(
            "px-4 pb-4 transition-transform duration-300",
            isOpen ? "translate-y-0" : "-translate-y-2"
          )}
        >
          <PromptCard promptMeta={block.promptMeta} />
        </div>
      </div>
    </div>
  );
}

export function PromptAccordion({
  contentBlocks,
  className,
}: PromptAccordionProps) {
  const [openBlocks, setOpenBlocks] = useState<Set<string>>(new Set());

  const toggleBlock = (blockId: string) => {
    setOpenBlocks((prev) => {
      const next = new Set(prev);
      if (next.has(blockId)) {
        next.delete(blockId);
      } else {
        next.add(blockId);
      }
      return next;
    });
  };

  const blocksWithPrompts = contentBlocks.filter(
    (block) => block.promptMeta
  );

  if (blocksWithPrompts.length === 0) {
    return null;
  }

  return (
    <div className={cn("lg:hidden", className)}>
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            💡 Prompt 診斷室
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            點擊展開查看各段落的 Prompt 優化建議
          </p>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {blocksWithPrompts.map((block) => (
            <AccordionItem
              key={block.id}
              block={block}
              isOpen={openBlocks.has(block.id)}
              onToggle={() => toggleBlock(block.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

