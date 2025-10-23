# Three Major Features Implementation Guide

## Feature 1: Dashboard Charts/Graphs ✅ (Backend Complete)

### Backend: COMPLETE
- Added `/analytics` endpoint in main.py (lines 1027-1115)
- Returns: leads_by_day, leads_by_timeline, leads_by_price, leads_by_site, leads_by_agent, sync_stats

### Frontend: TODO

#### 1. Add Analytics Tab Navigation
Add after the "Users" tab in navbar:
```html
<li class="nav-item">
    <a class="nav-link" href="#" onclick="showSection('analytics'); return false;">Analytics</a>
</li>
```

#### 2. Add Analytics Section
Add before the Users section:
```html
<div id="analyticsSection" class="section" style="display: none;">
    <div class="container-fluid">
        <h2 class="mb-4">Analytics Dashboard</h2>

        <!-- Row 1: Time-based Charts -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Leads Over Time (Last 30 Days)</h5>
                        <canvas id="leadsByDayChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">CINC Sync Status</h5>
                        <canvas id="syncStatsChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Row 2: Distribution Charts -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Leads by Purchase Timeline</h5>
                        <canvas id="leadsBy TimelineChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Leads by Price Range</h5>
                        <canvas id="leadsByPriceChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Row 3: Site & Agent Performance -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Leads by Site/Community</h5>
                        <canvas id="leadsBySiteChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6" id="agentChartContainer" style="display: none;">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Leads by Agent</h5>
                        <canvas id="leadsByAgentChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### 3. Add JavaScript Functions
```javascript
// Chart instances
let charts = {};

async function loadAnalytics() {
    try {
        const site = document.getElementById('siteFilter')?.value;
        const url = site ? `${API_BASE}/analytics?site=${encodeURIComponent(site)}` : `${API_BASE}/analytics`;

        const response = await fetch(url, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            handleLogout();
            return;
        }

        const data = await response.json();

        // Destroy existing charts
        Object.values(charts).forEach(chart => chart?.destroy());
        charts = {};

        // Show/hide agent chart based on role
        if (currentUser.role === 'admin' || currentUser.role === 'super_admin') {
            document.getElementById('agentChartContainer').style.display = 'block';
        }

        // Leads by Day (Line Chart)
        const leadsByDayData = data.leads_by_day.reverse(); // Show oldest to newest
        charts.leadsByDay = new Chart(document.getElementById('leadsByDayChart'), {
            type: 'line',
            data: {
                labels: leadsByDayData.map(d => d.date),
                datasets: [{
                    label: 'Leads',
                    data: leadsByDayData.map(d => d.count),
                    borderColor: '#670038',
                    backgroundColor: 'rgba(103, 0, 56, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // CINC Sync Status (Doughnut Chart)
        charts.syncStats = new Chart(document.getElementById('syncStatsChart'), {
            type: 'doughnut',
            data: {
                labels: ['Synced', 'Pending'],
                datasets: [{
                    data: [data.sync_stats.synced, data.sync_stats.not_synced],
                    backgroundColor: ['#28a745', '#ffc107']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });

        // Leads by Timeline (Bar Chart)
        charts.leadsByTimeline = new Chart(document.getElementById('leadsByTimelineChart'), {
            type: 'bar',
            data: {
                labels: data.leads_by_timeline.map(d => d.timeline),
                datasets: [{
                    label: 'Leads',
                    data: data.leads_by_timeline.map(d => d.count),
                    backgroundColor: '#670038'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // Leads by Price (Horizontal Bar Chart)
        charts.leadsByPrice = new Chart(document.getElementById('leadsByPriceChart'), {
            type: 'bar',
            data: {
                labels: data.leads_by_price.map(d => d.price_range),
                datasets: [{
                    label: 'Leads',
                    data: data.leads_by_price.map(d => d.count),
                    backgroundColor: '#8a0049'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });

        // Leads by Site (Pie Chart)
        const siteColors = ['#670038', '#8a0049', '#a50062', '#c0007b', '#db0094'];
        charts.leadsBySite = new Chart(document.getElementById('leadsBySiteChart'), {
            type: 'pie',
            data: {
                labels: data.leads_by_site.map(d => d.site),
                datasets: [{
                    data: data.leads_by_site.map(d => d.count),
                    backgroundColor: siteColors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });

        // Leads by Agent (Bar Chart - Admins only)
        if (data.leads_by_agent.length > 0) {
            charts.leadsByAgent = new Chart(document.getElementById('leadsByAgentChart'), {
                type: 'bar',
                data: {
                    labels: data.leads_by_agent.map(d => d.agent_name),
                    datasets: [{
                        label: 'Leads',
                        data: data.leads_by_agent.map(d => d.count),
                        backgroundColor: '#670038'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

    } catch (error) {
        console.error('Error loading analytics:', error);
        showToast('Failed to load analytics', 'error');
    }
}

// Update showSection function to handle analytics
function showSection(section) {
    document.getElementById('dashboardSection').style.display = 'none';
    document.getElementById('usersSection').style.display = 'none';
    document.getElementById('analyticsSection').style.display = 'none';

    if (section === 'dashboard') {
        document.getElementById('dashboardSection').style.display = 'block';
        loadVisitors();
        loadStats();
    } else if (section === 'users') {
        document.getElementById('usersSection').style.display = 'block';
        loadUsers();
    } else if (section === 'analytics') {
        document.getElementById('analyticsSection').style.display = 'block';
        loadAnalytics();
    }
}
```

---

## Feature 2: Bulk Operations

### Backend: TODO
Add these endpoints to main.py:

```python
@app.post("/visitors/bulk-delete")
def bulk_delete_visitors(visitor_ids: List[int], current_user: UserInDB = Depends(get_current_user)):
    """Bulk delete visitors (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only administrators can delete visitors")

    with get_db() as conn:
        cursor = conn.cursor()
        deleted_count = 0

        for visitor_id in visitor_ids:
            # Delete notes first
            cursor.execute("DELETE FROM visitor_notes WHERE visitor_id = ?", (visitor_id,))
            # Delete visitor
            result = cursor.execute("DELETE FROM visitors WHERE id = ?", (visitor_id,))
            if result.rowcount > 0:
                deleted_count += 1

        return {"message": f"Successfully deleted {deleted_count} visitors", "count": deleted_count}

@app.post("/visitors/bulk-assign")
def bulk_assign_agent(visitor_ids: List[int], new_agent_id: int, current_user: UserInDB = Depends(get_current_user)):
    """Bulk reassign visitors to different agent (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only administrators can reassign visitors")

    # Verify agent exists
    with get_db() as conn:
        cursor = conn.cursor()
        agent = cursor.execute("SELECT id, name FROM agents WHERE id = ?", (new_agent_id,)).fetchone()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        updated_count = 0
        for visitor_id in visitor_ids:
            result = cursor.execute(
                "UPDATE visitors SET capturing_agent_id = ?, updated_at = ? WHERE id = ?",
                (new_agent_id, datetime.now().isoformat(), visitor_id)
            )
            if result.rowcount > 0:
                updated_count += 1

        return {
            "message": f"Successfully reassigned {updated_count} visitors to {agent['name']}",
            "count": updated_count
        }
```

### Frontend: TODO

#### 1. Add checkboxes to visitor table
```html
<!-- In table header -->
<th><input type="checkbox" id="selectAllVisitors" onchange="toggleSelectAll(this)"></th>

<!-- In each visitor row -->
<td><input type="checkbox" class="visitor-checkbox" value="${visitor.id}"></td>
```

#### 2. Add bulk action buttons
```html
<!-- Add after the "Refresh" button in dashboard -->
<button class="btn btn-outline-danger" id="bulkDeleteBtn" style="display:none;" onclick="bulkDeleteVisitors()">
    <i class="bi bi-trash"></i> Delete Selected
</button>
<button class="btn btn-outline-primary" id="bulkAssignBtn" style="display:none;" onclick="showBulkAssignModal()">
    <i class="bi bi-person-plus"></i> Reassign Selected
</button>
```

#### 3. Add JavaScript functions
```javascript
function toggleSelectAll(checkbox) {
    document.querySelectorAll('.visitor-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateBulkButtons();
}

function updateBulkButtons() {
    const checked = document.querySelectorAll('.visitor-checkbox:checked').length;
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const bulkAssignBtn = document.getElementById('bulkAssignBtn');

    if (checked > 0 && (currentUser.role === 'admin' || currentUser.role === 'super_admin')) {
        bulkDeleteBtn.style.display = 'inline-block';
        bulkAssignBtn.style.display = 'inline-block';
    } else {
        bulkDeleteBtn.style.display = 'none';
        bulkAssignBtn.style.display = 'none';
    }
}

async function bulkDeleteVisitors() {
    const selectedIds = Array.from(document.querySelectorAll('.visitor-checkbox:checked')).map(cb => parseInt(cb.value));

    if (selectedIds.length === 0) {
        showToast('No visitors selected', 'warning');
        return;
    }

    showConfirm(
        `Are you sure you want to delete ${selectedIds.length} selected visitor(s)? This action cannot be undone.`,
        'Confirm Bulk Delete',
        async () => {
            try {
                const response = await fetch(`${API_BASE}/visitors/bulk-delete`, {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify(selectedIds)
                });

                if (response.status === 401) {
                    handleLogout();
                    return;
                }

                if (!response.ok) {
                    throw await response.json();
                }

                const data = await response.json();
                showToast(data.message, 'success');
                loadVisitors();
                loadStats();
            } catch (error) {
                await handleApiError(error, 'Failed to delete visitors');
            }
        },
        'Delete Selected',
        'btn-danger'
    );
}

async function bulkAssignAgent(newAgentId) {
    const selectedIds = Array.from(document.querySelectorAll('.visitor-checkbox:checked')).map(cb => parseInt(cb.value));

    try {
        const response = await fetch(`${API_BASE}/visitors/bulk-assign`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({visitor_ids: selectedIds, new_agent_id: newAgentId})
        });

        if (response.status === 401) {
            handleLogout();
            return;
        }

        if (!response.ok) {
            throw await response.json();
        }

        const data = await response.json();
        showToast(data.message, 'success');
        loadVisitors();
    } catch (error) {
        await handleApiError(error, 'Failed to reassign visitors');
    }
}
```

---

## Feature 3: Activity Log/Audit Trail

### Backend: TODO

#### 1. Add audit_log table to schema.sql
```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'create', 'update', 'delete', 'login', 'logout'
    entity_type TEXT NOT NULL,  -- 'visitor', 'user', 'note', 'agent'
    entity_id INTEGER,
    changes TEXT,  -- JSON string of what changed
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);
```

#### 2. Add audit logging helper in main.py
```python
import json

def log_audit(
    conn: sqlite3.Connection,
    user_id: int,
    username: str,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    changes: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    """Log an audit trail entry"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log (user_id, username, action, entity_type, entity_id, changes, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username,
        action,
        entity_type,
        entity_id,
        json.dumps(changes) if changes else None,
        ip_address
    ))
```

#### 3. Add audit logging to key endpoints
```python
# In create_visitor endpoint:
log_audit(conn, current_user.id, current_user.username, "create", "visitor", visitor_id, {
    "buyer_name": visitor.buyer_name,
    "site": visitor.site
})

# In delete_visitor endpoint:
log_audit(conn, current_user.id, current_user.username, "delete", "visitor", visitor_id, {
    "visitor_name": visitor_name
})

# In add_note endpoint:
log_audit(conn, current_user.id, current_user.username, "create", "note", note_id, {
    "visitor_id": visitor_id
})

# In login endpoint:
log_audit(conn, user["id"], user["username"], "login", "user", user["id"])
```

#### 4. Add audit log endpoint
```python
@app.get("/audit-log")
def get_audit_log(
    page: int = 1,
    page_size: int = 50,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Get audit log (admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()

        where_conditions = []
        params = []

        if entity_type:
            where_conditions.append("entity_type = ?")
            params.append(entity_type)

        if action:
            where_conditions.append("action = ?")
            params.append(action)

        if user_id:
            where_conditions.append("user_id = ?")
            params.append(user_id)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Get total count
        total = cursor.execute(f"""
            SELECT COUNT(*) as count FROM audit_log {where_clause}
        """, params).fetchone()["count"]

        # Get paginated results
        offset = (page - 1) * page_size
        logs = cursor.execute(f"""
            SELECT * FROM audit_log
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset]).fetchall()

        return {
            "logs": [dict(log) for log in logs],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
```

### Frontend: TODO

#### 1. Add Audit Log tab (admin only)
```html
<li class="nav-item" id="auditLogTab" style="display:none;">
    <a class="nav-link" href="#" onclick="showSection('auditLog'); return false;">Audit Log</a>
</li>
```

#### 2. Add Audit Log section
```html
<div id="auditLogSection" class="section" style="display: none;">
    <div class="container-fluid">
        <h2 class="mb-4">Audit Log</h2>

        <!-- Filters -->
        <div class="row mb-3">
            <div class="col-md-3">
                <select class="form-select" id="auditEntityFilter" onchange="loadAuditLog()">
                    <option value="">All Entities</option>
                    <option value="visitor">Visitor</option>
                    <option value="user">User</option>
                    <option value="note">Note</option>
                    <option value="agent">Agent</option>
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select" id="auditActionFilter" onchange="loadAuditLog()">
                    <option value="">All Actions</option>
                    <option value="create">Create</option>
                    <option value="update">Update</option>
                    <option value="delete">Delete</option>
                    <option value="login">Login</option>
                    <option value="logout">Logout</option>
                </select>
            </div>
        </div>

        <!-- Audit Table -->
        <div class="card">
            <div class="card-body">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>User</th>
                            <th>Action</th>
                            <th>Entity Type</th>
                            <th>Entity ID</th>
                            <th>Changes</th>
                            <th>IP Address</th>
                        </tr>
                    </thead>
                    <tbody id="auditLogTableBody">
                        <!-- Populated by JavaScript -->
                    </tbody>
                </table>

                <!-- Pagination -->
                <nav>
                    <ul class="pagination" id="auditLogPagination">
                        <!-- Populated by JavaScript -->
                    </ul>
                </nav>
            </div>
        </div>
    </div>
</div>
```

#### 3. Add JavaScript functions
```javascript
async function loadAuditLog(page = 1) {
    try {
        const entityType = document.getElementById('auditEntityFilter').value;
        const action = document.getElementById('auditActionFilter').value;

        let url = `${API_BASE}/audit-log?page=${page}&page_size=50`;
        if (entityType) url += `&entity_type=${entityType}`;
        if (action) url += `&action=${action}`;

        const response = await fetch(url, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            handleLogout();
            return;
        }

        const data = await response.json();
        const tbody = document.getElementById('auditLogTableBody');
        tbody.innerHTML = '';

        data.logs.forEach(log => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${new Date(log.created_at).toLocaleString()}</td>
                <td>${log.username}</td>
                <td><span class="badge bg-${getActionColor(log.action)}">${log.action}</span></td>
                <td>${log.entity_type}</td>
                <td>${log.entity_id || '-'}</td>
                <td><small>${log.changes || '-'}</small></td>
                <td>${log.ip_address || '-'}</td>
            `;
        });

        // Render pagination
        renderAuditLogPagination(data.pagination);

    } catch (error) {
        console.error('Error loading audit log:', error);
        showToast('Failed to load audit log', 'error');
    }
}

function getActionColor(action) {
    const colors = {
        'create': 'success',
        'update': 'primary',
        'delete': 'danger',
        'login': 'info',
        'logout': 'secondary'
    };
    return colors[action] || 'secondary';
}

function renderAuditLogPagination(pagination) {
    const nav = document.getElementById('auditLogPagination');
    nav.innerHTML = '';

    for (let i = 1; i <= pagination.total_pages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === pagination.page ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="loadAuditLog(${i}); return false;">${i}</a>`;
        nav.appendChild(li);
    }
}
```

---

## Implementation Checklist

### Feature 1: Analytics Dashboard
- [x] Backend API endpoint (`/analytics`) - DONE
- [ ] Frontend: Add Chart.js CDN - DONE
- [ ] Frontend: Add Analytics tab
- [ ] Frontend: Add Analytics section HTML
- [ ] Frontend: Add loadAnalytics() function
- [ ] Frontend: Update showSection() function

### Feature 2: Bulk Operations
- [ ] Backend: Add `/visitors/bulk-delete` endpoint
- [ ] Backend: Add `/visitors/bulk-assign` endpoint
- [ ] Frontend: Add checkboxes to visitor table
- [ ] Frontend: Add bulk action buttons
- [ ] Frontend: Add bulk operation functions
- [ ] Frontend: Add bulk assign modal

### Feature 3: Audit Trail
- [ ] Database: Add audit_log table to schema.sql
- [ ] Backend: Add log_audit() helper function
- [ ] Backend: Add audit logging to all CRUD operations
- [ ] Backend: Add `/audit-log` endpoint
- [ ] Frontend: Add Audit Log tab (admin only)
- [ ] Frontend: Add Audit Log section HTML
- [ ] Frontend: Add loadAuditLog() function

---

## Testing Notes

### Analytics
- Test with different user roles (admin sees all, user sees own)
- Test site filtering
- Verify chart responsiveness
- Check edge cases (no data, single data point)

### Bulk Operations
- Test with 1, multiple, and all visitors selected
- Test permission checks (regular users shouldn't see buttons)
- Test reassignment to different agents
- Verify cascade deletion of notes

### Audit Trail
- Verify all actions are logged
- Test filtering by entity type and action
- Test pagination
- Check performance with large logs (consider adding date range filter)

---

**Current Status:**
- Feature 1 Backend: ✅ COMPLETE
- Feature 1 Frontend: ⚠️ PARTIAL (Chart.js CDN added)
- Feature 2: ❌ NOT STARTED
- Feature 3: ❌ NOT STARTED
