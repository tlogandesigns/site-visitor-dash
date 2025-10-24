#!/usr/bin/env python3
"""
Database migration script to convert agents table to many-to-many with sites
"""

import sqlite3
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/leads.db")

def migrate():
    """Migrate agents table to support many-to-many relationship with sites"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print("Starting migration of agents table to many-to-many with sites...")

    try:
        # Check if migration has already been completed by checking if agents table still has 'site' column
        cursor.execute("PRAGMA table_info(agents)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'site' not in columns:
            print("✓ Migration already completed (agents table does not have 'site' column)")
            return

        # Get existing agents data
        cursor.execute("SELECT id, name, cinc_id, site, email, phone, active, created_at FROM agents")
        existing_agents = cursor.fetchall()
        print(f"Found {len(existing_agents)} existing agent records...")

        # Create new agents table without site column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                cinc_id TEXT NOT NULL UNIQUE,
                email TEXT,
                phone TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created new agents table...")

        # Create agent_sites junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL,
                site TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                UNIQUE(agent_id, site)
            )
        """)
        print("Created agent_sites junction table...")

        # Migrate data - group agents by name and combine sites
        agent_map = {}  # Map of name -> (cinc_id, email, phone, active, created_at, [sites])

        for old_id, name, cinc_id, site, email, phone, active, created_at in existing_agents:
            if name not in agent_map:
                agent_map[name] = {
                    'cinc_id': cinc_id,
                    'email': email,
                    'phone': phone,
                    'active': active,
                    'created_at': created_at,
                    'sites': [],
                    'old_ids': []
                }
            agent_map[name]['sites'].append(site)
            agent_map[name]['old_ids'].append(old_id)

        # Insert unique agents
        new_agent_id_map = {}  # Map old_id -> new_id
        for name, data in agent_map.items():
            cursor.execute("""
                INSERT OR REPLACE INTO agents_new (name, cinc_id, email, phone, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, data['cinc_id'], data['email'], data['phone'], data['active'], data['created_at']))

            new_id = cursor.lastrowid
            for old_id in data['old_ids']:
                new_agent_id_map[old_id] = new_id

            # Insert agent-site relationships
            for site in data['sites']:
                cursor.execute("""
                    INSERT OR IGNORE INTO agent_sites (agent_id, site)
                    VALUES (?, ?)
                """, (new_id, site))

            print(f"✓ Migrated: {name} ({len(data['sites'])} site(s))")

        print(f"Migrated {len(agent_map)} unique agents...")

        # Update users table - map old agent_id to new agent_id
        cursor.execute("SELECT id, agent_id FROM users WHERE agent_id IS NOT NULL")
        users_to_update = cursor.fetchall()

        for user_id, old_agent_id in users_to_update:
            if old_agent_id in new_agent_id_map:
                new_id = new_agent_id_map[old_agent_id]
                cursor.execute("UPDATE users SET agent_id = ? WHERE id = ?", (new_id, user_id))

        print(f"Updated {len(users_to_update)} user agent references...")

        # Drop the visitor_details view that depends on agents table
        cursor.execute("DROP VIEW IF EXISTS visitor_details")
        print("Dropped visitor_details view...")

        # Drop old agents table
        cursor.execute("DROP TABLE agents")
        print("Dropped old agents table...")

        # Rename new table
        cursor.execute("ALTER TABLE agents_new RENAME TO agents")
        print("Renamed new table to agents...")

        # Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_cinc_id ON agents(cinc_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_sites_agent_id ON agent_sites(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_sites_site ON agent_sites(site)")
        print("Recreated indexes...")

        # Recreate visitor_details view
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
        print("\n✓ Migration completed successfully!")
        print(f"  - {len(agent_map)} unique agents")
        print(f"  - {sum(len(data['sites']) for data in agent_map.values())} agent-site relationships")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
