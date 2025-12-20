"use client";

import { create } from "@bufbuild/protobuf";
import type { ConversationMessage, PromptSuggestion, PromptMeta } from "@blog-agent/proto-gen";
import { PromptMetaSchema } from "@blog-agent/proto-gen";
import { PromptCard } from "./prompt-card";
import { cn } from "@/lib/utils";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@blog-agent/ui/components/accordion";

interface PromptAccordionProps {
  conversationMessages: ConversationMessage[];
  promptSuggestions: PromptSuggestion[];
  className?: string;
  conversationLogId?: string;
}

export function PromptAccordion({
  conversationMessages,
  promptSuggestions,
  className,
  conversationLogId,
}: PromptAccordionProps) {
  // Find user messages with associated prompt suggestions
  const messagesWithPrompts = conversationMessages
    .map((msg, index) => {
      if (msg.role === "user") {
        const matchingPrompt = promptSuggestions.find(
          (ps) => ps.originalPrompt === msg.content || ps.originalPrompt.trim() === msg.content.trim()
        );
        return matchingPrompt ? { index, message: msg, promptSuggestion: matchingPrompt } : null;
      }
      return null;
    })
    .filter((item): item is { index: number; message: ConversationMessage; promptSuggestion: PromptSuggestion } => item !== null);

  if (messagesWithPrompts.length === 0) {
    return null;
  }

  return (
    <div className={cn("lg:hidden", className)}>
      <div className="bg-card text-card-foreground rounded-lg border shadow-sm overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">
            💡 Prompt 診斷室
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            查看各訊息的 Prompt 優化建議
          </p>
        </div>
        
        <Accordion type="multiple" className="w-full">
          {messagesWithPrompts.map(({ index, message, promptSuggestion }) => {
            const promptMeta: PromptMeta = create(PromptMetaSchema, {
              originalPrompt: promptSuggestion.originalPrompt,
              analysis: promptSuggestion.analysis,
              betterCandidates: promptSuggestion.betterCandidates || [],
              expectedEffect: promptSuggestion.expectedEffect || "",
            });

            return (
              <AccordionItem key={index} value={`item-${index}`} className="border-b last:border-b-0 px-4">
                <AccordionTrigger className="hover:no-underline py-4">
                  <div className="flex items-center gap-3 text-left">
                    <span className="text-2xl" role="img" aria-label="提示詞優化建議">
                      💡
                    </span>
                    <span className="font-medium">
                      查看訊息 #{index + 1} 的技巧
                    </span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-4">
                  <div className="pt-2">
                    <PromptCard 
                      promptMeta={promptMeta} 
                      messages={conversationMessages}
                      conversationLogId={conversationLogId}
                      activeMessageIndex={index}
                    />
                  </div>
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      </div>
    </div>
  );
}
