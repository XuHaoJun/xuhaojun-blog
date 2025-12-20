import { useState } from "react";
import type { ConversationMessage } from "@blog-agent/proto-gen";
import { formatConversationContext } from "@/lib/context-formatter";
import { toast } from "sonner";
import { createBlogAgentClient } from "@blog-agent/rpc-client";

export interface UseCopyActionsOptions {
  messages: ConversationMessage[];
  conversationLogId?: string;
}

export function useCopyActions({ messages, conversationLogId }: UseCopyActionsOptions) {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isCompressing, setIsCompressing] = useState(false);
  const [targetIndex, setTargetIndex] = useState<number | null>(null);
  const [contentOverride, setContentOverride] = useState<string | undefined>();

  const copyCurrentMessage = (index: number, override?: string) => {
    const message = messages[index];
    const content = override ?? message?.content;
    if (content) {
      navigator.clipboard.writeText(content);
      toast.success(`已複製訊息內容 (${content.length} 字)`);
    }
  };

  const copyOriginal = (index: number, override?: string) => {
    const messagesToCopy = [...messages.slice(0, index + 1)];
    if (override && messagesToCopy.length > 0) {
      const lastMsg = messagesToCopy[messagesToCopy.length - 1];
      messagesToCopy[messagesToCopy.length - 1] = { ...lastMsg, content: override };
    }
    
    const formattedContext = formatConversationContext(messagesToCopy);

    if (formattedContext) {
      navigator.clipboard.writeText(formattedContext);
      toast.success(`已複製原始對話內容 (${formattedContext.length} 字)`);
    }
  };

  const startCompressedCopy = (index: number, override?: string) => {
    setTargetIndex(index);
    setContentOverride(override);
    setIsFormOpen(true);
  };

  const handleCompressedSubmit = async (limit: number) => {
    if (!conversationLogId || targetIndex === null) return;

    setIsCompressing(true);
    try {
      const client = createBlogAgentClient({
        baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:50051",
      });

      const response = await client.extractConversationFacts({
        conversationLogId,
        maxCharacters: limit,
        upToMessageIndex: targetIndex,
      });

      if (response.extractedFacts) {
        const header = `以下是我們之前對話的重點事實摘要，請作為背景參考，並根據最後的 <Task> 進行回覆。`;
        const historyBlock = `<History>\n${response.extractedFacts}\n</History>`;
        
        const taskContent = contentOverride ?? messages[targetIndex]?.content;

        if (!taskContent) {
          toast.error("找不到目標訊息內容");
          return;
        }

        const taskBlock = `<Task>\n${taskContent}\n</Task>`;
        const fullPackage = `${header}\n\n${historyBlock}\n\n${taskBlock}`;

        await navigator.clipboard.writeText(fullPackage);

        if (response.limitExceeded) {
          toast.warning(`已複製摘要內容 (${fullPackage.length} 字)，但已超過 ${limit} 字限制，已提供最佳壓縮版本`);
        } else {
          toast.success(`已複製事實提取後的摘要內容 (${fullPackage.length} 字)`);
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

  return {
    isFormOpen,
    setIsFormOpen,
    isCompressing,
    copyCurrentMessage,
    copyOriginal,
    startCompressedCopy,
    handleCompressedSubmit,
  };
}

