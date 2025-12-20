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
  const copyCurrentMessage = async (index: number, override?: string) => {
    const message = messages[index];
    const content = override ?? message?.content;
    if (content) {
      try {
        await writeToClipboard(content);
        toast.success(`已複製訊息內容 (${content.length} 字)`);
      } catch (error) {
        console.error("Copy failed:", error);
        toast.error("複製失敗");
      }
    }
  };

  const copyOriginal = async (index: number, override?: string) => {
    const messagesToCopy = [...messages.slice(0, index + 1)];
    if (override && messagesToCopy.length > 0) {
      const lastMsg = messagesToCopy[messagesToCopy.length - 1];
      if (lastMsg) {
        messagesToCopy[messagesToCopy.length - 1] = { ...lastMsg, content: override };
      }
    }

    const formattedContext = formatConversationContext(messagesToCopy);

    if (formattedContext) {
      try {
        await writeToClipboard(formattedContext);
        toast.success(`已複製原始對話內容 (${formattedContext.length} 字)`);
      } catch (error) {
        console.error("Copy failed:", error);
        toast.error("複製失敗");
      }
    }
  };

  const startCompressedCopy = async (index: number, override?: string) => {
    if (!conversationLogId) {
      toast.error("缺少對話紀錄 ID");
      return;
    }

    const targetMessage = messages[index];
    const isUser = targetMessage?.role === "user";

    // 如果是 user，我們只壓縮之前的歷史 (index - 1)
    // 如果不是 user (如 assistant)，我們包含當前訊息一起壓縮 (index)
    const upTo = isUser ? index - 1 : index;

    toast.info("正在提取對話事實...");

    try {
      const client = createBlogAgentClient({
        baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:50051",
      });

      let extractedFacts = "";

      // 如果有需要壓縮的訊息範圍才呼叫 API
      if (upTo >= 0) {
        const response = await client.extractConversationFacts({
          conversationLogId,
          upToMessageIndex: upTo,
        });
        extractedFacts = response.extractedFacts;
      }

      if (extractedFacts || isUser) {
        let header =
          "以下是我們之前對話的重點事實摘要，請作為背景參考，並根據最後的 <Task> 進行回覆。";
        const historyBlock = extractedFacts ? `<History>\n${extractedFacts}\n</History>` : "";

        let fullPackage: string;
        if (!isUser) {
          // 非使用者訊息：不包含 <Task> 區塊，且摘要已包含此訊息
          header = "以下是我們之前對話的重點事實摘要，請作為背景參考。";
          fullPackage = `${header}\n\n${historyBlock}`;
        } else {
          // 使用者訊息：摘要為之前的內容，此訊息放入 <Task>
          const taskContent = override ?? targetMessage?.content;

          if (!taskContent) {
            toast.error("找不到目標訊息內容");
            return;
          }

          const taskBlock = `<Task>\n${taskContent}\n</Task>`;
          fullPackage = historyBlock
            ? `${header}\n\n${historyBlock}\n\n${taskBlock}`
            : `請根據以下的 <Task> 進行回覆。\n\n${taskBlock}`;
        }

        try {
          await writeToClipboard(fullPackage);
          toast.success(`已複製事實提取後的摘要內容 (${fullPackage.length} 字)`);
        } catch (copyError) {
          console.error("Copy failed:", copyError);
          toast.error("複製失敗");
        }
      }
    } catch (error) {
      console.error("Fact extraction failed:", error);
      toast.error("事實提取失敗，請稍後再試");
    }
  };

  return {
    copyCurrentMessage,
    copyOriginal,
    startCompressedCopy,
  };
}

/**
 * 等待文档获得焦点后执行复制操作
 * @param text 要复制的文本
 * @param timeout 超时时间（毫秒），默认 5 分钟
 */
async function writeToClipboardWithFocus(text: string, timeout: number = 300000): Promise<void> {
  // 如果文档已经有焦点，直接复制
  if (document.hasFocus()) {
    await navigator.clipboard.writeText(text);
    return;
  }

  // 等待文档获得焦点
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      cleanup();
      reject(new Error("等待文档获得焦点超时"));
    }, timeout);

    const handleFocus = async () => {
      cleanup();
      try {
        // 稍微延迟一下，确保焦点稳定
        await new Promise((r) => setTimeout(r, 100));
        await navigator.clipboard.writeText(text);
        resolve();
      } catch (error) {
        reject(error);
      }
    };

    const cleanup = () => {
      clearTimeout(timeoutId);
      window.removeEventListener("focus", handleFocus);
    };

    window.addEventListener("focus", handleFocus, { once: true });
  });
}

async function writeToClipboard(text: string): Promise<void> {
  await writeToClipboardWithFocus(text);
}
