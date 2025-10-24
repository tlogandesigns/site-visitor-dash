# Deployment Guide

## Quick Deploy to Server (72.60.116.213)

### Prerequisites
- Docker and Docker Compose installed on server
- Git installed (or ability to upload files)
- Port 8087 available

### Deployment Steps

#### 1. Get Code on Server

**Option A: Using Git (Recommended)**
```bash
# SSH into server
ssh user@72.60.116.213

# Clone or pull latest code
cd /path/to/deploy
git pull origin main  # or git clone if first time
```

**Option B: Manual Upload**
```bash
# From your local machine, sync files to server
rsync -avz --exclude 'data' --exclude '.git' \
  /Users/loganeason/Desktop/site-visitor-dash/ \
  user@72.60.116.213:/path/to/deploy/
```

#### 2. Set Up Environment

```bash
# SSH into server
ssh user@72.60.116.213
cd /path/to/deploy

# Create .env file (copy from .env.example)
cp .env.example .env

# Edit .env with production values
nano .env
```

Required `.env` variables:
```
JWT_SECRET_KEY=<generate-a-strong-random-key>
SUPER_ADMIN_PASSWORD=<strong-password>
CINC_API_KEY=<your-cinc-api-key>
GOOGLE_SHEET_KEY=<your-sheet-id>
WORKSHEET_NAME=Sheet1
DATABASE_PATH=/data/leads.db
```

#### 3. Upload Google Sheets Credentials

```bash
# Upload credentials.json to server
scp credentials.json user@72.60.116.213:/path/to/deploy/
```

#### 4. Deploy Application

```bash
# SSH into server
ssh user@72.60.116.213
cd /path/to/deploy

# Stop any existing containers
docker-compose down

# Build and start services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 5. Verify Deployment

```bash
# Test API
curl http://localhost:8087/api/

# Test frontend
curl http://localhost:8087/
```

Access application at: **http://72.60.116.213:8087**

### Post-Deployment

#### Create Admin User

```bash
docker exec -it newhomes-api python scripts/create_admin.py
```

#### Import Agents

```bash
docker exec -it newhomes-api python scripts/import_agents.py
```

#### View Logs

```bash
# All logs
docker-compose logs -f

# API only
docker-compose logs -f api

# Nginx only
docker-compose logs -f nginx

# Last 100 lines
docker-compose logs --tail=100
```

### Troubleshooting

#### 403 Error - Frontend Not Loading

**Problem**: nginx returns 403 Forbidden
**Cause**: Frontend files not baked into nginx image
**Solution**: Rebuild nginx with `docker-compose up -d --build nginx`

#### Can't Connect to Database

**Problem**: Database not found
**Solution**: Check data volume and permissions
```bash
docker-compose down
docker volume ls
docker-compose up -d
```

#### API Not Responding

**Problem**: Backend container crashed
**Solution**: Check logs and restart
```bash
docker-compose logs api
docker-compose restart api
```

### Updating Application

```bash
# SSH into server
ssh user@72.60.116.213
cd /path/to/deploy

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Check everything is running
docker-compose ps
```

### Backup Database

```bash
# Create backup
docker exec newhomes-api sqlite3 /data/leads.db ".backup '/data/backup-$(date +%Y%m%d).db'"

# Copy to host
docker cp newhomes-api:/data/backup-$(date +%Y%m%d).db ./backups/

# Download from server
scp user@72.60.116.213:/path/to/deploy/backups/backup-*.db ./local-backups/
```

### Production Checklist

- [ ] Change `JWT_SECRET_KEY` from default
- [ ] Change `SUPER_ADMIN_PASSWORD` from default
- [ ] Set up HTTPS with SSL certificate (Cloudflare Tunnel recommended)
- [ ] Configure firewall to allow only necessary ports
- [ ] Set up automated database backups (cron job)
- [ ] Configure log rotation
- [ ] Test CINC API integration
- [ ] Import all agents from Google Sheets
- [ ] Create user accounts for team members
- [ ] Test agent management features

### Security Notes

**Important**: The current setup uses HTTP on port 8087. For production:

1. **Use HTTPS**: Set up Cloudflare Tunnel or reverse proxy with SSL
2. **Change Secrets**: Update all default passwords and keys
3. **Restrict Access**: Use firewall rules or VPN
4. **Regular Backups**: Automate database backups
5. **Update Regularly**: Keep Docker images and dependencies updated

### Port Configuration

If you need to change the port from 8087:

1. Edit `docker-compose.yml`:
   ```yaml
   nginx:
     ports:
       - "YOUR_PORT:80"  # Change 8087 to your preferred port
   ```

2. Rebuild:
   ```bash
   docker-compose up -d --build
   ```

### Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify environment: `docker-compose ps`
3. Test connectivity: `curl http://localhost:8087/api/`
4. Review CLAUDE.md for detailed documentation
