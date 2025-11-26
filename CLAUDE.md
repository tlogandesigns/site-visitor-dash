# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

New Homes Lead Tracker - A compliance-first lead management system for new home sales agents to capture, track, and sync visitor information with CINC CRM. Built with FastAPI backend, vanilla JavaScript frontend, and SQLite database, deployed via Docker Compose.

**Authentication**: JWT-based authentication with site-based access control:
- **Admin/Super Admin**: Full access to all leads across all sites, can create users, manage agents, view all statistics
- **User**: Site-based access - can view/edit all leads from sites their agent is assigned to (enables team collaboration within communities)

## Project Structure

```
site-visitor-dash/
├── backend/                # FastAPI backend application
│   ├── main.py            # Main FastAPI application with all endpoints
│   ├── schema.sql         # Database schema definition
│   └── requirements.txt   # Python dependencies
├── frontend/              # Static HTML/CSS/JS frontend
│   ├── index.html        # Main application SPA
│   └── analytics.html    # Analytics dashboard
├── scripts/               # Utility scripts
│   ├── import_agents.py           # Import agents from Google Sheets
│   ├── create_admin.py            # Create admin users
│   ├── migrate_users.py           # User table migration
│   ├── migrate_visitors.py        # Visitor table migration
│   └── migrate_agents_sites.py   # Agent-sites many-to-many migration
├── nginx/                 # Nginx configuration
│   └── conf.d/
│       └── default.conf  # Nginx reverse proxy config
├── docs/                  # Documentation
├── data/                  # SQLite database (volume mount)
│   └── leads.db
├── Dockerfile            # API container definition
├── docker-compose.yml    # Multi-service orchestration
├── .env                  # Environment variables (not in git)
├── .env.example          # Example environment file
├── credentials.json      # Google Sheets API credentials (not in git)
└── README.md
```

## Architecture

### Two-Service Docker Setup
- **api** service: FastAPI backend on port 8000 (Python 3.11)
- **nginx** service: Reverse proxy serving static frontend on port 80 (mapped to 8087)

### Key Components
- `backend/main.py` - FastAPI application with all API endpoints and CINC integration
- `frontend/index.html` - Single-page application frontend (Bootstrap 5)
- `backend/schema.sql` - Database schema with agents, visitors, visitor_notes, agent_sites tables
- `scripts/import_agents.py` - Google Sheets import utility for agent onboarding
- `docker-compose.yml` - Service orchestration
- `data/leads.db` - SQLite database (volume-mounted)

### Authentication Flow
1. User logs in via `/login` endpoint with username/password
2. Backend validates credentials and returns JWT token (8-hour expiry)
3. Frontend stores token in localStorage and includes in all API requests via `/api` proxy
4. Backend validates token and enforces role-based access control on each request
5. Users with role="user" can only access visitors where `capturing_agent_id` matches their `agent_id`

### Data Flow
1. Frontend captures visitor information through form
2. POST /visitors creates record in SQLite and triggers CINC sync
3. CINC API sync happens synchronously in `sync_to_cinc()` function
4. Frontend polls /stats for dashboard metrics
5. Notes system allows timestamped follow-ups on any visitor

## Development Commands

### Start Services
```bash
docker-compose up -d              # Start all services in background
docker-compose up -d --build      # Rebuild and start
docker-compose ps                 # Check service status
docker-compose logs -f            # View logs (all services)
docker-compose logs -f api        # View API logs only
```

### Stop Services
```bash
docker-compose down               # Stop and remove containers
docker-compose down -v            # Also remove volumes (DELETES DATA)
```

### Database Operations
```bash
# Access database shell
docker exec -it newhomes-api python
>>> import sqlite3
>>> conn = sqlite3.connect('/data/leads.db')
>>> cursor = conn.cursor()
>>> cursor.execute("SELECT * FROM agents").fetchall()

# Run schema migrations
docker exec -it newhomes-api python scripts/migrate_agents_sites.py

# Backup database
docker exec newhomes-api sqlite3 /data/leads.db ".backup '/data/leads_backup.db'"
docker cp newhomes-api:/data/leads_backup.db ./backups/
```

### Import Agents
```bash
# From Google Sheets (requires credentials.json and GOOGLE_SHEET_KEY in .env)
docker exec -it newhomes-api python scripts/import_agents.py

# View existing agents
docker exec -it newhomes-api python scripts/import_agents.py export
```

### Create Users
```bash
# Create admin user via script
docker exec -it newhomes-api python scripts/create_admin.py

# Or use the API (admin only)
curl -X POST http://localhost:8087/api/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "password123",
    "role": "user",
    "agent_id": 1
  }'
```

### Testing API Endpoints
```bash
# Health check (no auth required)
curl http://localhost:8087/api/

# Login to get token
curl -X POST http://localhost:8087/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Save the access_token from response
TOKEN="your_token_here"

# List visitors (authenticated)
curl http://localhost:8087/api/visitors \
  -H "Authorization: Bearer $TOKEN"

# Get stats (authenticated)
curl http://localhost:8087/api/stats \
  -H "Authorization: Bearer $TOKEN"

# List agents with sites
curl http://localhost:8087/api/agents \
  -H "Authorization: Bearer $TOKEN"
```

### Rebuild After Code Changes
```bash
# Backend changes (Python code in backend/main.py)
docker-compose up -d --build api

# Frontend changes (HTML in frontend/)
docker-compose restart nginx

# Schema changes
docker exec -it newhomes-api python
>>> import sqlite3
>>> conn = sqlite3.connect('/data/leads.db')
>>> with open('schema.sql', 'r') as f:
...     conn.executescript(f.read())
```

## CINC API Integration

### Configuration
- Set `CINC_API_KEY` environment variable in `.env` file
- Each agent must have valid `cinc_id` in database
- API base URL: https://public.cincapi.com
- Docs: https://public.cincapi.com/index.html

### Sync Behavior
- Synchronous sync on visitor creation in `sync_to_cinc()` function (backend/main.py)
- Splits buyer_name into firstName/lastName
- Maps custom fields: purchase_timeline, price_range, locations, occupation, represented status
- Updates `cinc_synced`, `cinc_sync_at`, `cinc_lead_id` columns on success
- Errors logged but don't block visitor creation

## Database Schema Details

### Core Tables
- **users**: Authentication table with username, password_hash, role (admin/user), agent_id (FK to agents). JWT token expiry: 8 hours.
- **agents**: Sales agents with CINC IDs, contact info. Unique constraint on name and cinc_id.
- **agent_sites**: Junction table for many-to-many agent-site relationships
- **visitors**: Lead records with buyer info, capturing agent, site, CINC sync status
- **visitor_notes**: Timestamped follow-up notes linked to visitors and agents
- **communities**: Site/community names (currently unused, legacy table)

### Important View
- **visitor_details**: Denormalized view joining visitors with agent info and latest note

### Indexes
Performance indexes on: buyer_phone, buyer_email, site, created_at, visitor_id (notes), agent_id, agent_sites

## Frontend Architecture

Single-page vanilla JavaScript application in `frontend/index.html`:
- Bootstrap 5 for UI components
- No build process or framework
- Direct API calls to backend via `/api/` proxy (nginx routes to api:8000)
- Real-time dashboard with stats polling
- CSV export functionality
- Site/community filtering
- Agent Management UI (admin only)

## Environment Variables

Required in `.env` file:
- `CINC_API_KEY` - CINC CRM API key (required for lead sync)
- `DATABASE_PATH` - Path to SQLite DB (default: /data/leads.db)
- `JWT_SECRET_KEY` - Secret key for JWT token signing (CHANGE IN PRODUCTION!)
- `GOOGLE_SHEET_KEY` - Google Sheet ID for agent import (optional)
- `WORKSHEET_NAME` - Sheet name for agents (optional, default: "Sheet1")

## Deployment Notes

- Designed for Hostinger VPS or Raspberry Pi 5
- Uses volume mount for persistent database storage
- Nginx handles static files and API proxying
- Cloudflare Tunnel recommended for secure external access
- Database backups should be automated via cron

## Common Issues

### Authentication Issues
- **"Could not validate credentials"**: JWT token expired (8 hours) or invalid. Re-login required.
- **403 Forbidden**: User role doesn't have permission. Check user role in database.
- **Can't access leads**: Users can only see leads where `capturing_agent_id` matches their `agent_id`. Verify user's `agent_id` is set correctly.
- **No agent linked error**: User account must have valid `agent_id` to create visitors/notes. Update user record in database.

### CINC Sync Failures
- Check `CINC_API_KEY` in .env
- Verify agent `cinc_id` values in database
- Review API logs: `docker-compose logs api | grep -i cinc`
- Test CINC API connectivity manually with curl

### Database Locked
- SQLite doesn't handle high concurrency - consider PostgreSQL for production
- Check for long-running transactions
- Restart API service: `docker-compose restart api`

### Frontend Not Loading
- Check nginx config syntax: `docker exec newhomes-nginx nginx -t`
- Verify API is responding: `curl http://localhost:8087/api/`
- Check browser console for JavaScript errors
- Review nginx logs: `docker-compose logs nginx`
- Clear localStorage if authentication issues persist: `localStorage.clear()` in browser console

### Initial Setup
- **No users exist**: After first deployment, create admin user via `scripts/create_admin.py`
- **Can't login**: Ensure database schema is initialized with users table. Run schema.sql if needed.
- **Missing JWT_SECRET_KEY**: Set in .env file or uses default (INSECURE for production)

## Recent Enhancements

### Site-Based Access Control (2025)
- Changed from agent-based to site-based visibility
- Users can now see all leads from sites their agent is assigned to (not just their own)
- Enables team collaboration within communities
- Uses `agent_sites` junction table for many-to-many relationships
- Helper function `get_user_accessible_sites()` centralizes access logic

### Placeholder Generation for Missing Data
- **Email**: Auto-generates `{uuid}@noemail.com` when no email provided
  - Stored in database for consistent lead identification
  - Enables CINC lead lookup and note updates
- **Phone**: Sends `5555555555` to webhook when no phone provided
  - Not stored in database (webhook only)
  - Ensures CINC can process all leads

### CINC Integration Enhancements
- **Note Syncing**: Notes are automatically synced to CINC when added
- **Type Differentiation**: Webhook payloads include `type` field:
  - `type: "lead"` for new lead creation
  - `type: "note"` for note updates
- **Initial Notes**: Notes entered during visitor creation now appear in notes history

### Frontend Improvements
- Phone number validation with real-time feedback (min 10 digits)
- Site field changed to required dropdown
- Price range extended to $1M+
- User tracking: Shows which user created each visitor

### Code Quality
- Migrated to Pydantic V2 validators (future-proof for V3)
- Replaced deprecated `on_event` with modern lifespan handler
- Consolidated site filtering logic into reusable helper function
- Eliminated deprecation warnings

### Database Migrations
- `scripts/migrate_notes.py`: Migrates initial notes from `visitors.notes` to `visitor_notes` table
