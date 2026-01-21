-- Migration: Add page format and DPI fields to jobs and posters tables
-- Date: 2026-01-21
-- Description: Add page format, orientation, DPI, and custom dimension fields to support multiple poster formats

-- ============================================================================
-- Jobs Table Migrations
-- ============================================================================

-- Add page_format column (default: 'classic')
-- Check if column exists before adding (idempotent)
ALTER TABLE jobs ADD COLUMN page_format VARCHAR(50) DEFAULT 'classic';

-- Add orientation column (default: 'portrait')
ALTER TABLE jobs ADD COLUMN orientation VARCHAR(20) DEFAULT 'portrait';

-- Add dpi column (default: 300)
ALTER TABLE jobs ADD COLUMN dpi INTEGER DEFAULT 300;

-- Add custom_width_inches column (nullable)
ALTER TABLE jobs ADD COLUMN custom_width_inches REAL;

-- Add custom_height_inches column (nullable)
ALTER TABLE jobs ADD COLUMN custom_height_inches REAL;

-- Update existing rows to have default values
UPDATE jobs 
SET page_format = 'classic', 
    orientation = 'portrait', 
    dpi = 300 
WHERE page_format IS NULL OR orientation IS NULL OR dpi IS NULL;

-- ============================================================================
-- Posters Table Migrations
-- ============================================================================

-- Add page_format column (default: 'classic')
ALTER TABLE posters ADD COLUMN page_format VARCHAR(50) DEFAULT 'classic';

-- Add orientation column (default: 'portrait')
ALTER TABLE posters ADD COLUMN orientation VARCHAR(20) DEFAULT 'portrait';

-- Add dpi column (default: 300)
ALTER TABLE posters ADD COLUMN dpi INTEGER DEFAULT 300;

-- Add custom_width_inches column (nullable)
ALTER TABLE posters ADD COLUMN custom_width_inches REAL;

-- Add custom_height_inches column (nullable)
ALTER TABLE posters ADD COLUMN custom_height_inches REAL;

-- Add width_inches column (default: 12.0)
ALTER TABLE posters ADD COLUMN width_inches REAL DEFAULT 12.0;

-- Add height_inches column (default: 16.0)
ALTER TABLE posters ADD COLUMN height_inches REAL DEFAULT 16.0;

-- Update existing rows to have default values
UPDATE posters 
SET page_format = 'classic', 
    orientation = 'portrait', 
    dpi = 300,
    width_inches = 12.0,
    height_inches = 16.0
WHERE page_format IS NULL OR orientation IS NULL OR dpi IS NULL OR width_inches IS NULL OR height_inches IS NULL;

-- ============================================================================
-- Notes:
-- ============================================================================
-- - SQLite uses REAL for floating point numbers (equivalent to FLOAT)
-- - SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so the migration
--   runner script will handle checking if columns exist before running
-- - Default values are set both in ALTER TABLE and via UPDATE to ensure
--   existing rows get the defaults
-- - Custom dimensions are nullable as they're only used for 'custom' format