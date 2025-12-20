/**
 * Utility for formatting conversation history into a structured package
 * suitable for pasting into LLM web interfaces (ChatGPT, Claude, DeepSeek).
 */

import { ConversationMessage } from "@blog-agent/proto-gen";

export interface ContextPackageOptions {
  includeSystemPrompt?: boolean;
}

/**
 * Formats a list of messages into a structured context package.
 * 
 * @param messages List of conversation messages up to the current one.
 * @param options Options for formatting.
 * @returns Formatted string with instruction header, history, and current task.
 */
export function formatConversationContext(
  messages: ConversationMessage[],
  options: ContextPackageOptions = {}
): string {
  if (messages.length === 0) return "";

  // Per clarification: System messages are excluded.
  const filteredMessages = messages.filter((msg) => msg.role !== "system");
  
  if (filteredMessages.length === 0) return "";

  // The last message in the provided array is the "current task" or the message where the action was triggered.
  const historyMessages = filteredMessages.slice(0, -1);
  const taskMessage = filteredMessages[filteredMessages.length - 1];

  if (!taskMessage) return "";

  const header = `以下是我之前與你的對話紀錄，請作為背景參考，並根據最後的 <Task> 進行回覆。`;

  let historyBlock = "";
  if (historyMessages.length > 0) {
    const historyContent = historyMessages
      .map((msg) => `${msg.role === "user" ? "User" : "Assistant"}: ${msg.content}`)
      .join("\n\n");
    historyBlock = `<History>\n${historyContent}\n</History>`;
  }

  const taskBlock = `<Task>\n${taskMessage.content}\n</Task>`;

  return [header, historyBlock, taskBlock].filter(Boolean).join("\n\n");
}

