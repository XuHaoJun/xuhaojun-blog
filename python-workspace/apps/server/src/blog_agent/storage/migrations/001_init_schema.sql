-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Migration history table (must be first to track all migrations)
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    migration_name TEXT NOT NULL UNIQUE,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_migration_history_name ON migration_history (migration_name);

-- conversation_logs table
CREATE TABLE conversation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    file_format TEXT NOT NULL CHECK (file_format IN ('markdown', 'json', 'csv', 'text')),
    raw_content TEXT NOT NULL,
    parsed_content JSONB NOT NULL,
    metadata JSONB,
    language TEXT,
    message_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_conversation_logs_created_at ON conversation_logs (created_at DESC);
CREATE INDEX idx_conversation_logs_language ON conversation_logs (language);

-- blog_posts table
CREATE TABLE blog_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_log_id UUID NOT NULL REFERENCES conversation_logs(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    content TEXT NOT NULL,
    metadata JSONB,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_blog_posts_conversation_log_id ON blog_posts (conversation_log_id);
CREATE INDEX idx_blog_posts_status ON blog_posts (status);
CREATE INDEX idx_blog_posts_created_at ON blog_posts (created_at DESC);

-- processing_history table
CREATE TABLE processing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_log_id UUID NOT NULL REFERENCES conversation_logs(id) ON DELETE CASCADE,
    blog_post_id UUID REFERENCES blog_posts(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    processing_steps JSONB,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_processing_history_conversation_log_id ON processing_history (conversation_log_id);
CREATE INDEX idx_processing_history_status ON processing_history (status);
CREATE INDEX idx_processing_history_started_at ON processing_history (started_at DESC);

-- content_extracts table
CREATE TABLE content_extracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_log_id UUID NOT NULL REFERENCES conversation_logs(id) ON DELETE CASCADE,
    key_insights TEXT[] NOT NULL DEFAULT '{}',
    core_concepts TEXT[] NOT NULL DEFAULT '{}',
    facts TEXT,
    conversation_history TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_content_extracts_conversation_log_id ON content_extracts (conversation_log_id);

-- review_findings table
CREATE TABLE review_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_extract_id UUID NOT NULL REFERENCES content_extracts(id) ON DELETE CASCADE,
    issues JSONB NOT NULL,
    improvement_suggestions TEXT[] NOT NULL DEFAULT '{}',
    fact_checking_needs TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_review_findings_content_extract_id ON review_findings (content_extract_id);

-- prompt_suggestions table
CREATE TABLE prompt_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_log_id UUID NOT NULL REFERENCES conversation_logs(id) ON DELETE CASCADE,
    original_prompt TEXT NOT NULL,
    analysis TEXT NOT NULL,
    better_candidates TEXT[] NOT NULL DEFAULT '{}',
    reasoning TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_prompt_suggestions_conversation_log_id ON prompt_suggestions (conversation_log_id);

-- embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('conversation_log', 'blog_post', 'content_extract')),
    entity_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_embeddings_entity ON embeddings (entity_type, entity_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);

