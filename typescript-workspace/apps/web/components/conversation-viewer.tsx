"use client";

import { useState } from "react";
import type { ConversationMessage } from "@blog-agent/proto-gen";
import { cn } from "@/lib/utils";
import { MyReactMarkdown } from "./my-react-markdown";
import { Copy, MoreVertical } from "lucide-react";
import { formatConversationContext } from "@/lib/context-formatter";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@blog-agent/ui/components/dropdown-menu";
import { createBlogAgentClient } from "@blog-agent/rpc-client";
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
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isCompressing, setIsCompressing] = useState(false);
  const [targetIndex, setTargetIndex] = useState<number | null>(null);

  const handleCopyOriginal = (index: number) => {
    const messagesToCopy = messages.slice(0, index + 1);
    const formattedContext = formatConversationContext(messagesToCopy);
    
    if (formattedContext) {
      navigator.clipboard.writeText(formattedContext);
      toast.success("已複製原始對話內容");
    }
  };

  const handleCompressedCopyRequest = (index: number) => {
    setTargetIndex(index);
    setIsFormOpen(true);
  };

  const handleCompressedSubmit = async (limit: number) => {
    if (!conversationLogId || targetIndex === null) return;

    setIsCompressing(true);
    try {
      const client = createBlogAgentClient({
        baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:50051"
      });

      const response = await client.extractConversationFacts({
        conversationLogId,
        maxCharacters: limit,
        upToMessageIndex: targetIndex,
      });

      if (response.extractedFacts) {
        const header = `以下是我們之前對話的重點事實摘要，請作為背景參考，並根據最後的 <Task> 進行回覆。`;
        const historyBlock = `<History>\n${response.extractedFacts}\n</History>`;
        const taskMessage = messages[targetIndex];
        
        if (!taskMessage) {
          toast.error("找不到目標訊息");
          return;
        }

        const taskBlock = `<Task>\n${taskMessage.content}\n</Task>`;
        
        const fullPackage = `${header}\n\n${historyBlock}\n\n${taskBlock}`;
        
        await navigator.clipboard.writeText(fullPackage);
        
        if (response.limitExceeded) {
          toast.warning(`已複製摘要內容，但已超過 ${limit} 字限制，已提供最佳壓縮版本`);
        } else {
          toast.success("已複製事實提取後的摘要內容");
        }
        setIsFormOpen(false);
      }
    } catch (error) {
      console.error("Fact extraction failed:", error);
      toast.error("事實提取失敗，請稍後再試");
    } finally {
      setIsCompressing(false);
    }
  };

  if (messages.length === 0) {
    return (
      <div className="text-center text-gray-500 dark:text-gray-400 py-8">
        沒有對話內容
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((msg, index) => {
        const isUser = msg.role === "user";
        const isActive = activeMessageIndex === index;

        return (
          <div
            key={index}
            id={`message-${index}`}
            className={cn(
              "p-4 rounded-lg transition-all duration-300 relative group",
              isUser
                ? "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
                : "bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
              isActive &&
                "ring-2 ring-blue-500 dark:ring-blue-400 ring-offset-2 dark:ring-offset-gray-900"
            )}
            onMouseEnter={() => onMessageHover?.(index)}
            onMouseLeave={onMessageLeave}
          >
            {/* Actions overlay */}
            <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleCopyOriginal(index)}
                className="p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors"
                title="複製原始對話"
              >
                <Copy className="w-4 h-4" />
              </button>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem 
                    className="cursor-pointer"
                    onClick={() => handleCompressedCopyRequest(index)}
                  >
                    壓縮版本 (需事實提取)
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Role label */}
            <div className="text-sm font-semibold mb-2 flex items-center gap-2">
              {isUser ? (
                <>
                  <span>👤</span>
                  <span className="text-blue-700 dark:text-blue-300">使用者</span>
                </>
              ) : (
                <>
                  <span>🤖</span>
                  <span className="text-gray-700 dark:text-gray-300">AI</span>
                </>
              )}
              <span className="ml-auto text-xs text-gray-400 dark:text-gray-500 font-normal">
                #{index + 1}
              </span>
            </div>

            {/* Message content */}
            <div className="prose prose-lg dark:prose-invert max-w-none font-serif">
              <MyReactMarkdown content={msg.content} />
            </div>

            {/* Timestamp (if available) */}
            {msg.timestamp && (
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
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
