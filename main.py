"""
New Homes Lead Tracker API
FastAPI backend with CINC integration
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import sqlite3
import requests
import csv
import io
import os
from contextlib import contextmanager

app = FastAPI(title="New Homes Lead Tracker", version="1.0.0")

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "leads.db")
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "")  # Zapier webhook for lead sync

# Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Super Admin Configuration
SUPER_ADMIN_USERNAME = os.getenv("SUPER_ADMIN_USERNAME", "superadmin")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "ChangeMeOnFirstLogin123!")
SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "admin@example.com")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Database connection manager
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    agent_id: Optional[int] = None

class UserInDB(BaseModel):
    id: int
    username: str
    role: str
    agent_id: Optional[int] = None
    active: bool

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    role: str  # 'super_admin', 'admin' or 'user'
    agent_id: Optional[int] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    agent_id: Optional[int] = None
    active: Optional[bool] = None

class VisitorCreate(BaseModel):
    buyer_name: str
    buyer_phone: str
    buyer_email: Optional[EmailStr] = None
    purchase_timeline: Optional[str] = None
    price_range: Optional[str] = None
    location_looking: Optional[str] = None
    location_current: Optional[str] = None
    occupation: Optional[str] = None
    represented: bool = False
    agent_name: Optional[str] = None
    capturing_agent_id: int
    site: str
    notes: Optional[str] = None

class NoteCreate(BaseModel):
    visitor_id: int
    agent_id: int
    note: str

class AgentCreate(BaseModel):
    name: str
    cinc_id: str
    site: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

# Authentication Helper Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user and return user data"""
    with get_db() as conn:
        cursor = conn.cursor()
        user = cursor.execute(
            "SELECT id, username, password_hash, role, agent_id, active FROM users WHERE username = ? AND active = 1",
            (username,)
        ).fetchone()

        if not user:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user["id"])
        )

        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "agent_id": user["agent_id"],
            "active": user["active"]
        }

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    with get_db() as conn:
        cursor = conn.cursor()
        user = cursor.execute(
            "SELECT id, username, role, agent_id, active FROM users WHERE username = ? AND active = 1",
            (username,)
        ).fetchone()

        if user is None:
            raise credentials_exception

        return UserInDB(
            id=user["id"],
            username=user["username"],
            role=user["role"],
            agent_id=user["agent_id"],
            active=user["active"]
        )

async def get_current_admin_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Verify current user is admin or super_admin"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_super_admin_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Verify current user is super_admin"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin permissions required"
        )
    return current_user

# Helper Functions
def sync_to_zapier(visitor_data: dict, agent_data: dict) -> dict:
    """
    Send lead data to Zapier webhook
    The webhook will handle forwarding to CINC or other systems
    """
    if not ZAPIER_WEBHOOK_URL:
        return {"success": False, "error": "Zapier webhook URL not configured"}

    try:
        # Split name into first and last
        name_parts = visitor_data["buyer_name"].split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Prepare payload for Zapier
        payload = {
            # Buyer Information
            "firstName": first_name,
            "lastName": last_name,
            "fullName": visitor_data["buyer_name"],
            "email": visitor_data.get("buyer_email", ""),
            "phone": visitor_data["buyer_phone"],

            # Agent Information
            "agentName": agent_data.get("name", ""),
            "agentEmail": agent_data.get("email", ""),
            "agentCincId": agent_data.get("cinc_id", ""),
            "site": visitor_data["site"],

            # Lead Details
            "purchaseTimeline": visitor_data.get("purchase_timeline", ""),
            "priceRange": visitor_data.get("price_range", ""),
            "locationLooking": visitor_data.get("location_looking", ""),
            "locationCurrent": visitor_data.get("location_current", ""),
            "occupation": visitor_data.get("occupation", ""),
            "represented": "Yes" if visitor_data.get("represented") else "No",
            "representingAgent": visitor_data.get("agent_name", ""),

            # Metadata
            "source": "New Homes Lead Tracker",
            "notes": visitor_data.get("notes", ""),
            "timestamp": datetime.now().isoformat(),
            "visitDate": visitor_data.get("created_at", datetime.now().isoformat())
        }

        # Send to Zapier webhook
        response = requests.post(
            ZAPIER_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        response.raise_for_status()

        # Zapier webhooks typically return 200 with success
        return {"success": True, "zapier_response": response.status_code}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

# API Endpoints

@app.get("/")
def read_root():
    return {"message": "New Homes Lead Tracker API", "version": "1.0.0"}

# Authentication Endpoints
@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        username=user["username"],
        agent_id=user["agent_id"]
    )

@app.get("/me")
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@app.post("/users")
async def create_user(user: UserCreate, current_user: UserInDB = Depends(get_current_admin_user)):
    """Create new user (admin and super_admin only)"""
    # Only super_admin can create super_admin users
    if user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can create super admin users")

    if user.role not in ["super_admin", "admin", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if username exists
        existing = cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Verify agent_id exists if provided
        if user.agent_id:
            agent = cursor.execute("SELECT id FROM agents WHERE id = ?", (user.agent_id,)).fetchone()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")

        # Create user
        password_hash = get_password_hash(user.password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, role, agent_id)
            VALUES (?, ?, ?, ?, ?)
        """, (user.username, password_hash, user.email, user.role, user.agent_id))

        return {"id": cursor.lastrowid, "username": user.username, "role": user.role}

@app.get("/users")
async def list_users(current_user: UserInDB = Depends(get_current_admin_user)):
    """List all users (admin and super_admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()
        users = cursor.execute("""
            SELECT u.id, u.username, u.email, u.role, u.agent_id, u.active, u.created_at, u.last_login, a.name as agent_name
            FROM users u
            LEFT JOIN agents a ON u.agent_id = a.id
            ORDER BY u.created_at DESC
        """).fetchall()

        return {"users": [dict(u) for u in users]}

@app.put("/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, current_user: UserInDB = Depends(get_current_admin_user)):
    """Update user (admin and super_admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if user exists
        existing_user = cursor.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Only super_admin can modify super_admin users
        if existing_user["role"] == "super_admin" and current_user.role != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can modify super admin users")

        # Only super_admin can change role to super_admin
        if user_update.role == "super_admin" and current_user.role != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can assign super admin role")

        # Verify agent_id exists if provided
        if user_update.agent_id is not None:
            agent = cursor.execute("SELECT id FROM agents WHERE id = ?", (user_update.agent_id,)).fetchone()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")

        # Build update query dynamically
        updates = []
        params = []

        if user_update.email is not None:
            updates.append("email = ?")
            params.append(user_update.email)

        if user_update.password is not None:
            updates.append("password_hash = ?")
            params.append(get_password_hash(user_update.password))

        if user_update.role is not None:
            if user_update.role not in ["super_admin", "admin", "user"]:
                raise HTTPException(status_code=400, detail="Invalid role")
            updates.append("role = ?")
            params.append(user_update.role)

        if user_update.agent_id is not None:
            updates.append("agent_id = ?")
            params.append(user_update.agent_id)

        if user_update.active is not None:
            updates.append("active = ?")
            params.append(1 if user_update.active else 0)

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)

        return {"message": "User updated successfully"}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: UserInDB = Depends(get_current_admin_user)):
    """Delete/deactivate user (admin and super_admin only)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if user exists
        existing_user = cursor.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Cannot delete yourself
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")

        # Only super_admin can delete super_admin users
        if existing_user["role"] == "super_admin" and current_user.role != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can delete super admin users")

        # Deactivate instead of delete to preserve data integrity
        cursor.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))

        return {"message": "User deactivated successfully"}

@app.post("/visitors")
def create_visitor(visitor: VisitorCreate, current_user: UserInDB = Depends(get_current_user)):
    """Create new visitor and sync via Zapier webhook"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get agent information
        agent = cursor.execute(
            "SELECT id, name, cinc_id, email FROM agents WHERE id = ?",
            (visitor.capturing_agent_id,)
        ).fetchone()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Insert visitor
        cursor.execute("""
            INSERT INTO visitors (
                buyer_name, buyer_phone, buyer_email, purchase_timeline,
                price_range, location_looking, location_current, occupation,
                represented, agent_name, capturing_agent_id, site
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            visitor.buyer_name, visitor.buyer_phone, visitor.buyer_email,
            visitor.purchase_timeline, visitor.price_range, visitor.location_looking,
            visitor.location_current, visitor.occupation, visitor.represented,
            visitor.agent_name, visitor.capturing_agent_id, visitor.site
        ))

        visitor_id = cursor.lastrowid

        # Add initial note if provided
        if visitor.notes:
            cursor.execute("""
                INSERT INTO visitor_notes (visitor_id, agent_id, note)
                VALUES (?, ?, ?)
            """, (visitor_id, visitor.capturing_agent_id, visitor.notes))

        # Sync to Zapier webhook
        visitor_dict = visitor.dict()
        visitor_dict["created_at"] = datetime.now().isoformat()

        agent_dict = {
            "name": agent["name"],
            "cinc_id": agent["cinc_id"],
            "email": agent["email"]
        }

        zapier_result = sync_to_zapier(visitor_dict, agent_dict)

        if zapier_result["success"]:
            cursor.execute("""
                UPDATE visitors
                SET cinc_synced = 1, cinc_sync_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), visitor_id))

        return {
            "id": visitor_id,
            "synced": zapier_result["success"],
            "sync_error": zapier_result.get("error")
        }

@app.get("/visitors")
def list_visitors(site: Optional[str] = None, limit: int = 100, offset: int = 0, current_user: UserInDB = Depends(get_current_user)):
    """List all visitors with optional site filter. Users only see their own leads, admins and super_admins see all."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users can only see visitors they created, admins and super_admins see all
        if current_user.role == "user":
            if site:
                query = "SELECT * FROM visitor_details WHERE site = ? AND capturing_agent_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params = (site, current_user.agent_id, limit, offset)
            else:
                query = "SELECT * FROM visitor_details WHERE capturing_agent_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params = (current_user.agent_id, limit, offset)
        else:  # admin or super_admin
            if site:
                query = "SELECT * FROM visitor_details WHERE site = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params = (site, limit, offset)
            else:
                query = "SELECT * FROM visitor_details ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params = (limit, offset)

        visitors = cursor.execute(query, params).fetchall()

        return {
            "visitors": [dict(v) for v in visitors],
            "count": len(visitors)
        }

@app.get("/visitors/{visitor_id}")
def get_visitor(visitor_id: int, current_user: UserInDB = Depends(get_current_user)):
    """Get single visitor with all notes. Users can only see their own leads."""
    with get_db() as conn:
        cursor = conn.cursor()

        visitor = cursor.execute(
            "SELECT * FROM visitor_details WHERE id = ?",
            (visitor_id,)
        ).fetchone()

        if not visitor:
            raise HTTPException(status_code=404, detail="Visitor not found")

        # Users can only view visitors they created
        if current_user.role == "user" and visitor["capturing_agent_id"] != current_user.agent_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this visitor")

        notes = cursor.execute("""
            SELECT n.*, a.name as agent_name
            FROM visitor_notes n
            JOIN agents a ON n.agent_id = a.id
            WHERE n.visitor_id = ?
            ORDER BY n.created_at DESC
        """, (visitor_id,)).fetchall()

        return {
            "visitor": dict(visitor),
            "notes": [dict(n) for n in notes]
        }

@app.post("/visitors/{visitor_id}/notes")
def add_note(visitor_id: int, note: NoteCreate, current_user: UserInDB = Depends(get_current_user)):
    """Add timestamped note to visitor"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify visitor exists
        visitor = cursor.execute("SELECT id FROM visitors WHERE id = ?", (visitor_id,)).fetchone()
        if not visitor:
            raise HTTPException(status_code=404, detail="Visitor not found")
        
        cursor.execute("""
            INSERT INTO visitor_notes (visitor_id, agent_id, note)
            VALUES (?, ?, ?)
        """, (visitor_id, note.agent_id, note.note))
        
        cursor.execute("UPDATE visitors SET updated_at = ? WHERE id = ?", 
                      (datetime.now().isoformat(), visitor_id))
        
        return {"id": cursor.lastrowid, "created_at": datetime.now().isoformat()}

@app.get("/visitors/export/csv")
def export_visitors_csv(site: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)):
    """Export visitors to CSV. Users only export their own leads."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users can only export their own visitors
        if current_user.role == "user":
            if site:
                visitors = cursor.execute(
                    "SELECT * FROM visitor_details WHERE site = ? AND capturing_agent_id = ? ORDER BY created_at DESC",
                    (site, current_user.agent_id)
                ).fetchall()
            else:
                visitors = cursor.execute(
                    "SELECT * FROM visitor_details WHERE capturing_agent_id = ? ORDER BY created_at DESC",
                    (current_user.agent_id,)
                ).fetchall()
        else:  # admin
            if site:
                visitors = cursor.execute(
                    "SELECT * FROM visitor_details WHERE site = ? ORDER BY created_at DESC",
                    (site,)
                ).fetchall()
            else:
                visitors = cursor.execute(
                    "SELECT * FROM visitor_details ORDER BY created_at DESC"
                ).fetchall()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[desc[0] for desc in cursor.description])
        writer.writeheader()
        
        for visitor in visitors:
            writer.writerow(dict(visitor))
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leads_export.csv"}
        )

# Agent Management
@app.post("/agents")
def create_agent(agent: AgentCreate):
    """Create new agent"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO agents (name, cinc_id, site, email, phone)
                VALUES (?, ?, ?, ?, ?)
            """, (agent.name, agent.cinc_id, agent.site, agent.email, agent.phone))
            
            return {"id": cursor.lastrowid}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Agent already exists for this site")

@app.get("/agents")
def list_agents(site: Optional[str] = None):
    """List all agents"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if site:
            agents = cursor.execute(
                "SELECT * FROM agents WHERE site = ? AND active = 1 ORDER BY name",
                (site,)
            ).fetchall()
        else:
            agents = cursor.execute(
                "SELECT * FROM agents WHERE active = 1 ORDER BY name"
            ).fetchall()
        
        return {"agents": [dict(a) for a in agents]}

@app.get("/sites")
def list_sites():
    """Get unique list of sites/communities"""
    with get_db() as conn:
        cursor = conn.cursor()
        sites = cursor.execute("SELECT DISTINCT site FROM agents ORDER BY site").fetchall()
        return {"sites": [s["site"] for s in sites]}

@app.get("/stats")
def get_stats(site: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)):
    """Get dashboard statistics. Users only see their own stats, admins and super_admins see all."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users only see their own stats
        if current_user.role == "user":
            if site:
                total_visitors = cursor.execute(
                    "SELECT COUNT(*) as count FROM visitors WHERE site = ? AND capturing_agent_id = ?",
                    (site, current_user.agent_id)
                ).fetchone()["count"]

                today_visitors = cursor.execute("""
                    SELECT COUNT(*) as count FROM visitors
                    WHERE site = ? AND capturing_agent_id = ? AND DATE(created_at) = DATE('now')
                """, (site, current_user.agent_id)).fetchone()["count"]

                cinc_synced = cursor.execute(
                    "SELECT COUNT(*) as count FROM visitors WHERE cinc_synced = 1 AND capturing_agent_id = ?",
                    (current_user.agent_id,)
                ).fetchone()["count"]
            else:
                total_visitors = cursor.execute(
                    "SELECT COUNT(*) as count FROM visitors WHERE capturing_agent_id = ?",
                    (current_user.agent_id,)
                ).fetchone()["count"]

                today_visitors = cursor.execute("""
                    SELECT COUNT(*) as count FROM visitors
                    WHERE capturing_agent_id = ? AND DATE(created_at) = DATE('now')
                """, (current_user.agent_id,)).fetchone()["count"]

                cinc_synced = cursor.execute(
                    "SELECT COUNT(*) as count FROM visitors WHERE cinc_synced = 1 AND capturing_agent_id = ?",
                    (current_user.agent_id,)
                ).fetchone()["count"]
        else:  # admin sees all
            if site:
                total_visitors = cursor.execute(
                    "SELECT COUNT(*) as count FROM visitors WHERE site = ?", (site,)
                ).fetchone()["count"]

                today_visitors = cursor.execute("""
                    SELECT COUNT(*) as count FROM visitors
                    WHERE site = ? AND DATE(created_at) = DATE('now')
                """, (site,)).fetchone()["count"]
            else:
                total_visitors = cursor.execute(
                    "SELECT COUNT(*) as count FROM visitors"
                ).fetchone()["count"]

                today_visitors = cursor.execute("""
                    SELECT COUNT(*) as count FROM visitors
                    WHERE DATE(created_at) = DATE('now')
                """).fetchone()["count"]

            cinc_synced = cursor.execute(
                "SELECT COUNT(*) as count FROM visitors WHERE cinc_synced = 1"
            ).fetchone()["count"]

        return {
            "total_visitors": total_visitors,
            "today_visitors": today_visitors,
            "cinc_synced": cinc_synced
        }

def initialize_super_admin():
    """Initialize or update super admin user on startup"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Check if super admin exists
            existing = cursor.execute(
                "SELECT id FROM users WHERE username = ?",
                (SUPER_ADMIN_USERNAME,)
            ).fetchone()

            password_hash = get_password_hash(SUPER_ADMIN_PASSWORD)

            if existing:
                # Update existing super admin
                cursor.execute("""
                    UPDATE users
                    SET password_hash = ?, email = ?, role = 'super_admin', active = 1
                    WHERE username = ?
                """, (password_hash, SUPER_ADMIN_EMAIL, SUPER_ADMIN_USERNAME))
                print(f"✅ Super admin '{SUPER_ADMIN_USERNAME}' updated")
            else:
                # Create new super admin
                cursor.execute("""
                    INSERT INTO users (username, password_hash, email, role, agent_id, active)
                    VALUES (?, ?, ?, 'super_admin', NULL, 1)
                """, (SUPER_ADMIN_USERNAME, password_hash, SUPER_ADMIN_EMAIL))
                print(f"✅ Super admin '{SUPER_ADMIN_USERNAME}' created")

    except Exception as e:
        print(f"❌ Error initializing super admin: {e}")

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    # Initialize database
    with get_db() as conn:
        with open("schema.sql", "r") as f:
            conn.executescript(f.read())

    # Initialize super admin
    initialize_super_admin()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
