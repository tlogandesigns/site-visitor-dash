# Zapier Webhook Setup Guide

This guide will help you set up a Zapier webhook to sync leads from the Lead Tracker to CINC CRM (or any other system).

## Overview

Instead of connecting directly to the CINC API, the Lead Tracker sends lead data to a Zapier webhook. Zapier then handles the integration with CINC or other systems.

**Benefits:**
- ✅ No need for CINC API key
- ✅ Easy to configure without code
- ✅ Can connect to multiple systems (email, Slack, etc.)
- ✅ Built-in error handling and retry logic
- ✅ Activity logging in Zapier dashboard

## Step 1: Create a New Zap

1. Go to [Zapier.com](https://zapier.com) and log in
2. Click **"Create Zap"** (top right)
3. Name it: `Lead Tracker to CINC Sync`

## Step 2: Set Up the Trigger (Catch Webhook)

1. **Choose App**: Search for **"Webhooks by Zapier"**
2. **Choose Event**: Select **"Catch Hook"**
3. Click **"Continue"**
4. **Pick off a Child Key**: Leave blank (optional)
5. Click **"Continue"**
6. **Copy the Custom Webhook URL** - it looks like:
   ```
   https://hooks.zapier.com/hooks/catch/123456/abcdef/
   ```
7. **DO NOT click "Test trigger" yet** - we need to send data first

## Step 3: Configure the Lead Tracker

1. Open your `.env` file
2. Paste the webhook URL:
   ```
   ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/123456/abcdef/
   ```
3. Save the file
4. Restart the application:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Step 4: Send a Test Lead

1. Go to your Lead Tracker: http://localhost
2. Click **"Add New Visitor"**
3. Fill in the form with test data:
   - **Buyer Name**: Test Lead
   - **Phone**: 555-1234
   - **Email**: test@example.com
   - **Agent**: Select any agent
   - **Site**: Select a site
   - Fill in other fields (optional)
4. Click **"Add Visitor"**

The lead will be sent to Zapier!

## Step 5: Test the Trigger in Zapier

1. Go back to Zapier
2. Click **"Test trigger"**
3. You should see the test lead data appear
4. Click **"Continue with selected record"**

## Step 6: Add Action (Send to CINC)

### Option A: CINC CRM Integration

1. **Choose App**: Search for your CINC integration
   - If CINC has a direct Zapier app, select it
   - Otherwise, use **"Webhooks by Zapier"** → **"POST"**

2. **For Direct CINC Integration:**
   - Follow CINC's Zapier integration steps
   - Map the fields:
     - First Name → `firstName`
     - Last Name → `lastName`
     - Email → `email`
     - Phone → `phone`
     - Agent ID → `agentCincId`
     - etc.

3. **For Webhook POST to CINC API:**
   - URL: `https://public.cincapi.com/leads`
   - Method: POST
   - Headers:
     ```
     Authorization: Bearer YOUR_CINC_API_KEY
     Content-Type: application/json
     ```
   - Data:
     ```json
     {
       "firstName": (map from trigger data),
       "lastName": (map from trigger data),
       "email": (map from trigger data),
       "phone": (map from trigger data),
       "agentId": (map from trigger: agentCincId),
       "source": "New Homes Lead Tracker"
     }
     ```

### Option B: Other Integrations

You can add additional actions:
- **Email**: Send notification to agent
- **Slack**: Post to channel
- **Google Sheets**: Log to spreadsheet
- **Salesforce**: Create lead
- etc.

## Step 7: Test the Action

1. Click **"Test action"**
2. Verify the lead was created in CINC (or your target system)
3. Click **"Continue"**

## Step 8: Turn On the Zap

1. Click **"Publish"** or **"Turn on Zap"**
2. Your Zap is now live!

## Data Fields Sent to Zapier

The Lead Tracker sends the following fields:

### Buyer Information
- `firstName` - First name
- `lastName` - Last name
- `fullName` - Full name
- `email` - Email address
- `phone` - Phone number

### Agent Information
- `agentName` - Agent's name
- `agentEmail` - Agent's email
- `agentCincId` - Agent's CINC ID (use this for CINC agent mapping)
- `site` - Site/Community name

### Lead Details
- `purchaseTimeline` - When they plan to buy
- `priceRange` - Price range
- `locationLooking` - Where they're looking
- `locationCurrent` - Current location
- `occupation` - Buyer's occupation
- `represented` - "Yes" or "No"
- `representingAgent` - Agent's name if represented

### Metadata
- `source` - Always "New Homes Lead Tracker"
- `notes` - Any notes added
- `timestamp` - When lead was captured (ISO format)
- `visitDate` - Visit date (ISO format)

## Testing

### Test Without Zapier URL (Development)

If `ZAPIER_WEBHOOK_URL` is not set, leads will still be saved to the database, but won't sync. This is useful for testing.

### View Zapier Activity

1. Go to Zapier Dashboard
2. Click on your Zap
3. Click **"Zap History"**
4. See all webhook calls and their status

### Troubleshooting

**Lead not appearing in Zapier:**
- Check that ZAPIER_WEBHOOK_URL is set in `.env`
- Restart the application after updating `.env`
- Check the browser console for errors
- Verify the webhook URL is correct (no extra spaces)

**Zap not triggering:**
- Make sure the Zap is turned ON
- Check Zap History for errors
- Verify the webhook URL hasn't changed

**Data mapping issues:**
- In Zapier, click "Refresh fields" to see all available data
- Use the test lead to verify field names
- Check that required CINC fields are mapped

**CINC errors:**
- Verify `agentCincId` is being sent correctly
- Check that the CINC API key is valid (if using webhook POST)
- Ensure all required CINC fields are provided

## Advanced: Multiple Actions

You can add multiple actions to one Zap:

1. **Action 1**: Send to CINC
2. **Action 2**: Send email to agent
3. **Action 3**: Post to Slack channel
4. **Action 4**: Log to Google Sheets

All will trigger when a new lead is captured!

## Monitoring

**Zapier Dashboard:**
- View success/failure rates
- See recent webhook calls
- Debug errors

**Lead Tracker:**
- Check "CINC Synced" column in visitors table
- If synced successfully, `cinc_synced` = 1
- If failed, check `sync_error` in the response

## Example Zap Workflow

```
New Lead Captured
    ↓
Zapier Webhook (Trigger)
    ↓
Filter: Only if email exists (optional)
    ↓
Send to CINC API (Action 1)
    ↓
Send Email to Agent (Action 2)
    ↓
Post to Slack (Action 3)
```

## Need Help?

- Zapier Help: https://help.zapier.com/
- CINC API Docs: https://public.cincapi.com/index.html
- Check Zapier's error messages in Zap History
