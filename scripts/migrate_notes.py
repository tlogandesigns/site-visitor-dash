#!/usr/bin/env python3
"""
Migrate existing notes from visitors.notes field to visitor_notes table
"""
import sqlite3
import os

DB_PATH = os.environ.get('DATABASE_PATH', '/data/leads.db')

def migrate_notes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find all visitors with notes that aren't already in visitor_notes
    visitors_with_notes = cursor.execute("""
        SELECT id, notes, capturing_agent_id, created_at
        FROM visitors
        WHERE notes IS NOT NULL
        AND notes != ''
        AND TRIM(notes) != ''
    """).fetchall()

    print(f"Found {len(visitors_with_notes)} visitors with notes in the notes field")

    migrated = 0
    skipped = 0

    for visitor in visitors_with_notes:
        visitor_id = visitor['id']
        note_text = visitor['notes'].strip()
        agent_id = visitor['capturing_agent_id']
        created_at = visitor['created_at']

        # Check if this note already exists in visitor_notes
        existing_note = cursor.execute("""
            SELECT id FROM visitor_notes
            WHERE visitor_id = ? AND note = ?
        """, (visitor_id, note_text)).fetchone()

        if existing_note:
            print(f"  Visitor {visitor_id}: Note already exists in visitor_notes, skipping")
            skipped += 1
            continue

        # Create the note in visitor_notes table with the original visitor creation timestamp
        cursor.execute("""
            INSERT INTO visitor_notes (visitor_id, agent_id, note, created_at)
            VALUES (?, ?, ?, ?)
        """, (visitor_id, agent_id, note_text, created_at))

        print(f"  Visitor {visitor_id}: Migrated note to visitor_notes")
        migrated += 1

    conn.commit()
    conn.close()

    print(f"\nMigration complete!")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped (already exists): {skipped}")
    print(f"  Total: {len(visitors_with_notes)}")

if __name__ == "__main__":
    migrate_notes()
