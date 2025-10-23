# New Homes Lead Tracker - Documentation

This folder contains detailed documentation for the New Homes Lead Tracker application.

## 📖 Available Documentation

### Getting Started

- **[../README.md](../README.md)** - Main README with quick start guide and overview

### Setup Guides

- **[GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)** - Complete guide to setting up Google Sheets integration
  - Service account creation
  - Spreadsheet configuration
  - Credentials setup

- **[SHEETS_IMPORT_QUICKSTART.md](SHEETS_IMPORT_QUICKSTART.md)** - Quick reference for importing agents
  - Expected spreadsheet format
  - Import commands
  - Troubleshooting

- **[ZAPIER_SETUP.md](ZAPIER_SETUP.md)** - Zapier webhook configuration
  - Creating webhook URLs
  - Configuring CINC forwarding
  - Testing webhooks

### Developer Documentation

- **[CLAUDE.md](CLAUDE.md)** - Guide for working with Claude Code
  - Development commands
  - Database operations
  - Testing endpoints
  - Git workflows
  - Common issues and solutions

- **[API_ENHANCEMENTS.md](API_ENHANCEMENTS.md)** - Latest API improvements (v1.1)
  - Input validation and sanitization
  - Pagination with total counts
  - Search and filter capabilities
  - Sorting options
  - Usage examples and error handling

## 🗂️ Documentation by Topic

### Authentication & Security
- User roles and permissions → [../README.md](../README.md#-user-management)
- JWT configuration → [CLAUDE.md](CLAUDE.md)
- Password requirements → [API_ENHANCEMENTS.md](API_ENHANCEMENTS.md#1-input-validation--sanitization-)

### Integration
- CINC API sync → [../README.md](../README.md#-cinc-api-integration)
- Zapier webhooks → [ZAPIER_SETUP.md](ZAPIER_SETUP.md)
- Google Sheets import → [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

### Database
- Schema overview → [../README.md](../README.md#-database-schema)
- Backup procedures → [../README.md](../README.md#-backup--maintenance)
- Direct database access → [CLAUDE.md](CLAUDE.md#database-operations)

### API Reference
- Endpoint documentation → [../README.md](../README.md#-api-endpoints)
- Enhanced API features → [API_ENHANCEMENTS.md](API_ENHANCEMENTS.md)
- Request/response examples → [API_ENHANCEMENTS.md](API_ENHANCEMENTS.md#api-usage-examples)

### Deployment
- Quick start → [../README.md](../README.md#-quick-start)
- Production deployment → [../README.md](../README.md#-production-deployment)
- Troubleshooting → [../README.md](../README.md#-troubleshooting)

## 🔄 Recent Updates

### January 2025 - API Enhancements (v1.1)
- ✅ Comprehensive input validation
- ✅ Pagination with metadata
- ✅ Search across multiple fields
- ✅ Advanced filtering (date range, timeline, price, sync status)
- ✅ Flexible sorting options
- ✅ Fixed Python 3.12+ compatibility

See [API_ENHANCEMENTS.md](API_ENHANCEMENTS.md) for complete details.

## 💡 Quick Links

### Common Tasks

**Import agents from Google Sheets:**
```bash
docker exec -it newhomes-api python import_agents.py
```
→ [SHEETS_IMPORT_QUICKSTART.md](SHEETS_IMPORT_QUICKSTART.md)

**Create admin user:**
```bash
docker exec -it newhomes-api python create_admin.py
```
→ [../README.md](../README.md#5-create-initial-admin-user)

**View API logs:**
```bash
docker-compose logs -f api
```
→ [CLAUDE.md](CLAUDE.md#development-commands)

**Backup database:**
```bash
docker exec newhomes-api sqlite3 /data/leads.db ".backup '/data/leads_backup.db'"
```
→ [../README.md](../README.md#backup-database)

**Test API endpoint:**
```bash
curl http://localhost:8000/ -H "Authorization: Bearer YOUR_TOKEN"
```
→ [CLAUDE.md](CLAUDE.md#testing-api-endpoints)

## 📞 Support

For issues or questions:
1. Check relevant documentation above
2. Review logs: `docker-compose logs`
3. Check troubleshooting guide: [../README.md](../README.md#-troubleshooting)
4. Contact system administrator

---

**Last Updated:** January 2025
**Version:** 1.1.0
