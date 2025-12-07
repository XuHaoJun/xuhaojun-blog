/**
 * File reader utility for reading conversation logs
 */

import * as fs from "fs/promises";
import * as path from "path";

export interface FileReadResult {
  content: Buffer;
  format: string;
}

/**
 * Read file and detect format
 */
export async function readConversationFile(filePath: string): Promise<FileReadResult> {
  try {
    const content = await fs.readFile(filePath);
    const format = detectFileFormat(filePath, content);

    return {
      content,
      format,
    };
  } catch (error) {
    throw new Error(`Failed to read file ${filePath}: ${error}`);
  }
}

/**
 * Detect file format from path and content
 */
function detectFileFormat(filePath: string, content: Buffer): string {
  const ext = path.extname(filePath).toLowerCase();

  const formatMap: Record<string, string> = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".json": "json",
    ".csv": "csv",
    ".txt": "text",
  };

  if (ext in formatMap) {
    return formatMap[ext];
  }

  // Try to detect from content
  const contentStr = content.toString("utf-8", 0, Math.min(500, content.length));

  // Check for JSON
  if (contentStr.trim().startsWith("{") || contentStr.trim().startsWith("[")) {
    try {
      JSON.parse(contentStr);
      return "json";
    } catch {
      // Not valid JSON
    }
  }

  // Check for Markdown (has ## headers)
  if (contentStr.includes("##")) {
    return "markdown";
  }

  // Check for CSV (has commas and newlines)
  if (contentStr.includes(",") && contentStr.includes("\n")) {
    return "csv";
  }

  // Default to text
  return "text";
}

