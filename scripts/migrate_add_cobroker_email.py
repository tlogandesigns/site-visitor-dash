#!/usr/bin/env python3
"""
Database migration script to add the cobroker_email column to visitors
"""

import sqlite3
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/leads.db")

def migrate():
    """Add cobroker_email column to the visitors table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print("Starting migration to add cobroker_email column...")

    try:
        cursor.execute("PRAGMA table_info(visitors)")
        columns = [row[1] for row in cursor.fetchall()]

        if "cobroker_email" in columns:
            print("✓ Migration already completed (cobroker_email column exists)")
            return

        cursor.execute("ALTER TABLE visitors ADD COLUMN cobroker_email TEXT")
        print("Added cobroker_email column...")

        conn.commit()
        print("✓ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
