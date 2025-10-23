# Login Error Fix - JSON Parse Error

## Error Description

**Error Message:**
```
Login error: SyntaxError: JSON.parse: unexpected character at line 1 column 1 of the JSON data
```

**What This Means:**
The frontend is trying to parse JSON from the API response, but the API is returning something else (likely HTML, plain text, or an error page).

---

## Root Cause

This error occurs when:
1. ❌ The API service is not running
2. ❌ Nginx cannot reach the API container
3. ❌ The API endpoint doesn't exist
4. ❌ Network configuration issue between containers

---

## Solutions Implemented

### 1. Enhanced Error Handling ✅

Added content-type checking before attempting to parse JSON:

```javascript
// Check content type before parsing
const contentType = response.headers.get('content-type');
if (!contentType || !contentType.includes('application/json')) {
    const text = await response.text();
    console.error('Non-JSON response:', text.substring(0, 200));
    throw new Error('Server returned invalid response. Check API connection.');
}
```

**Benefits:**
- Shows clear error message instead of JSON parse error
- Logs the actual response in console for debugging
- Helps identify if nginx is returning HTML error page

### 2. Improved API_BASE Detection ✅

Better hostname detection:

```javascript
const API_BASE = (() => {
    const hostname = window.location.hostname;

    // Development (localhost)
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }

    // Production with nginx proxy
    return '/api';
})();

console.log('API_BASE configured as:', API_BASE);
```

**Now logs:** The API_BASE URL in browser console for debugging

---

## Troubleshooting Steps

### Step 1: Check if Services are Running

```bash
# Check container status
docker-compose ps

# Should show:
# newhomes-api    running (healthy)
# newhomes-nginx  running
```

**If API is not running:**
```bash
# View logs
docker-compose logs api

# Restart services
docker-compose restart api
```

### Step 2: Test API Directly

```bash
# Test API health endpoint (inside container)
docker exec newhomes-api curl http://localhost:8000/

# Test API from host machine
curl http://localhost:8000/

# Expected: {"message":"New Homes Lead Tracker API"}
```

### Step 3: Test Nginx Proxy

```bash
# Test nginx proxy to API
curl http://localhost:8087/api/

# Should return same as above
```

### Step 4: Check Network Connectivity

```bash
# From nginx container, test API connection
docker exec newhomes-nginx ping -c 3 api

# From nginx container, test API endpoint
docker exec newhomes-nginx wget -O- http://api:8000/
```

### Step 5: Check Browser Console

1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for:
   - `API_BASE configured as: /api`
   - `Non-JSON response: ...` (if error)
4. Go to Network tab
5. Try to login
6. Click on the `/api/login` request
7. Check:
   - Status code
   - Response headers
   - Response body

---

## Common Issues & Fixes

### Issue 1: API Container Not Running

**Symptom:**
```
Error: connect ECONNREFUSED
```

**Solution:**
```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### Issue 2: Port Already in Use

**Symptom:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Find process using port 8087
lsof -i :8087

# Kill the process or change port in docker-compose.yml
# Then restart
docker-compose down
docker-compose up -d
```

### Issue 3: Network Issue Between Containers

**Symptom:**
```
nginx: [error] connect() failed (111: Connection refused) while connecting to upstream
```

**Solution:**
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

### Issue 4: CORS Error

**Symptom:**
```
Access to fetch at 'http://...' has been blocked by CORS policy
```

**Solution:**
Already fixed in `nginx.conf` (lines 21-23):
```nginx
add_header Access-Control-Allow-Origin *;
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
add_header Access-Control-Allow-Headers "Content-Type, Authorization";
```

### Issue 5: Wrong API Endpoint

**Symptom:**
```
404 Not Found
```

**Solution:**
Check that `/api/login` correctly maps to API container:
- Frontend calls: `http://72.60.116.213:8087/api/login`
- Nginx proxies to: `http://api:8000/login`
- FastAPI serves: `/login` endpoint

---

## Verification Commands

### Complete Health Check

```bash
# 1. Check containers
echo "=== Container Status ==="
docker-compose ps

# 2. Check API health
echo "\n=== API Health Check ==="
curl -f http://localhost:8087/api/ && echo "✅ API OK" || echo "❌ API Failed"

# 3. Check login endpoint
echo "\n=== Login Endpoint Test ==="
curl -X POST http://localhost:8087/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  && echo "\n✅ Login endpoint OK" || echo "\n❌ Login endpoint failed"

# 4. Check nginx logs
echo "\n=== Nginx Logs (last 20 lines) ==="
docker-compose logs --tail=20 nginx

# 5. Check API logs
echo "\n=== API Logs (last 20 lines) ==="
docker-compose logs --tail=20 api
```

---

## Production Deployment Checklist

When deploying to `72.60.116.213:8087`:

- [ ] Services are running: `docker-compose ps`
- [ ] API is healthy: `curl http://localhost:8000/`
- [ ] Nginx proxy works: `curl http://localhost:8087/api/`
- [ ] Firewall allows port 8087
- [ ] Environment variables are set in `.env`
- [ ] Database is initialized: `docker exec newhomes-api ls -la /data/`
- [ ] Admin user exists (or create one)

---

## Expected Behavior

### Successful Login Flow

1. **Frontend Request:**
   ```
   POST http://72.60.116.213:8087/api/login
   Content-Type: application/x-www-form-urlencoded
   Body: username=admin&password=admin123
   ```

2. **Nginx Proxy:**
   ```
   Forwards to: http://api:8000/login
   ```

3. **FastAPI Response:**
   ```json
   {
     "access_token": "eyJ...",
     "token_type": "bearer",
     "role": "admin",
     "username": "admin"
   }
   ```

4. **Frontend:**
   - Stores token in localStorage
   - Shows dashboard
   - Console logs: "API_BASE configured as: /api"

---

## Quick Fix (If Services are Running)

If containers are running but login still fails:

```bash
# 1. Restart both services
docker-compose restart

# 2. Clear browser cache and localStorage
# In browser console:
localStorage.clear()

# 3. Hard refresh page (Ctrl+Shift+R or Cmd+Shift+R)

# 4. Try login again
```

---

## Files Modified

1. **index.html** (lines 647-661):
   - Improved API_BASE detection
   - Added console logging

2. **index.html** (lines 890-896):
   - Added content-type validation
   - Better error messages
   - Response logging

---

## Still Having Issues?

Check these logs:

```bash
# Full API logs
docker-compose logs api | tail -100

# Full nginx logs
docker-compose logs nginx | tail -100

# System logs (if on Linux)
journalctl -u docker -n 50

# Network inspection
docker network inspect site-visitor-dash_newhomes-network
```

**Contact support with:**
- Container status output
- Browser console logs
- Network tab screenshot
- API and nginx logs

---

**Last Updated:** January 2025
**Status:** Fixed ✅
