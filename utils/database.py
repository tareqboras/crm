import sqlite3
import os
from datetime import datetime, timedelta
import hashlib

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crm.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'seller',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        org_number TEXT,
        contact_person TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        city TEXT,
        postal_code TEXT,
        lead_source TEXT,
        assigned_to INTEGER REFERENCES users(id),
        status TEXT DEFAULT 'Ny',
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
        service_type TEXT,
        provider TEXT,
        current_price REAL,
        contract_end TEXT,
        binding_months INTEGER,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
        created_by INTEGER REFERENCES users(id),
        status TEXT DEFAULT 'Utkast',
        total_current REAL DEFAULT 0,
        total_offered REAL DEFAULT 0,
        monthly_saving REAL DEFAULT 0,
        yearly_saving REAL DEFAULT 0,
        valid_until TEXT,
        pdf_path TEXT,
        sent_at TEXT,
        reminder_7_sent INTEGER DEFAULT 0,
        reminder_14_sent INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS quote_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_id INTEGER REFERENCES quotes(id) ON DELETE CASCADE,
        service_type TEXT,
        provider_current TEXT,
        price_current REAL,
        provider_offered TEXT,
        price_offered REAL,
        binding_months INTEGER,
        saving REAL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id),
        activity_type TEXT,
        description TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS pipeline_stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sort_order INTEGER,
        color TEXT
    );

    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_id INTEGER REFERENCES quotes(id),
        customer_id INTEGER REFERENCES customers(id),
        reminder_date TEXT,
        type TEXT,
        sent INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)

    # Seed pipeline stages
    c.execute("SELECT COUNT(*) FROM pipeline_stages")
    if c.fetchone()[0] == 0:
        stages = [
            ("Ny", 1, "#6366f1"),
            ("Kontaktad", 2, "#f59e0b"),
            ("Offert skickad", 3, "#3b82f6"),
            ("Förhandling", 4, "#8b5cf6"),
            ("Bokad", 5, "#06b6d4"),
            ("Vunnen", 6, "#10b981"),
            ("Förlorad", 7, "#ef4444"),
        ]
        c.executemany("INSERT INTO pipeline_stages (name, sort_order, color) VALUES (?,?,?)", stages)

    # Seed admin user
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        seller_hash = hashlib.sha256("seller123".encode()).hexdigest()
        c.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
                  ("Admin", "admin@crm.se", admin_hash, "admin"))
        c.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
                  ("Sara Lindqvist", "sara@crm.se", seller_hash, "seller"))
        c.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
                  ("Marcus Holm", "marcus@crm.se", seller_hash, "seller"))

        # Seed demo customers
        c.execute("""INSERT INTO customers (company_name, org_number, contact_person, phone, email,
                     address, city, lead_source, assigned_to, status)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  ("Göteborg Bygg AB", "556123-4567", "Johan Svensson", "031-123456",
                   "johan@gbgbygg.se", "Byggvägen 12", "Göteborg", "Kallringning", 2, "Offert skickad"))
        c.execute("""INSERT INTO customers (company_name, org_number, contact_person, phone, email,
                     address, city, lead_source, assigned_to, status)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  ("Nordic Tech Solutions", "556789-0123", "Anna Berg", "08-987654",
                   "anna@nordictech.se", "Teknikgatan 5", "Stockholm", "LinkedIn", 2, "Förhandling"))
        c.execute("""INSERT INTO customers (company_name, org_number, contact_person, phone, email,
                     address, city, lead_source, assigned_to, status)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  ("Malmö Handel HB", "969123-4567", "Erik Nilsson", "040-555666",
                   "erik@malmohandel.se", "Handelsvägen 3", "Malmö", "Rekommendation", 3, "Vunnen"))

    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(email, password):
    conn = get_conn()
    pw_hash = hash_password(password)
    user = conn.execute(
        "SELECT * FROM users WHERE email=? AND password_hash=?", (email, pw_hash)
    ).fetchone()
    conn.close()
    return dict(user) if user else None

# ── CUSTOMERS ─────────────────────────────────────────────────────────────────
def get_customers(user_id=None, role=None, search=None, status=None):
    conn = get_conn()
    q = """SELECT c.*, u.name as assigned_name
           FROM customers c LEFT JOIN users u ON c.assigned_to=u.id WHERE 1=1"""
    params = []
    if role == "seller" and user_id:
        q += " AND c.assigned_to=?"
        params.append(user_id)
    if search:
        q += " AND (c.company_name LIKE ? OR c.contact_person LIKE ? OR c.phone LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if status:
        q += " AND c.status=?"
        params.append(status)
    q += " ORDER BY c.updated_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer(customer_id):
    conn = get_conn()
    c = conn.execute(
        "SELECT c.*, u.name as assigned_name FROM customers c LEFT JOIN users u ON c.assigned_to=u.id WHERE c.id=?",
        (customer_id,)
    ).fetchone()
    conn.close()
    return dict(c) if c else None

def save_customer(data, customer_id=None):
    conn = get_conn()
    now = datetime.now().isoformat()
    if customer_id:
        conn.execute("""UPDATE customers SET company_name=?, org_number=?, contact_person=?,
                        phone=?, email=?, address=?, city=?, postal_code=?, lead_source=?,
                        assigned_to=?, status=?, notes=?, updated_at=? WHERE id=?""",
                     (data["company_name"], data.get("org_number"), data.get("contact_person"),
                      data.get("phone"), data.get("email"), data.get("address"), data.get("city"),
                      data.get("postal_code"), data.get("lead_source"), data.get("assigned_to"),
                      data.get("status", "Ny"), data.get("notes"), now, customer_id))
        conn.commit(); conn.close()
        return customer_id
    else:
        cur = conn.execute("""INSERT INTO customers (company_name, org_number, contact_person,
                        phone, email, address, city, postal_code, lead_source, assigned_to, status, notes, created_at, updated_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (data["company_name"], data.get("org_number"), data.get("contact_person"),
                      data.get("phone"), data.get("email"), data.get("address"), data.get("city"),
                      data.get("postal_code"), data.get("lead_source"), data.get("assigned_to"),
                      data.get("status", "Ny"), data.get("notes"), now, now))
        conn.commit()
        cid = cur.lastrowid
        conn.close()
        return cid

def delete_customer(customer_id):
    conn = get_conn()
    conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    conn.commit(); conn.close()

def update_customer_status(customer_id, status):
    conn = get_conn()
    conn.execute("UPDATE customers SET status=?, updated_at=? WHERE id=?",
                 (status, datetime.now().isoformat(), customer_id))
    conn.commit(); conn.close()

# ── SERVICES ──────────────────────────────────────────────────────────────────
def get_services(customer_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM services WHERE customer_id=?", (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_service(customer_id, data, service_id=None):
    conn = get_conn()
    if service_id:
        conn.execute("""UPDATE services SET service_type=?, provider=?, current_price=?,
                        contract_end=?, binding_months=?, notes=? WHERE id=?""",
                     (data["service_type"], data.get("provider"), data.get("current_price"),
                      data.get("contract_end"), data.get("binding_months"), data.get("notes"), service_id))
    else:
        conn.execute("""INSERT INTO services (customer_id, service_type, provider, current_price,
                        contract_end, binding_months, notes) VALUES (?,?,?,?,?,?,?)""",
                     (customer_id, data["service_type"], data.get("provider"), data.get("current_price"),
                      data.get("contract_end"), data.get("binding_months"), data.get("notes")))
    conn.commit(); conn.close()

def delete_service(service_id):
    conn = get_conn()
    conn.execute("DELETE FROM services WHERE id=?", (service_id,))
    conn.commit(); conn.close()

# ── ACTIVITIES ────────────────────────────────────────────────────────────────
def get_activities(customer_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT a.*, u.name as user_name FROM activities a
           LEFT JOIN users u ON a.user_id=u.id
           WHERE a.customer_id=? ORDER BY a.created_at DESC""",
        (customer_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_activity(customer_id, user_id, activity_type, description):
    conn = get_conn()
    conn.execute("INSERT INTO activities (customer_id, user_id, activity_type, description) VALUES (?,?,?,?)",
                 (customer_id, user_id, activity_type, description))
    conn.execute("UPDATE customers SET updated_at=? WHERE id=?",
                 (datetime.now().isoformat(), customer_id))
    conn.commit(); conn.close()

# ── QUOTES ────────────────────────────────────────────────────────────────────
def get_quotes(customer_id=None, user_id=None, role=None):
    conn = get_conn()
    q = """SELECT qt.*, c.company_name, u.name as seller_name
           FROM quotes qt
           JOIN customers c ON qt.customer_id=c.id
           LEFT JOIN users u ON qt.created_by=u.id
           WHERE 1=1"""
    params = []
    if customer_id:
        q += " AND qt.customer_id=?"
        params.append(customer_id)
    if role == "seller" and user_id:
        q += " AND c.assigned_to=?"
        params.append(user_id)
    q += " ORDER BY qt.created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_quote(quote_id):
    conn = get_conn()
    q = conn.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
    conn.close()
    return dict(q) if q else None

def save_quote(customer_id, user_id, items, valid_days=30):
    conn = get_conn()
    now = datetime.now().isoformat()
    valid_until = (datetime.now() + timedelta(days=valid_days)).strftime("%Y-%m-%d")

    total_cur = sum(i.get("price_current", 0) or 0 for i in items)
    total_off = sum(i.get("price_offered", 0) or 0 for i in items)
    monthly_saving = total_cur - total_off
    yearly_saving = monthly_saving * 12

    cur = conn.execute("""INSERT INTO quotes (customer_id, created_by, status, total_current,
                          total_offered, monthly_saving, yearly_saving, valid_until, created_at, updated_at)
                          VALUES (?,?,?,?,?,?,?,?,?,?)""",
                       (customer_id, user_id, "Utkast", total_cur, total_off,
                        monthly_saving, yearly_saving, valid_until, now, now))
    quote_id = cur.lastrowid

    for item in items:
        saving = (item.get("price_current") or 0) - (item.get("price_offered") or 0)
        conn.execute("""INSERT INTO quote_items (quote_id, service_type, provider_current,
                        price_current, provider_offered, price_offered, binding_months, saving, notes)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                     (quote_id, item.get("service_type"), item.get("provider_current"),
                      item.get("price_current"), item.get("provider_offered"),
                      item.get("price_offered"), item.get("binding_months"),
                      saving, item.get("notes")))

    # Create reminders
    r7 = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    r14 = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    conn.execute("INSERT INTO reminders (quote_id, customer_id, reminder_date, type) VALUES (?,?,?,?)",
                 (quote_id, customer_id, r7, "7-day"))
    conn.execute("INSERT INTO reminders (quote_id, customer_id, reminder_date, type) VALUES (?,?,?,?)",
                 (quote_id, customer_id, r14, "14-day"))

    conn.commit(); conn.close()
    return quote_id

def get_quote_items(quote_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM quote_items WHERE quote_id=?", (quote_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_quote_status(quote_id, status):
    conn = get_conn()
    conn.execute("UPDATE quotes SET status=?, updated_at=? WHERE id=?",
                 (status, datetime.now().isoformat(), quote_id))
    conn.commit(); conn.close()

# ── PIPELINE ──────────────────────────────────────────────────────────────────
def get_pipeline(user_id=None, role=None):
    conn = get_conn()
    q = """SELECT c.*, u.name as assigned_name,
                  (SELECT COUNT(*) FROM quotes WHERE customer_id=c.id) as quote_count,
                  (SELECT MAX(created_at) FROM activities WHERE customer_id=c.id) as last_activity
           FROM customers c LEFT JOIN users u ON c.assigned_to=u.id WHERE 1=1"""
    params = []
    if role == "seller" and user_id:
        q += " AND c.assigned_to=?"
        params.append(user_id)
    q += " ORDER BY c.updated_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── DASHBOARD STATS ──────────────────────────────────────────────────────────
def get_stats(user_id=None, role=None):
    conn = get_conn()
    params_filter = ""
    params = []
    if role == "seller" and user_id:
        params_filter = " AND c.assigned_to=?"
        params = [user_id]

    total_customers = conn.execute(
        f"SELECT COUNT(*) FROM customers c WHERE 1=1{params_filter}", params
    ).fetchone()[0]

    quotes_out = conn.execute(
        f"""SELECT COUNT(*) FROM quotes qt JOIN customers c ON qt.customer_id=c.id
            WHERE qt.status IN ('Utkast','Skickad'){params_filter.replace('c.', 'c.')}""",
        params
    ).fetchone()[0]

    won_month = conn.execute(
        f"""SELECT COUNT(*) FROM customers c WHERE c.status='Vunnen'
            AND strftime('%Y-%m', c.updated_at)=strftime('%Y-%m', 'now'){params_filter}""",
        params
    ).fetchone()[0]

    pipeline_value = conn.execute(
        f"""SELECT COALESCE(SUM(qt.monthly_saving*12), 0) FROM quotes qt
            JOIN customers c ON qt.customer_id=c.id
            WHERE c.status NOT IN ('Vunnen','Förlorad'){params_filter}""",
        params
    ).fetchone()[0]

    due_reminders = conn.execute(
        """SELECT COUNT(*) FROM reminders r JOIN customers c ON r.customer_id=c.id
           WHERE r.sent=0 AND r.reminder_date <= date('now')"""
    ).fetchone()[0]

    conn.close()
    return {
        "total_customers": total_customers,
        "quotes_out": quotes_out,
        "won_month": won_month,
        "pipeline_value": pipeline_value,
        "due_reminders": due_reminders,
    }

def get_users(role=None):
    conn = get_conn()
    q = "SELECT * FROM users"
    if role:
        q += f" WHERE role='{role}'"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_user(name, email, password, role="seller"):
    conn = get_conn()
    pw_hash = hash_password(password)
    try:
        conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
                     (name, email, pw_hash, role))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False
