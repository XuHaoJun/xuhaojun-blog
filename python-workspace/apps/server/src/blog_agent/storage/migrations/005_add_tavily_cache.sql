-- Tavily search results cache table
CREATE TABLE tavily_search_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    search_depth TEXT NOT NULL,
    max_results INTEGER NOT NULL,
    include_domains TEXT[],
    exclude_domains TEXT[],
    results JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Unique constraint for cache lookup
    -- PostgreSQL handles NULLs in UNIQUE constraints such that NULL != NULL.
    -- However, for our cache, we want to treat empty/null domains as part of the key.
    -- We'll use COALESCE in a unique index instead if needed, but for now let's try a standard unique constraint
    -- if we can ensure domains are stored as empty arrays instead of NULL.
    UNIQUE (query, search_depth, max_results, include_domains, exclude_domains)
);

CREATE INDEX idx_tavily_search_cache_expires_at ON tavily_search_cache (expires_at);
CREATE INDEX idx_tavily_search_cache_query ON tavily_search_cache (query);

