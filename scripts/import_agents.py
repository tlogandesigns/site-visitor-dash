"""
Import agents from Google Sheets to database
Requires: pip install gspread oauth2client
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3
import sys
import os

# Configuration
GOOGLE_SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY", "YOUR_SHEET_KEY_HERE")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Agents")
DATABASE_PATH = os.getenv("DATABASE_PATH", "leads.db")

# Expected columns in Google Sheet:
# site_agent_name | agent_mdid | Site | Email | Phone

def connect_to_sheet():
    """Connect to Google Sheets"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    # Try to find credentials.json in multiple locations
    credentials_path = None
    for path in ['/credentials.json', 'credentials.json', '/app/credentials.json']:
        if os.path.exists(path):
            credentials_path = path
            break

    if not credentials_path:
        raise FileNotFoundError("credentials.json not found. Please place it in the project directory.")

    # Use service account credentials
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    
    # Open the sheet
    sheet = client.open_by_key(GOOGLE_SHEET_KEY)
    worksheet = sheet.worksheet(WORKSHEET_NAME)
    
    return worksheet

def import_agents():
    """Import agents from Google Sheet to database"""
    try:
        print("Connecting to Google Sheets...")
        worksheet = connect_to_sheet()
        
        # Get all records
        records = worksheet.get_all_records()
        print(f"Found {len(records)} agents in sheet")
        
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        imported = 0
        skipped = 0
        
        for record in records:
            try:
                agent_name = record.get('site_agent_name', '').strip()
                cinc_id = record.get('agent_mdid', '').strip()
                # Try both 'site' and 'Site' column names - can be comma-separated for multiple sites
                sites_str = record.get('site', '').strip() or record.get('Site', '').strip() or record.get('sites', '').strip() or record.get('Sites', '').strip()
                # Try various email column names
                email = record.get('site_agent_email', '').strip() or record.get('Email', '').strip() or record.get('email', '').strip()
                phone = record.get('Phone', '').strip() or record.get('phone', '').strip()

                if not agent_name or not cinc_id:
                    print(f"Skipping incomplete record (missing required fields): agent_name='{agent_name}', cinc_id='{cinc_id}'")
                    skipped += 1
                    continue

                # Parse sites - can be comma-separated or single site
                # If no sites provided, agent will be created without site assignments
                sites = [s.strip() for s in sites_str.split(',') if s.strip()] if sites_str else []

                # Insert or update agent
                cursor.execute("""
                    INSERT INTO agents (name, cinc_id, email, phone)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(cinc_id) DO UPDATE SET
                        name = excluded.name,
                        email = excluded.email,
                        phone = excluded.phone
                """, (agent_name, cinc_id, email or None, phone or None))

                # Get agent_id (either newly inserted or existing)
                cursor.execute("SELECT id FROM agents WHERE cinc_id = ?", (cinc_id,))
                agent_id = cursor.fetchone()[0]

                # Clear existing site assignments for this agent (we'll re-add them)
                cursor.execute("DELETE FROM agent_sites WHERE agent_id = ?", (agent_id,))

                # Add site assignments
                sites_added = 0
                if sites:
                    for site in sites:
                        cursor.execute("""
                            INSERT OR IGNORE INTO agent_sites (agent_id, site)
                            VALUES (?, ?)
                        """, (agent_id, site))
                        sites_added += 1

                    print(f"✓ Imported: {agent_name} ({sites_added} site(s): {', '.join(sites)})")
                else:
                    print(f"✓ Imported: {agent_name} (no sites assigned)")

                imported += 1

            except Exception as e:
                print(f"Error importing {record}: {e}")
                skipped += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Import complete!")
        print(f"   Imported: {imported}")
        print(f"   Skipped: {skipped}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def export_agents_template():
    """Export current agents to see format"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    agents = cursor.execute("SELECT name, cinc_id, site, email, phone FROM agents").fetchall()
    
    print("\nCurrent Agents:")
    print("-" * 80)
    print(f"{'Agent Name':<30} {'CINC ID':<20} {'Site':<20} {'Email':<30}")
    print("-" * 80)
    
    for agent in agents:
        print(f"{agent[0]:<30} {agent[1]:<20} {agent[2]:<20} {agent[3] or '':<30}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "export":
        export_agents_template()
    else:
        import_agents()
