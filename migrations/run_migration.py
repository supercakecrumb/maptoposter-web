#!/usr/bin/env python3
"""
Database Migration Runner for Page Format and DPI Fields

This script applies the add_page_format_dpi.sql migration to the SQLite database.
It handles:
- Detecting database location (posters.db or instance/posters.db)
- Checking if columns already exist (idempotent)
- Graceful error handling
- Detailed logging

Usage:
    python migrations/run_migration.py
    
Or specify a custom database path:
    python migrations/run_migration.py --db-path /path/to/database.db
"""

import sqlite3
import sys
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migrations/migration.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


def find_database():
    """
    Find the SQLite database file.
    
    Checks in order:
    1. posters.db in project root
    2. instance/posters.db
    
    Returns:
        Path: Path to the database file
        
    Raises:
        FileNotFoundError: If no database file is found
    """
    # Get project root (parent of migrations directory)
    project_root = Path(__file__).parent.parent
    
    # Check possible locations
    possible_locations = [
        project_root / 'posters.db',
        project_root / 'instance' / 'posters.db'
    ]
    
    for db_path in possible_locations:
        if db_path.exists():
            logger.info(f"Found database at: {db_path}")
            return db_path
    
    # No database found
    locations_str = '\n  - '.join(str(p) for p in possible_locations)
    raise FileNotFoundError(
        f"Database not found. Checked:\n  - {locations_str}\n"
        "Please ensure the database exists before running migrations."
    )


def get_table_columns(cursor, table_name):
    """
    Get list of column names for a table.
    
    Args:
        cursor: SQLite cursor
        table_name: Name of the table
        
    Returns:
        set: Set of column names
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    return columns


def column_exists(cursor, table_name, column_name):
    """
    Check if a column exists in a table.
    
    Args:
        cursor: SQLite cursor
        table_name: Name of the table
        column_name: Name of the column
        
    Returns:
        bool: True if column exists
    """
    columns = get_table_columns(cursor, table_name)
    return column_name in columns


def check_migration_needed(cursor):
    """
    Check which columns need to be added.
    
    Args:
        cursor: SQLite cursor
        
    Returns:
        dict: Dictionary with tables as keys and lists of missing columns as values
    """
    logger.info("Checking which columns need to be added...")
    
    # Define expected columns for each table
    expected_columns = {
        'jobs': [
            'page_format',
            'orientation',
            'dpi',
            'custom_width_inches',
            'custom_height_inches'
        ],
        'posters': [
            'page_format',
            'orientation',
            'dpi',
            'custom_width_inches',
            'custom_height_inches',
            'width_inches',
            'height_inches'
        ]
    }
    
    missing_columns = {}
    
    for table_name, columns in expected_columns.items():
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            logger.warning(f"Table '{table_name}' does not exist!")
            continue
        
        # Get existing columns
        existing_columns = get_table_columns(cursor, table_name)
        
        # Find missing columns
        missing = [col for col in columns if col not in existing_columns]
        
        if missing:
            missing_columns[table_name] = missing
            logger.info(f"  {table_name}: Missing columns: {', '.join(missing)}")
        else:
            logger.info(f"  {table_name}: All columns already exist ✓")
    
    return missing_columns


def execute_migration_statement(cursor, statement):
    """
    Execute a single migration statement with error handling.
    
    Args:
        cursor: SQLite cursor
        statement: SQL statement to execute
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        cursor.execute(statement)
        return True, None
    except sqlite3.OperationalError as e:
        error_msg = str(e)
        # Check if it's a "duplicate column" error (column already exists)
        if 'duplicate column name' in error_msg.lower():
            return True, 'Column already exists (skipped)'
        else:
            return False, error_msg


def run_migration(db_path):
    """
    Run the migration on the specified database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        bool: True if migration succeeded
    """
    logger.info("=" * 70)
    logger.info("Starting database migration: add_page_format_dpi")
    logger.info(f"Database: {db_path}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 70)
    
    # Read migration SQL file
    migration_file = Path(__file__).parent / 'add_page_format_dpi.sql'
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False
    
    logger.info(f"Reading migration file: {migration_file}")
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        logger.info("Database connection established ✓")
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        return False
    
    try:
        # Check what needs to be migrated
        missing_columns = check_migration_needed(cursor)
        
        if not missing_columns:
            logger.info("\n" + "=" * 70)
            logger.info("Migration not needed - all columns already exist!")
            logger.info("=" * 70)
            return True
        
        logger.info("\n" + "=" * 70)
        logger.info("Applying migration...")
        logger.info("=" * 70)
        
        # Split SQL into individual statements and clean them
        raw_statements = migration_sql.split(';')
        statements = []
        
        for stmt in raw_statements:
            # Remove comments and empty lines
            lines = []
            for line in stmt.split('\n'):
                stripped = line.strip()
                if stripped and not stripped.startswith('--'):
                    lines.append(line)
            
            cleaned_stmt = '\n'.join(lines).strip()
            if cleaned_stmt:
                statements.append(cleaned_stmt)
        
        executed_count = 0
        skipped_count = 0
        failed_count = 0
        
        logger.info(f"Found {len(statements)} SQL statements to execute")
        
        for i, statement in enumerate(statements, 1):
            
            # Log the statement type
            statement_lower = statement.lower()
            if 'alter table' in statement_lower:
                # Extract table and column info
                parts = statement.split()
                if 'add column' in statement_lower:
                    table_idx = parts.index('table') if 'table' in parts else -1
                    if table_idx > 0 and table_idx + 1 < len(parts):
                        table_name = parts[table_idx + 1]
                        column_idx = parts.index('column') if 'column' in parts else -1
                        if column_idx > 0 and column_idx + 1 < len(parts):
                            column_name = parts[column_idx + 1]
                            logger.info(f"  [{i}/{len(statements)}] Adding column '{column_name}' to '{table_name}'...")
            elif 'update' in statement_lower:
                logger.info(f"  [{i}/{len(statements)}] Updating default values...")
            
            # Execute statement
            success, error = execute_migration_statement(cursor, statement)
            
            if success:
                if error:
                    logger.info(f"    → {error}")
                    skipped_count += 1
                else:
                    logger.info(f"    → Success ✓")
                    executed_count += 1
            else:
                logger.error(f"    → Failed: {error}")
                failed_count += 1
        
        # Commit changes
        if failed_count == 0:
            conn.commit()
            logger.info("\n" + "=" * 70)
            logger.info("Migration completed successfully! ✓")
            logger.info(f"  Executed: {executed_count} statements")
            logger.info(f"  Skipped: {skipped_count} statements (already applied)")
            logger.info("=" * 70)
            return True
        else:
            conn.rollback()
            logger.error("\n" + "=" * 70)
            logger.error(f"Migration failed! {failed_count} statements had errors")
            logger.error("Changes have been rolled back.")
            logger.error("=" * 70)
            return False
        
    except Exception as e:
        conn.rollback()
        logger.error(f"\nUnexpected error during migration: {e}")
        logger.exception("Full traceback:")
        return False
    
    finally:
        conn.close()
        logger.info("Database connection closed")


def main():
    """Main entry point for the migration runner."""
    parser = argparse.ArgumentParser(
        description='Run database migration to add page format and DPI fields'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        help='Path to the SQLite database file (default: auto-detect)'
    )
    
    args = parser.parse_args()
    
    try:
        # Find or use specified database
        if args.db_path:
            db_path = Path(args.db_path)
            if not db_path.exists():
                logger.error(f"Specified database not found: {db_path}")
                sys.exit(1)
        else:
            db_path = find_database()
        
        # Run migration
        success = run_migration(db_path)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == '__main__':
    main()