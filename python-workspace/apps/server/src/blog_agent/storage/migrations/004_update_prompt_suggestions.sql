-- Migration: Update prompt_suggestions table for UI/UX support (UI/UX P0)
-- This migration updates better_candidates to JSONB and adds expected_effect field

-- First, convert existing better_candidates from TEXT[] to JSONB
-- For existing data, we'll convert each string to a JSON object with default structure
DO $$
DECLARE
    rec RECORD;
    candidate_json JSONB;
    candidates_array JSONB := '[]'::JSONB;
BEGIN
    -- For each existing prompt_suggestion, convert better_candidates
    FOR rec IN SELECT id, better_candidates FROM prompt_suggestions WHERE better_candidates IS NOT NULL
    LOOP
        -- Convert TEXT[] to JSONB array of objects
        -- Each string becomes: {"type": "structured", "prompt": "<original>", "reasoning": ""}
        candidates_array := '[]'::JSONB;
        
        FOR i IN 1..array_length(rec.better_candidates, 1)
        LOOP
            candidate_json := jsonb_build_object(
                'type', 'structured',
                'prompt', rec.better_candidates[i],
                'reasoning', ''
            );
            candidates_array := candidates_array || candidate_json;
        END LOOP;
        
        -- Update the row with JSONB version
        UPDATE prompt_suggestions
        SET better_candidates = candidates_array::TEXT
        WHERE id = rec.id;
    END LOOP;
END $$;

-- Now alter the column type from TEXT[] to JSONB
ALTER TABLE prompt_suggestions 
ALTER COLUMN better_candidates TYPE JSONB USING better_candidates::JSONB;

-- Set default to empty JSONB array
ALTER TABLE prompt_suggestions 
ALTER COLUMN better_candidates SET DEFAULT '[]'::JSONB;

-- Add expected_effect column (nullable for backward compatibility)
ALTER TABLE prompt_suggestions 
ADD COLUMN expected_effect TEXT;

