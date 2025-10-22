"""
Create initial admin user for New Homes Lead Tracker
Run this script after initial deployment to create the first admin user
"""

import sys
import getpass
from main import get_db, get_password_hash

def create_admin_user():
    """Create admin user interactively"""
    print("\n=== Create Admin User ===\n")

    username = input("Enter admin username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)

    password = getpass.getpass("Enter admin password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Error: Passwords do not match")
        sys.exit(1)

    if len(password) < 6:
        print("Error: Password must be at least 6 characters")
        sys.exit(1)

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Check if username exists
            existing = cursor.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if existing:
                print(f"Error: Username '{username}' already exists")
                sys.exit(1)

            # Create admin user
            password_hash = get_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, agent_id, active)
                VALUES (?, ?, 'admin', NULL, 1)
            """, (username, password_hash))

            user_id = cursor.lastrowid

            print(f"\n✅ Admin user created successfully!")
            print(f"   ID: {user_id}")
            print(f"   Username: {username}")
            print(f"   Role: admin")
            print(f"\nYou can now login at: http://localhost:80")

    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_admin_user()
