-- Migration: Update prompt_suggestions table for UI/UX support (UI/UX P0)
-- This migration updates better_candidates to JSONB and adds expected_effect field

-- Step 0: Drop the existing default (TEXT[] default can't be cast to JSONB)
ALTER TABLE prompt_suggestions 
ALTER COLUMN better_candidates DROP DEFAULT;

-- Step 1: First alter column from TEXT[] to TEXT (intermediate step)
-- This allows us to work with the data as text
ALTER TABLE prompt_suggestions 
ALTER COLUMN better_candidates TYPE TEXT USING array_to_string(better_candidates, ',');

-- Step 2: Convert existing better_candidates from TEXT (comma-separated) to JSONB
-- For existing data, we'll convert each string to a JSON object with default structure
DO $$
DECLARE
    rec RECORD;
    candidate_json JSONB;
    candidates_array JSONB := '[]'::JSONB;
    candidate_text TEXT;
    candidate_array TEXT[];
BEGIN
    -- For each existing prompt_suggestion, convert better_candidates
    FOR rec IN SELECT id, better_candidates FROM prompt_suggestions WHERE better_candidates IS NOT NULL AND better_candidates != ''
    LOOP
        -- Parse comma-separated string back to array
        candidate_array := string_to_array(rec.better_candidates, ',');
        candidates_array := '[]'::JSONB;
        
        -- Convert each string to JSONB object
        FOREACH candidate_text IN ARRAY candidate_array
        LOOP
            candidate_json := jsonb_build_object(
                'type', 'structured',
                'prompt', candidate_text,
                'reasoning', ''
            );
            candidates_array := candidates_array || candidate_json;
        END LOOP;
        
        -- Update the row with JSONB version (as text for now)
        UPDATE prompt_suggestions
        SET better_candidates = candidates_array::TEXT
        WHERE id = rec.id;
    END LOOP;
    
    -- For empty/null values, set to empty JSONB array
    UPDATE prompt_suggestions
    SET better_candidates = '[]'::TEXT
    WHERE better_candidates IS NULL OR better_candidates = '';
END $$;

-- Step 3: Now alter the column type from TEXT to JSONB
ALTER TABLE prompt_suggestions 
ALTER COLUMN better_candidates TYPE JSONB USING better_candidates::JSONB;

-- Step 4: Set new default to empty JSONB array
ALTER TABLE prompt_suggestions 
ALTER COLUMN better_candidates SET DEFAULT '[]'::JSONB;

-- Add expected_effect column (nullable for backward compatibility)
ALTER TABLE prompt_suggestions 
ADD COLUMN expected_effect TEXT;

