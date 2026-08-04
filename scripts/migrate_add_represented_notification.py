#!/usr/bin/env python3
"""
Database migration script to add the represented_notified_at column to visitors
"""

import sqlite3
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/leads.db")

def migrate():
    """Add represented_notified_at column to the visitors table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print("Starting migration to add represented_notified_at column...")

    try:
        cursor.execute("PRAGMA table_info(visitors)")
        columns = [row[1] for row in cursor.fetchall()]

        if "represented_notified_at" in columns:
            print("✓ Migration already completed (represented_notified_at column exists)")
            return

        cursor.execute("ALTER TABLE visitors ADD COLUMN represented_notified_at TIMESTAMP")
        print("Added represented_notified_at column...")

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
