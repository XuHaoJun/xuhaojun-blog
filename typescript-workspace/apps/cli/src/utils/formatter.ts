/**
 * Formatter utility for displaying structured metadata
 */

export interface BlogPostMetadata {
  id?: string;
  conversation_log_id?: string;
  title: string;
  summary: string;
  tags: string[];
  content: string;
  metadata?: Record<string, any>;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Format blog post metadata for display
 */
export function formatBlogPostMetadata(blogPost: BlogPostMetadata): string {
  const lines: string[] = [];

  // Title
  lines.push(`標題 (Title): ${blogPost.title}`);
  lines.push("");

  // Summary
  lines.push(`摘要 (Summary): ${blogPost.summary}`);
  lines.push("");

  // Tags
  if (blogPost.tags && blogPost.tags.length > 0) {
    lines.push(`標籤 (Tags): ${blogPost.tags.join(", ")}`);
  } else {
    lines.push("標籤 (Tags): (無)");
  }
  lines.push("");

  // Status
  if (blogPost.status) {
    lines.push(`狀態 (Status): ${blogPost.status}`);
    lines.push("");
  }

  // Metadata from conversation log (FR-015)
  if (blogPost.metadata) {
    if (blogPost.metadata.conversation_timestamps) {
      const timestamps = blogPost.metadata.conversation_timestamps;
      if (timestamps.first) {
        lines.push(`對話開始時間: ${timestamps.first}`);
      }
      if (timestamps.last) {
        lines.push(`對話結束時間: ${timestamps.last}`);
      }
      if (timestamps.count) {
        lines.push(`時間戳記數量: ${timestamps.count}`);
      }
      lines.push("");
    }

    if (blogPost.metadata.conversation_participants) {
      const participants = Array.isArray(blogPost.metadata.conversation_participants)
        ? blogPost.metadata.conversation_participants
        : [blogPost.metadata.conversation_participants];
      lines.push(
        `參與者 (Participants): ${participants.join(", ")}`
      );
      lines.push("");
    }

    if (blogPost.metadata.language) {
      lines.push(`語言 (Language): ${blogPost.metadata.language}`);
      lines.push("");
    }

    if (blogPost.metadata.message_count) {
      lines.push(`訊息數量: ${blogPost.metadata.message_count}`);
      lines.push("");
    }

    if (blogPost.metadata.key_insights) {
      const keyInsights = Array.isArray(blogPost.metadata.key_insights)
        ? blogPost.metadata.key_insights
        : [blogPost.metadata.key_insights];
      if (keyInsights.length > 0) {
        lines.push("核心觀點 (Key Insights):");
        keyInsights.forEach((insight: string) => {
          lines.push(`  - ${insight}`);
        });
        lines.push("");
      }
    }

    if (blogPost.metadata.core_concepts) {
      const coreConcepts = Array.isArray(blogPost.metadata.core_concepts)
        ? blogPost.metadata.core_concepts
        : [blogPost.metadata.core_concepts];
      if (coreConcepts.length > 0) {
        lines.push("核心概念 (Core Concepts):");
        coreConcepts.forEach((concept: string) => {
          lines.push(`  - ${concept}`);
        });
        lines.push("");
      }
    }
  }

  // Dates
  if (blogPost.created_at) {
    lines.push(`建立時間: ${blogPost.created_at}`);
  }
  if (blogPost.updated_at) {
    lines.push(`更新時間: ${blogPost.updated_at}`);
  }

  return lines.join("\n");
}

/**
 * Format blog post as Markdown with frontmatter
 */
export function formatBlogPostAsMarkdown(blogPost: BlogPostMetadata): string {
  const frontmatter: string[] = [];
  frontmatter.push("---");

  // Required fields (FR-005)
  frontmatter.push(`title: "${escapeYamlString(blogPost.title)}"`);
  frontmatter.push(`summary: "${escapeYamlString(blogPost.summary)}"`);

  if (blogPost.tags && blogPost.tags.length > 0) {
    frontmatter.push("tags:");
    blogPost.tags.forEach((tag) => {
      frontmatter.push(`  - "${escapeYamlString(tag)}"`);
    });
  } else {
    frontmatter.push("tags: []");
  }

  if (blogPost.status) {
    frontmatter.push(`status: "${blogPost.status}"`);
  }

  // Dates
  if (blogPost.created_at) {
    frontmatter.push(`created_at: "${blogPost.created_at}"`);
  }
  if (blogPost.updated_at) {
    frontmatter.push(`updated_at: "${blogPost.updated_at}"`);
  }

  // Additional metadata
  if (blogPost.metadata) {
    if (blogPost.metadata.conversation_timestamps) {
      frontmatter.push("conversation_timestamps:");
      const ts = blogPost.metadata.conversation_timestamps;
      if (ts.first) frontmatter.push(`  first: "${ts.first}"`);
      if (ts.last) frontmatter.push(`  last: "${ts.last}"`);
      if (ts.count) frontmatter.push(`  count: ${ts.count}`);
    }

    if (blogPost.metadata.conversation_participants) {
      frontmatter.push("conversation_participants:");
      const participants = Array.isArray(blogPost.metadata.conversation_participants)
        ? blogPost.metadata.conversation_participants
        : [blogPost.metadata.conversation_participants];
      participants.forEach((p: string) => {
        frontmatter.push(`  - "${escapeYamlString(p)}"`);
      });
    }

    if (blogPost.metadata.language) {
      frontmatter.push(`language: "${blogPost.metadata.language}"`);
    }

    if (blogPost.metadata.message_count) {
      frontmatter.push(`message_count: ${blogPost.metadata.message_count}`);
    }
  }

  frontmatter.push("---");
  frontmatter.push("");

  return frontmatter.join("\n") + blogPost.content;
}

/**
 * Escape special characters in YAML strings
 */
function escapeYamlString(str: string): string {
  return str.replace(/"/g, '\\"').replace(/\n/g, "\\n");
}

