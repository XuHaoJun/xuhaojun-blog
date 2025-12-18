import { describe, it, expect } from "vitest";
import { formatConversationContext } from "../lib/context-formatter";
import { ConversationMessage } from "@blog-agent/proto-gen";

describe("formatConversationContext", () => {
  it("should return empty string for empty messages", () => {
    expect(formatConversationContext([])).toBe("");
  });

  it("should exclude system messages", () => {
    const messages: ConversationMessage[] = [
      { role: "system", content: "You are an assistant" },
      { role: "user", content: "Hello" },
    ];
    const result = formatConversationContext(messages);
    expect(result).not.toContain("system");
    expect(result).toContain("<Task>\nHello\n</Task>");
  });

  it("should format history and task correctly", () => {
    const messages: ConversationMessage[] = [
      { role: "user", content: "Question 1" },
      { role: "assistant", content: "Answer 1" },
      { role: "user", content: "Question 2" },
    ];
    const result = formatConversationContext(messages);
    
    expect(result).toContain("<History>");
    expect(result).toContain("User: Question 1");
    expect(result).toContain("Assistant: Answer 1");
    expect(result).toContain("<Task>\nQuestion 2\n</Task>");
  });

  it("should handle single message correctly (no history)", () => {
    const messages: ConversationMessage[] = [
      { role: "user", content: "Hello" },
    ];
    const result = formatConversationContext(messages);
    
    expect(result).not.toContain("<History>");
    expect(result).toContain("<Task>\nHello\n</Task>");
  });
});

