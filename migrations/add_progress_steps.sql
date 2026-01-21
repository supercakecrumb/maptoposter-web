-- Migration: Add progress_steps column to jobs table
-- Date: 2026-01-21
-- Description: Add JSON column to track detailed progress steps for poster generation

-- SQLite syntax for adding a column with default value
ALTER TABLE jobs ADD COLUMN progress_steps TEXT DEFAULT '[]';

-- Note: In SQLite, JSON columns are stored as TEXT
-- The application will handle JSON serialization/deserialization