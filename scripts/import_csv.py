#!/usr/bin/env python3
"""
Import visitors from CSV export file
"""
import sqlite3
import csv
import sys
import os
from pathlib import Path

# Database path - use environment variable or default to Docker path
DB_PATH = os.environ.get('DATABASE_PATH', '/data/leads.db')

def import_csv(csv_path):
    """Import visitors from CSV file"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Track statistics
    stats = {
        'agents_created': 0,
        'visitors_created': 0,
        'visitors_skipped': 0,
        'errors': []
    }

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Create agent if doesn't exist
                agent_name = row.get('agent_name')
                agent_cinc_id = row.get('agent_cinc_id')

                if agent_name and agent_cinc_id:
                    # Check if agent exists
                    existing = cursor.execute(
                        "SELECT id FROM agents WHERE cinc_id = ?",
                        (agent_cinc_id,)
                    ).fetchone()

                    if not existing:
                        # Create agent
                        cursor.execute("""
                            INSERT INTO agents (name, cinc_id, active)
                            VALUES (?, ?, 1)
                        """, (agent_name, agent_cinc_id))
                        stats['agents_created'] += 1
                        print(f"✓ Created agent: {agent_name}")

                    # Get agent ID
                    agent = cursor.execute(
                        "SELECT id FROM agents WHERE cinc_id = ?",
                        (agent_cinc_id,)
                    ).fetchone()
                    capturing_agent_id = agent['id']
                else:
                    print(f"⚠ Skipping row - missing agent info: {row.get('buyer_name')}")
                    stats['visitors_skipped'] += 1
                    continue

                # Parse boolean values
                def parse_bool(val):
                    if val in ('1', 'True', 'true', '1.0'):
                        return 1
                    return 0

                # Insert visitor
                cursor.execute("""
                    INSERT INTO visitors (
                        buyer_name, buyer_phone, buyer_email, first_visit,
                        interested_in, purchase_timeline, represented, cobroker_name,
                        is_local, buyer_state, occupation, occupation_other,
                        discovery_method, builders_requested, offer_on_table,
                        finalized_contracts, notes, price_range, location_looking,
                        location_current, capturing_agent_id, site, created_at,
                        cinc_synced, cinc_sync_at, cinc_lead_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('buyer_name'),
                    row.get('buyer_phone') if row.get('buyer_phone') else None,
                    row.get('buyer_email') if row.get('buyer_email') not in ('', 'None@gmail.com') else None,
                    parse_bool(row.get('first_visit', '1')),
                    row.get('interested_in') if row.get('interested_in') else None,
                    row.get('purchase_timeline') if row.get('purchase_timeline') else None,
                    parse_bool(row.get('represented', '0')),
                    row.get('cobroker_name') if row.get('cobroker_name') else None,
                    parse_bool(row.get('is_local', '1')),
                    row.get('buyer_state') if row.get('buyer_state') else None,
                    row.get('occupation') if row.get('occupation') else None,
                    row.get('occupation_other') if row.get('occupation_other') else None,
                    row.get('discovery_method') if row.get('discovery_method') else None,
                    row.get('builders_requested') if row.get('builders_requested') else None,
                    parse_bool(row.get('offer_on_table', '0')),
                    parse_bool(row.get('finalized_contracts', '0')),
                    row.get('notes') if row.get('notes') else None,
                    row.get('price_range') if row.get('price_range') else None,
                    row.get('location_looking') if row.get('location_looking') else None,
                    row.get('location_current') if row.get('location_current') else None,
                    capturing_agent_id,
                    row.get('site'),
                    row.get('created_at'),
                    parse_bool(row.get('cinc_synced', '0')),
                    row.get('cinc_sync_at') if row.get('cinc_sync_at') else None,
                    row.get('cinc_lead_id') if row.get('cinc_lead_id') else None
                ))

                stats['visitors_created'] += 1
                print(f"✓ Imported: {row.get('buyer_name')} ({row.get('site')})")

            except Exception as e:
                error_msg = f"Error importing {row.get('buyer_name', 'Unknown')}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"✗ {error_msg}")

    conn.commit()
    conn.close()

    # Print summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Agents created: {stats['agents_created']}")
    print(f"Visitors created: {stats['visitors_created']}")
    print(f"Visitors skipped: {stats['visitors_skipped']}")
    print(f"Errors: {len(stats['errors'])}")

    if stats['errors']:
        print("\nErrors:")
        for error in stats['errors']:
            print(f"  - {error}")

    return stats

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_csv.py <csv_file_path>")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print(f"Importing data from: {csv_path}")
    print("="*60)

    import_csv(csv_path)
