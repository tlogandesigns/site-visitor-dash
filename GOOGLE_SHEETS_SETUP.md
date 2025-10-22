# Google Sheets Import Setup Guide

This guide will help you import agents from your Google Sheet into the database.

## Prerequisites

Your Google Sheet should have these columns (in this order):
- **Agent Name** - Full name of the agent
- **CINC ID** - The agent's CINC CRM ID
- **Site** - The community/site name
- **Email** - Agent's email (optional)
- **Phone** - Agent's phone (optional)

## Step 1: Get Your Google Sheet ID

1. Open your Google Sheet in a browser
2. Look at the URL, it will look like:
   ```
   https://docs.google.com/spreadsheets/d/1ABC123xyz-LONG_STRING_HERE/edit
   ```
3. Copy the long string between `/d/` and `/edit` - this is your **SHEET_ID**

## Step 2: Create Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing):
   - Click the project dropdown at the top
   - Click "New Project"
   - Name it something like "Lead Tracker Import"
   - Click "Create"

3. Enable required APIs:
   - Click "☰ Menu" → "APIs & Services" → "Library"
   - Search for "Google Sheets API" → Click it → Click "Enable"
   - Search for "Google Drive API" → Click it → Click "Enable"

4. Create Service Account:
   - Click "☰ Menu" → "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name: `sheets-importer`
   - Description: `Import agents from Google Sheets`
   - Click "Create and Continue"
   - Skip the permissions (click "Continue")
   - Click "Done"

5. Create and Download Key:
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON" format
   - Click "Create"
   - The file will download automatically

6. Save the credentials file:
   - Rename the downloaded file to `credentials.json`
   - Move it to your project directory: `/Users/loganeason/Desktop/site-visitor-dash/credentials.json`

## Step 3: Share Your Google Sheet with Service Account

1. Open the downloaded `credentials.json` file
2. Look for the `client_email` field - it looks like:
   ```
   sheets-importer@your-project.iam.gserviceaccount.com
   ```
3. Copy this email address
4. Go back to your Google Sheet
5. Click the "Share" button (top right)
6. Paste the service account email
7. Make sure role is set to "Viewer"
8. Uncheck "Notify people" (the service account won't receive emails)
9. Click "Share"

## Step 4: Update Environment Variables

1. Open `.env` file in your project
2. Update these lines:
   ```
   GOOGLE_SHEET_KEY=YOUR_ACTUAL_SHEET_ID_FROM_STEP_1
   WORKSHEET_NAME=Sheet1
   ```
   - Replace `YOUR_ACTUAL_SHEET_ID_FROM_STEP_1` with your actual sheet ID
   - If your sheet tab has a different name, update `WORKSHEET_NAME`

## Step 5: Rebuild and Import

1. Make sure `credentials.json` is in your project directory
2. Rebuild the Docker container:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

3. Run the import:
   ```bash
   docker exec newhomes-api python import_agents.py
   ```

4. You should see output like:
   ```
   Connecting to Google Sheets...
   Found 10 agents in sheet
   ✓ Imported: John Doe (Cedar Creek)
   ✓ Imported: Jane Smith (Oak Ridge)
   ...
   ✅ Import complete!
      Imported: 10
      Skipped: 0
   ```

## Step 6: Verify Import

Check that agents were imported:
```bash
docker exec newhomes-api python import_agents.py export
```

This will show you all agents currently in the database.

## Troubleshooting

### "Error: credentials.json not found"
- Make sure the file is named exactly `credentials.json` (no extra extensions)
- Place it in `/Users/loganeason/Desktop/site-visitor-dash/`
- Rebuild the container: `docker-compose up -d --build`

### "Error: Permission denied"
- Make sure you shared the Google Sheet with the service account email
- The service account needs at least "Viewer" access

### "Error: Invalid sheet key"
- Double-check the GOOGLE_SHEET_KEY in your .env file
- It should be just the ID, not the full URL

### "Error: Worksheet not found"
- Check the tab name at the bottom of your Google Sheet
- Update WORKSHEET_NAME in .env to match exactly (case-sensitive)

## Re-importing / Updating

The import script uses `INSERT OR IGNORE`, which means:
- Existing agents (same name + site) will be skipped
- Only new agents will be added

To update existing agents, you would need to delete them first or modify the import script.

## Next Steps

After importing agents:
1. Log into the web interface
2. Go to "User Management" tab
3. Create users and link them to the imported agents
4. Users with role="user" must be linked to an agent to create leads
