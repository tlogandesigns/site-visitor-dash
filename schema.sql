-- New Homes Lead Tracker Database Schema

CREATE TABLE IF NOT EXISTS communities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin', 'user')),
    agent_id INTEGER,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cinc_id TEXT NOT NULL,
    site TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, site)
);

CREATE TABLE IF NOT EXISTS visitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Buyer Info
    buyer_name TEXT NOT NULL,
    buyer_phone TEXT NOT NULL,
    buyer_email TEXT,
    purchase_timeline TEXT,
    price_range TEXT,
    location_looking TEXT,
    location_current TEXT,
    occupation TEXT,
    represented BOOLEAN DEFAULT 0,
    agent_name TEXT,
    
    -- Agent Info
    capturing_agent_id INTEGER NOT NULL,
    site TEXT NOT NULL,
    
    -- Meta
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cinc_synced BOOLEAN DEFAULT 0,
    cinc_sync_at TIMESTAMP,
    cinc_lead_id TEXT,
    
    FOREIGN KEY (capturing_agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS visitor_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    note TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (visitor_id) REFERENCES visitors(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_agent_id ON users(agent_id);
CREATE INDEX IF NOT EXISTS idx_visitors_phone ON visitors(buyer_phone);
CREATE INDEX IF NOT EXISTS idx_visitors_email ON visitors(buyer_email);
CREATE INDEX IF NOT EXISTS idx_visitors_site ON visitors(site);
CREATE INDEX IF NOT EXISTS idx_visitors_created ON visitors(created_at);
CREATE INDEX IF NOT EXISTS idx_visitor_notes_visitor ON visitor_notes(visitor_id);
CREATE INDEX IF NOT EXISTS idx_visitors_capturing_agent ON visitors(capturing_agent_id);

-- View for easy querying
CREATE VIEW IF NOT EXISTS visitor_details AS
SELECT 
    v.*,
    a.name as agent_name,
    a.cinc_id as agent_cinc_id,
    (SELECT COUNT(*) FROM visitor_notes WHERE visitor_id = v.id) as note_count,
    (SELECT note FROM visitor_notes WHERE visitor_id = v.id ORDER BY created_at DESC LIMIT 1) as latest_note
FROM visitors v
LEFT JOIN agents a ON v.capturing_agent_id = a.id;
