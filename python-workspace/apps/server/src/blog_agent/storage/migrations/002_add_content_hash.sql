-- Migration: Add content_hash column to conversation_logs table (FR-031)
-- This migration adds the content_hash column for file change detection

-- Enable pgcrypto extension for SHA-256 hash calculation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Add content_hash column (NOT NULL, but we'll set default for existing rows first)
ALTER TABLE conversation_logs 
ADD COLUMN content_hash TEXT;

-- For existing rows, set a placeholder hash (empty string hash)
-- In production, you may want to backfill with actual hashes
UPDATE conversation_logs 
SET content_hash = encode(digest(raw_content, 'sha256'), 'hex')
WHERE content_hash IS NULL;

-- Now make it NOT NULL
ALTER TABLE conversation_logs 
ALTER COLUMN content_hash SET NOT NULL;

-- Create index on content_hash for fast lookups
CREATE INDEX idx_conversation_logs_content_hash ON conversation_logs (content_hash);

-- Create unique index on (file_path, content_hash) to prevent duplicate processing
CREATE UNIQUE INDEX idx_conversation_logs_file_path_hash ON conversation_logs (file_path, content_hash);

