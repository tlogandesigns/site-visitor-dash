# 🏘️ New Homes Lead Tracker

**Compliance-first lead management system with CINC integration**

Built for new home sales agents to capture, track, and sync visitor information seamlessly.

---

## ✨ Features

- **🔐 Authentication:** Secure login with role-based access control
  - **Admin:** Full access to all leads, user management
  - **User:** Access only to leads they created
- **Lead Capture:** Quickly input visitor information on-site
- **CINC Integration:** Automatic sync to CINC CRM via API
- **Timestamped Notes:** Add follow-up notes to any visitor
- **Dashboard View:** Real-time statistics and lead overview
- **Export:** CSV export for reporting and analysis
- **Multi-Site:** Filter by community/site
- **Responsive:** Works on tablets and mobile devices

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- CINC API Key
- Google Sheets with agent data (optional)

### 1. Clone/Download Files

```bash
# Create project directory
mkdir newhomes-tracker
cd newhomes-tracker

# Copy all project files here
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required configuration:**
```
CINC_API_KEY=your_actual_cinc_api_key
JWT_SECRET_KEY=your-random-secret-key-change-this
```

**Generate a secure secret key:**
```bash
# Use Python to generate a random secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Import Agents (One-time Setup)

**Option A: Manual Database Entry**

```bash
# Start the database
docker-compose up -d api

# Connect to container
docker exec -it newhomes-api python

# In Python shell:
import sqlite3
conn = sqlite3.connect('/data/leads.db')
cursor = conn.cursor()

# Add agents
cursor.execute("""
    INSERT INTO agents (name, cinc_id, site, email, phone)
    VALUES ('John Smith', 'CINC_ID_123', 'Cedar Creek', 'john@example.com', '555-1234')
""")

conn.commit()
conn.close()
```

**Option B: Google Sheets Import**

1. Create Google Service Account credentials
2. Share your agent spreadsheet with service account email
3. Add credentials.json to project root
4. Update GOOGLE_SHEET_KEY in .env
5. Run import:

```bash
docker exec -it newhomes-api python import_agents.py
```

### 4. Launch Application

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Create Initial Admin User

**IMPORTANT:** After first deployment, you must create an admin user to login.

**Option A: Interactive Script (Recommended)**
```bash
docker exec -it newhomes-api python create_admin.py
```

**Option B: Manual via Python Shell**
```bash
docker exec -it newhomes-api python

# In Python shell:
from main import get_db, get_password_hash

with get_db() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, agent_id)
        VALUES (?, ?, 'admin', NULL)
    """, ('admin', get_password_hash('admin123')))
    print(f"Admin user created with ID: {cursor.lastrowid}")
```

### 6. Access Dashboard

Open browser: **http://localhost** or **http://your-server-ip**

**Default credentials (if using Option B above):**
- Username: `admin`
- Password: `admin123`

**⚠️ IMPORTANT:** Change the admin password immediately after first login!

---

## 👥 User Management

### Creating Additional Users

After creating the initial admin user, you can add more users through the admin interface or API.

**Via Python Shell:**
```bash
docker exec -it newhomes-api python

# In Python shell:
from main import get_db, get_password_hash

# Create regular user linked to an agent
with get_db() as conn:
    cursor = conn.cursor()
    # First, find the agent_id
    agent = cursor.execute("SELECT id, name FROM agents WHERE name = 'John Smith'").fetchone()
    print(f"Agent ID: {agent['id']}, Name: {agent['name']}")

    # Create user linked to this agent
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, agent_id)
        VALUES (?, ?, 'user', ?)
    """, ('john.smith', get_password_hash('password123'), agent['id']))
    print(f"User created with ID: {cursor.lastrowid}")
```

**Via API (Admin only):**
```bash
# First, login as admin to get token
TOKEN=$(curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# Create new user
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.smith",
    "password": "password123",
    "role": "user",
    "agent_id": 1
  }'

# List all users
curl http://localhost:8000/users \
  -H "Authorization: Bearer $TOKEN"
```

### User Roles

- **admin**: Can view all leads, manage users, full system access
- **user**: Can only view/create leads they captured, must be linked to an agent via `agent_id`

---

## 📊 Database Schema

### Tables

**users** *(NEW)*
- `id` - Primary key
- `username` - Unique username for login
- `password_hash` - Bcrypt hashed password
- `role` - User role: 'admin' or 'user'
- `agent_id` - Foreign key to agents (required for 'user' role)
- `active` - Account status
- `last_login` - Last login timestamp

**agents**
- `id` - Primary key
- `name` - Agent name
- `cinc_id` - CINC CRM ID
- `site` - Community/site name
- `email` - Agent email
- `phone` - Agent phone
- `active` - Active status

**visitors**
- `id` - Primary key
- Buyer fields: name, phone, email, timeline, price range, locations, occupation
- `represented` - Has agent?
- `agent_name` - Representing agent
- `capturing_agent_id` - Agent who logged visit
- `site` - Community visited
- `cinc_synced` - Synced to CINC?
- `cinc_lead_id` - CINC lead ID
- Timestamps

**visitor_notes**
- `id` - Primary key
- `visitor_id` - Foreign key
- `agent_id` - Agent who added note
- `note` - Note text
- `created_at` - Timestamp

---

## 🔧 API Endpoints

### Visitors

**POST /visitors**
Create new visitor and sync to CINC
```json
{
  "buyer_name": "Jane Doe",
  "buyer_phone": "555-0100",
  "buyer_email": "jane@example.com",
  "purchase_timeline": "3-6 months",
  "price_range": "$300k-$400k",
  "location_looking": "Augusta",
  "location_current": "Atlanta",
  "occupation": "Teacher",
  "represented": false,
  "capturing_agent_id": 1,
  "site": "Cedar Creek",
  "notes": "Interested in 3BR homes"
}
```

**GET /visitors**
List all visitors (optional `site` parameter)

**GET /visitors/{id}**
Get visitor details with all notes

**POST /visitors/{id}/notes**
Add timestamped note to visitor

**GET /visitors/export/csv**
Export to CSV (optional `site` parameter)

### Agents

**POST /agents**
Create new agent

**GET /agents**
List all agents (optional `site` parameter)

### Statistics

**GET /stats**
Get dashboard statistics (optional `site` parameter)

**GET /sites**
Get list of all sites/communities

---

## 🔐 CINC API Integration

The system syncs leads to CINC using their public API: https://public.cincapi.com/index.html

### Configuration

1. Obtain CINC API key from your account
2. Add to `.env` file: `CINC_API_KEY=your_key`
3. Ensure agent CINC IDs are correct in database

### What Gets Synced

- Buyer name (split into first/last)
- Email and phone
- Source: "New Homes Lead Tracker"
- Initial notes
- Custom fields:
  - Purchase timeline
  - Price range
  - Locations
  - Occupation
  - Represented status

### Sync Status

- Green badge: Successfully synced
- Yellow badge: Pending/failed sync
- Check logs for sync errors

---

## 🌐 Production Deployment

### Hostinger VPS Deployment

1. **Upload files via SFTP/FileZilla**

2. **SSH into server:**
```bash
ssh user@your-server-ip
cd /path/to/newhomes-tracker
```

3. **Configure environment:**
```bash
nano .env
# Add your CINC_API_KEY
```

4. **Start services:**
```bash
docker-compose up -d
```

5. **Setup Cloudflare Tunnel (optional):**
```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# Login
./cloudflared tunnel login

# Create tunnel
./cloudflared tunnel create newhomes-tracker

# Configure tunnel
nano ~/.cloudflared/config.yml
```

**config.yml:**
```yaml
url: http://localhost:80
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json
```

6. **Run tunnel:**
```bash
./cloudflared tunnel run newhomes-tracker
```

### Raspberry Pi 5 Deployment

Same process as VPS. Ensure Docker is installed:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

---

## 📱 Mobile Access

The dashboard is fully responsive and works on:
- Tablets (iPad, Android tablets)
- Mobile phones (iOS, Android)
- Desktop browsers

**Recommended:** Save to home screen for app-like experience

---

## 🔄 Backup & Maintenance

### Backup Database

```bash
# Automated backup script
docker exec newhomes-api sqlite3 /data/leads.db ".backup '/data/leads_backup.db'"

# Copy to host
docker cp newhomes-api:/data/leads_backup.db ./backups/leads_$(date +%Y%m%d).db
```

### Backup to Backblaze/Wasabi

```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure remote
rclone config

# Sync backups
rclone sync ./backups/ remote:newhomes-backups/
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🐛 Troubleshooting

### CINC Sync Failures

1. Check API key in .env
2. Verify agent CINC IDs are correct
3. Check logs: `docker-compose logs api`
4. Test CINC API manually:
```bash
curl -X POST https://public.cincapi.com/leads \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Test","lastName":"Lead","email":"test@test.com"}'
```

### Database Issues

```bash
# Check database integrity
docker exec newhomes-api sqlite3 /data/leads.db "PRAGMA integrity_check;"

# Reset database (WARNING: deletes all data)
docker-compose down
rm -rf data/leads.db
docker-compose up -d
```

### Frontend Not Loading

1. Check nginx logs: `docker-compose logs nginx`
2. Verify API is running: `curl http://localhost:8000/`
3. Check browser console for errors

---

## 📈 Future Enhancements

- [ ] User authentication (agent login)
- [ ] Email notifications on new leads
- [ ] SMS follow-up reminders
- [ ] Advanced reporting & analytics
- [ ] Integration with showing management systems
- [ ] Automated lead scoring
- [ ] Mobile app (React Native)

---

## 🤝 Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review CINC API docs: https://public.cincapi.com/index.html
3. Contact system administrator

---

## 📄 License

Proprietary - Berkshire Hathaway HomeServices Beazley, REALTORS

**Built with:**
- FastAPI (Python)
- Bootstrap 5
- SQLite
- Docker
- CINC API

---

**Developed by Logan Eason**  
Director of Innovation & Digital Solutions
