# Quick Start: Import Agents from Google Sheets

Your spreadsheet is already configured! You just need to set up Google API access.

## Current Configuration ✓

- ✅ Sheet ID: `1xSZdTmqO3BOafQcFP8uOw0KWJIlp0igSmTe3lm1LIPk`
- ✅ Worksheet: `site_agents`
- ✅ Column mapping:
  - `site_agent_name` → Agent Name
  - `agent_mdid` → CINC ID
  - `Site` → Site/Community
  - `Email` → Email (optional)
  - `Phone` → Phone (optional)

## What You Need to Do

### Step 1: Create Google Cloud Project (5 minutes)

1. Go to: https://console.cloud.google.com/
2. Click **"Select a project"** dropdown at top → **"NEW PROJECT"**
3. Project name: `LeadTracker`
4. Click **"CREATE"**
5. Wait for project to be created (you'll see a notification)

### Step 2: Enable APIs (2 minutes)

1. Make sure your new project is selected at the top
2. Click **☰ Menu** → **"APIs & Services"** → **"Library"**
3. Search for **"Google Sheets API"** → Click it → Click **"ENABLE"**
4. Click **← back arrow** (or use browser back)
5. Search for **"Google Drive API"** → Click it → Click **"ENABLE"**

### Step 3: Create Service Account (3 minutes)

1. Click **☰ Menu** → **"IAM & Admin"** → **"Service Accounts"**
2. Click **"+ CREATE SERVICE ACCOUNT"** (at top)
3. Fill in:
   - **Service account name**: `sheets-importer`
   - **Service account ID**: (auto-filled, leave it)
   - **Description**: `Import agents from Google Sheets`
4. Click **"CREATE AND CONTINUE"**
5. Skip step 2 (Grant access) - just click **"CONTINUE"**
6. Skip step 3 - click **"DONE"**

### Step 4: Create & Download Key (2 minutes)

1. You should see your new service account in the list
2. Click on **`sheets-importer@...`** (the one you just created)
3. Click the **"KEYS"** tab at the top
4. Click **"ADD KEY"** → **"Create new key"**
5. Choose **"JSON"** format
6. Click **"CREATE"**
7. A file will download automatically (looks like `leadtracker-abc123.json`)
8. **IMPORTANT:** Rename this file to exactly: `credentials.json`
9. Move it to: `/Users/loganeason/Desktop/site-visitor-dash/credentials.json`

### Step 5: Share Your Google Sheet (1 minute)

1. Open the downloaded `credentials.json` in a text editor
2. Find and copy the email that looks like:
   ```
   "client_email": "sheets-importer@leadtracker-xxxxx.iam.gserviceaccount.com"
   ```
3. Go to your Google Sheet: https://docs.google.com/spreadsheets/d/1xSZdTmqO3BOafQcFP8uOw0KWJIlp0igSmTe3lm1LIPk/edit
4. Click **"Share"** button (top right)
5. Paste the service account email
6. Set permission to **"Viewer"**
7. **Uncheck** "Notify people"
8. Click **"Share"**

### Step 6: Run Import! (1 minute)

```bash
# Rebuild container with new dependencies
docker-compose down
docker-compose up -d --build

# Run the import
docker exec newhomes-api python import_agents.py
```

You should see:
```
Connecting to Google Sheets...
Found X agents in sheet
✓ Imported: Agent Name (Site)
✓ Imported: Agent Name (Site)
...
✅ Import complete!
   Imported: X
   Skipped: 0
```

## Verify Import

Check imported agents:
```bash
docker exec newhomes-api python import_agents.py export
```

Or view in the web interface:
1. Log in to http://localhost
2. The agent dropdown should now be populated when creating visitors

## Troubleshooting

**"credentials.json not found"**
- Make sure file is named exactly `credentials.json` (not `credentials.json.txt`)
- Place it in `/Users/loganeason/Desktop/site-visitor-dash/`
- Run: `ls -la credentials.json` to verify

**"Permission denied" or "The caller does not have permission"**
- Double-check you shared the sheet with the service account email
- Make sure you gave it "Viewer" permission
- Wait a minute and try again (permissions can take a moment)

**"Worksheet 'site_agents' not found"**
- Check the tab name at the bottom of your Google Sheet
- It must be exactly `site_agents` (case-sensitive)
- Update WORKSHEET_NAME in .env if different

**Need to re-import?**
The import uses `INSERT OR IGNORE`, so:
- Existing agents (same name + site) are skipped
- Only new agents are added
- To update existing agents, you'd need to delete them from the database first

## Next Steps After Import

1. **Create Users**: Go to "User Management" tab and create user accounts
2. **Link to Agents**: When creating users with role="user", select their agent from dropdown
3. **Test**: Try creating a new visitor - you should see agents in the dropdown
