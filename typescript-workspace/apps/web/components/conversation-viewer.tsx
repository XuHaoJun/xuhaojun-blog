"use client";

import type { ConversationMessage } from "@blog-agent/proto-gen";
import { cn } from "@/lib/utils";
import { MyReactMarkdown } from "./my-react-markdown";

interface ConversationViewerProps {
  messages: ConversationMessage[];
  onMessageHover?: (index: number) => void;
  onMessageLeave?: () => void;
  activeMessageIndex?: number;
}

export function ConversationViewer({
  messages,
  onMessageHover,
  onMessageLeave,
  activeMessageIndex,
}: ConversationViewerProps) {
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
              "p-4 rounded-lg transition-all duration-300",
              isUser
                ? "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
                : "bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
              isActive &&
                "ring-2 ring-blue-500 dark:ring-blue-400 ring-offset-2 dark:ring-offset-gray-900"
            )}
            onMouseEnter={() => onMessageHover?.(index)}
            onMouseLeave={onMessageLeave}
          >
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
    </div>
  );
}
