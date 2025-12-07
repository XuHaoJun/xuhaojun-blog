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
 * Validate that file path is within conversations/ directory (FR-029)
 */
export function validateConversationsDirectory(filePath: string): { valid: boolean; error?: string } {
  const resolvedPath = path.resolve(filePath);
  const pathParts = resolvedPath.split(path.sep);
  
  if (!pathParts.includes("conversations")) {
    return {
      valid: false,
      error: `File path must be within conversations/ directory. Got: ${filePath}`,
    };
  }
  
  const conversationsIdx = pathParts.indexOf("conversations");
  if (conversationsIdx === pathParts.length - 1) {
    return {
      valid: false,
      error: `File path points to conversations/ directory itself, not a file. Got: ${filePath}`,
    };
  }
  
  return { valid: true };
}

/**
 * Read file and detect format
 */
export async function readConversationFile(filePath: string): Promise<FileReadResult> {
  try {
    // Validate file path is in conversations/ directory (FR-029)
    const validation = validateConversationsDirectory(filePath);
    if (!validation.valid) {
      throw new Error(validation.error);
    }
    
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

