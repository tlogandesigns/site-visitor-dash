"""
Migration script to update users table with email column and super_admin role
"""

import sqlite3
import os

DATABASE_PATH = os.getenv('DATABASE_PATH', '/data/leads.db')

def migrate():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Create new users table with correct schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin', 'user')),
                agent_id INTEGER,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        """)

        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO users_new (id, username, password_hash, email, role, agent_id, active, created_at, last_login)
            SELECT id, username, password_hash, email, role, agent_id, active, created_at, last_login
            FROM users
        """)

        # Drop old table
        cursor.execute("DROP TABLE users")

        # Rename new table
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # Recreate index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_agent_id ON users(agent_id)")

        conn.commit()
        print("✅ Users table migrated successfully!")
        print("   - Added email column")
        print("   - Added super_admin role to CHECK constraint")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
