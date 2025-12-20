"use client";

import { useState } from "react";
import type { PromptMeta, ConversationMessage } from "@blog-agent/proto-gen";
import { cn } from "@/lib/utils";
import { MyReactMarkdown } from "./my-react-markdown";
import { useCopyActions } from "@/hooks/use-copy-actions";
import { CopyDropdown } from "./copy-dropdown";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@blog-agent/ui/components/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@blog-agent/ui/components/tabs";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@blog-agent/ui/components/collapsible";
import { Button } from "@blog-agent/ui/components/button";
import { Badge } from "@blog-agent/ui/components/badge";
import { Search, User, MessageSquare, ChevronDown, ChevronUp, Rocket } from "lucide-react";
import { toast } from "sonner";

interface PromptCardProps {
  promptMeta: PromptMeta;
  className?: string;
  messageNumber?: number;
  onScrollToMessage?: () => void;
  messages?: ConversationMessage[];
  conversationLogId?: string;
  activeMessageIndex?: number;
}

export function PromptCard({
  promptMeta,
  className,
  messageNumber,
  onScrollToMessage,
  messages = [],
  conversationLogId,
  activeMessageIndex,
}: PromptCardProps) {
  const [selectedCandidateIndex, setSelectedCandidateIndex] = useState(0);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const candidates = promptMeta.betterCandidates || [];

  const {
    copyCurrentMessage,
    copyOriginal,
    startCompressedCopy,
  } = useCopyActions({ messages, conversationLogId });

  const currentCandidatePrompt = candidates[selectedCandidateIndex]?.prompt;
  const targetIndex = activeMessageIndex ?? (messageNumber ? messageNumber - 1 : -1);

  return (
    <Card className={cn("overflow-hidden border-2", className)}>
      {/* 1. 🔴 原始提問 */}
      <div className="bg-blue-50/50 dark:bg-blue-900/10 border-b">
        <div className="p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800 gap-1 px-1.5"
              >
                <User className="w-3 h-3" /> 使用者
              </Badge>
              <span className="text-xs text-muted-foreground font-medium">原始提問</span>
            </div>
            {messageNumber !== undefined && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onScrollToMessage}
                className="h-6 px-2 text-xs text-muted-foreground hover:text-primary"
              >
                #{messageNumber} 跳至訊息
              </Button>
            )}
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none font-serif text-sm">
            <MyReactMarkdown content={promptMeta.originalPrompt} />
          </div>
        </div>
      </div>

      {/* 2. 🟢 優化建議 */}
      {candidates.length > 0 && (
        <div className="p-4 border-b">
          <div className="flex items-center gap-2 mb-4 text-green-700 dark:text-green-400">
            <Rocket className="w-4 h-4" />
            <span className="text-sm font-semibold">優化建議</span>
          </div>

          <Tabs
            defaultValue="0"
            className="w-full"
            onValueChange={(value) => setSelectedCandidateIndex(parseInt(value))}
          >
            {candidates.length > 1 && (
              <TabsList className="flex w-full mb-4 bg-muted/50 h-auto p-1 gap-1">
                {candidates.map((candidate, idx) => (
                  <TabsTrigger
                    key={idx}
                    value={idx.toString()}
                    className="flex-1 text-xs py-1.5 data-[state=active]:shadow-sm"
                  >
                    {getCandidateTypeLabel(candidate.type)}
                  </TabsTrigger>
                ))}
              </TabsList>
            )}

            {candidates.map((candidate, idx) => (
              <TabsContent key={idx} value={idx.toString()} className="mt-0 space-y-4">
                <div className="relative group">
                  <div className="bg-muted/30 dark:bg-muted/20 rounded-lg p-4 font-mono text-sm border border-dashed border-muted-foreground/20 leading-relaxed">
                    {candidate.prompt}
                  </div>
                  <CopyDropdown
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                    onCopyCurrent={() => copyCurrentMessage(targetIndex, candidate.prompt)}
                    onCopyOriginal={() => copyOriginal(targetIndex, candidate.prompt)}
                    onCopyCompressed={() => startCompressedCopy(targetIndex, candidate.prompt)}
                  />
                </div>

                {candidate.reasoning && (
                  <div className="flex gap-2 items-start text-xs text-muted-foreground italic bg-muted/20 p-2 rounded border-l-2 border-muted-foreground/30">
                    <MessageSquare className="w-3 h-3 mt-0.5 shrink-0" />
                    <p>{candidate.reasoning}</p>
                  </div>
                )}

                <div className="flex gap-2 pt-2">
                  <CopyDropdown
                    className="flex-1"
                    buttonVariant="default"
                    buttonSize="default"
                    buttonText="複製此優化 Prompt"
                    align="center"
                    onCopyCurrent={() => copyCurrentMessage(targetIndex, candidate.prompt)}
                    onCopyOriginal={() => copyOriginal(targetIndex, candidate.prompt)}
                    onCopyCompressed={() => startCompressedCopy(targetIndex, candidate.prompt)}
                  />
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </div>
      )}

      {/* 3. 🚀 預期效果 - 緊跟在建議之後 */}
      {promptMeta.expectedEffect && (
        <div className="px-4 py-3 bg-green-50/20 dark:bg-green-900/5 border-b italic">
          <div className="flex items-center gap-2 mb-1 opacity-70 text-green-700 dark:text-green-400">
            <Rocket className="w-3 h-3" />
            <span className="text-[10px] font-bold uppercase tracking-wider">預期效果</span>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none font-serif text-sm text-muted-foreground/80">
            <MyReactMarkdown content={promptMeta.expectedEffect} />
          </div>
        </div>
      )}

      {/* 4. 🧐 AI 診斷 - 放到最後並改為摺疊 */}
      {promptMeta.analysis && (
        <Collapsible open={isAnalysisOpen} onOpenChange={setIsAnalysisOpen} className="w-full">
          <CollapsibleTrigger asChild>
            <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-amber-50/50 dark:hover:bg-amber-900/10 transition-colors bg-amber-50/30 dark:bg-amber-900/5">
              <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                <Search className="w-4 h-4" />
                <span className="text-sm font-semibold">為什麼這樣改？(AI 診斷)</span>
              </div>
              {isAnalysisOpen ? (
                <ChevronUp className="w-4 h-4 text-amber-600" />
              ) : (
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-amber-600/70 font-medium">查看深度分析</span>
                  <ChevronDown className="w-4 h-4 text-amber-600" />
                </div>
              )}
            </div>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="p-4 pt-0 bg-amber-50/30 dark:bg-amber-900/5 border-t border-amber-100/50 dark:border-amber-900/20">
              <div className="prose prose-sm dark:prose-invert max-w-none font-serif text-sm text-muted-foreground py-4">
                <MyReactMarkdown content={promptMeta.analysis} />
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      )}
    </Card>
  );
}

function getCandidateTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    structured: "結構化",
    "role-play": "角色扮演",
    "chain-of-thought": "思維鏈",
    "step-by-step": "結構化",
    "expert-persona": "角色化",
    minimalist: "簡潔化",
  };
  return labels[type] || type;
}
