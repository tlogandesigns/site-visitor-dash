#!/usr/bin/env python3
"""
Database migration script to update visitors table with new fields
"""

import sqlite3
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/leads.db")

def migrate():
    """Migrate the visitors table to include new fields"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print("Starting migration of visitors table...")

    try:
        # Drop the existing view first (it depends on visitors table)
        cursor.execute("DROP VIEW IF EXISTS visitor_details")
        print("Dropped visitor_details view...")

        # Create new visitors table with all new fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitors_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- Buyer Info (Required fields)
                buyer_name TEXT NOT NULL,
                buyer_phone TEXT,
                buyer_email TEXT,

                -- Visit Info
                first_visit BOOLEAN DEFAULT 1,

                -- Interests (JSON array or comma-separated)
                interested_in TEXT,

                -- Timeline
                purchase_timeline TEXT,

                -- Representation
                represented BOOLEAN DEFAULT 0,
                cobroker_name TEXT,

                -- Location
                is_local BOOLEAN DEFAULT 1,
                buyer_state TEXT,

                -- Occupation
                occupation TEXT,
                occupation_other TEXT,

                -- Discovery method
                discovery_method TEXT,

                -- Builder preferences
                builders_requested TEXT,

                -- Sales status (updateable)
                offer_on_table BOOLEAN DEFAULT 0,
                finalized_contracts BOOLEAN DEFAULT 0,

                -- Notes (updateable)
                notes TEXT,

                -- Legacy fields (keeping for backward compatibility)
                price_range TEXT,
                location_looking TEXT,
                location_current TEXT,
                agent_name TEXT,

                -- Agent Info
                capturing_agent_id INTEGER NOT NULL,
                site TEXT NOT NULL,

                -- Meta
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cinc_synced BOOLEAN DEFAULT 0,
                cinc_sync_at TIMESTAMP,
                cinc_lead_id TEXT,

                FOREIGN KEY (capturing_agent_id) REFERENCES agents(id)
            )
        """)

        print("Created new visitors table...")

        # Copy existing data from old table to new table
        cursor.execute("""
            INSERT INTO visitors_new (
                id, buyer_name, buyer_phone, buyer_email,
                purchase_timeline, price_range, location_looking,
                location_current, occupation, represented, agent_name,
                capturing_agent_id, site, created_at, updated_at,
                cinc_synced, cinc_sync_at, cinc_lead_id
            )
            SELECT
                id, buyer_name, buyer_phone, buyer_email,
                purchase_timeline, price_range, location_looking,
                location_current, occupation, represented, agent_name,
                capturing_agent_id, site, created_at, updated_at,
                cinc_synced, cinc_sync_at, cinc_lead_id
            FROM visitors
        """)

        rows_copied = cursor.rowcount
        print(f"Copied {rows_copied} existing records...")

        # Drop old table
        cursor.execute("DROP TABLE visitors")
        print("Dropped old visitors table...")

        # Rename new table
        cursor.execute("ALTER TABLE visitors_new RENAME TO visitors")
        print("Renamed new table to visitors...")

        # Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_visitors_phone ON visitors(buyer_phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_visitors_email ON visitors(buyer_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_visitors_site ON visitors(site)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_visitors_created ON visitors(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_visitors_capturing_agent ON visitors(capturing_agent_id)")
        print("Recreated indexes...")

        # Recreate the visitor_details view
        cursor.execute("DROP VIEW IF EXISTS visitor_details")
        cursor.execute("""
            CREATE VIEW visitor_details AS
            SELECT
                v.*,
                a.name as agent_name,
                a.cinc_id as agent_cinc_id,
                (SELECT COUNT(*) FROM visitor_notes WHERE visitor_id = v.id) as note_count,
                (SELECT note FROM visitor_notes WHERE visitor_id = v.id ORDER BY created_at DESC LIMIT 1) as latest_note
            FROM visitors v
            LEFT JOIN agents a ON v.capturing_agent_id = a.id
        """)
        print("Recreated visitor_details view...")

        conn.commit()
        print("✓ Migration completed successfully!")
        print(f"  - {rows_copied} visitor records migrated")
        print("  - New fields added: first_visit, interested_in, cobroker_name, is_local, buyer_state,")
        print("    occupation_other, discovery_method, builders_requested, offer_on_table, finalized_contracts, notes")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
