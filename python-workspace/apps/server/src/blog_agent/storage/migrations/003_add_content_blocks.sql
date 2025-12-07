-- Migration: Add content_blocks table (UI/UX P0)
-- This migration adds the content_blocks table to support Side-by-Side UI/UX design

-- content_blocks table
CREATE TABLE content_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blog_post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    block_order INTEGER NOT NULL,                  -- 在文章中的順序（從 0 開始）
    text TEXT NOT NULL,                            -- 文章內容（Markdown 格式）
    prompt_suggestion_id UUID REFERENCES prompt_suggestions(id) ON DELETE SET NULL,  -- 可選：關聯的 prompt 建議
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_content_blocks_blog_post_id ON content_blocks (blog_post_id);
CREATE INDEX idx_content_blocks_blog_post_order ON content_blocks (blog_post_id, block_order);
CREATE INDEX idx_content_blocks_prompt_suggestion_id ON content_blocks (prompt_suggestion_id);

