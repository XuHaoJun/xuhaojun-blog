"use client";

import { useState } from "react";
import type { ConversationMessage } from "@blog-agent/proto-gen";
import { cn } from "@/lib/utils";
import { MyReactMarkdown } from "./my-react-markdown";
import { User, Bot } from "lucide-react";
import { useCopyActions } from "@/hooks/use-copy-actions";
import { CopyDropdown } from "./copy-dropdown";
import { Badge } from "@blog-agent/ui/components/badge";
import { CompressionLimitForm } from "./compression-limit-form";

interface ConversationViewerProps {
  messages: ConversationMessage[];
  conversationLogId?: string;
  onMessageHover?: (index: number) => void;
  onMessageLeave?: () => void;
  activeMessageIndex?: number;
}

export function ConversationViewer({
  messages,
  conversationLogId,
  onMessageHover,
  onMessageLeave,
  activeMessageIndex,
}: ConversationViewerProps) {
  const {
    isFormOpen,
    setIsFormOpen,
    isCompressing,
    copyCurrentMessage,
    copyOriginal,
    startCompressedCopy,
    handleCompressedSubmit,
  } = useCopyActions({ messages, conversationLogId });

  if (messages.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-12 bg-muted/20 rounded-lg border-2 border-dashed">
        沒有對話內容
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {messages.map((msg, index) => {
        const isUser = msg.role === "user";
        const isActive = activeMessageIndex === index;

        return (
          <div
            key={index}
            id={`message-${index}`}
            className={cn(
              "p-5 rounded-xl transition-all duration-300 relative group border-2",
              isUser
                ? "bg-blue-50/50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-900/30 shadow-sm"
                : "bg-background border-muted shadow-sm",
              isActive &&
                "ring-2 ring-primary ring-offset-2 dark:ring-offset-background z-10 scale-[1.01]"
            )}
            onMouseEnter={() => onMessageHover?.(index)}
            onMouseLeave={onMessageLeave}
          >
            {/* Role label and actions */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {isUser ? (
                  <Badge
                    variant="outline"
                    className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800 gap-1.5 px-2 py-0.5"
                  >
                    <User className="w-3.5 h-3.5" /> 使用者
                  </Badge>
                ) : (
                  <Badge
                    variant="outline"
                    className="bg-muted text-foreground border-muted-foreground/20 gap-1.5 px-2 py-0.5"
                  >
                    <Bot className="w-3.5 h-3.5" /> AI
                  </Badge>
                )}
                <span className="text-xs text-muted-foreground font-mono">#{index + 1}</span>
              </div>

              {/* Actions overlay */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <CopyDropdown
                  onCopyCurrent={() => copyCurrentMessage(index)}
                  onCopyOriginal={() => copyOriginal(index)}
                  onCopyCompressed={() => startCompressedCopy(index)}
                />
              </div>
            </div>

            {/* Message content */}
            <div className="prose prose-slate dark:prose-invert max-w-none font-serif leading-relaxed">
              <MyReactMarkdown content={msg.content} />
            </div>

            {/* Timestamp (if available) */}
            {msg.timestamp && (
              <div className="text-[10px] text-muted-foreground mt-4 text-right tabular-nums opacity-60">
                {new Date(msg.timestamp).toLocaleString("zh-TW")}
              </div>
            )}
          </div>
        );
      })}

      <CompressionLimitForm
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        onSubmit={handleCompressedSubmit}
        isLoading={isCompressing}
      />
    </div>
  );
}
