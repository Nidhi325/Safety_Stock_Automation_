import os
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SQLITE_PATH = PROJECT_ROOT / "safety_stock.db"

# Database Connection State
_db_type = "SQLite"
_db_status = "Connected to local SQLite database."
_mysql_config = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DB", "safety_stock"),
    "port": int(os.environ.get("MYSQL_PORT", 3306))
}

def get_connection():
    """
    Tries to connect to MySQL based on environment variables.
    Falls back to SQLite if MySQL is unavailable.
    """
    global _db_type, _db_status
    
    # Try MySQL first
    try:
        import pymysql
        conn = pymysql.connect(
            host=_mysql_config["host"],
            user=_mysql_config["user"],
            password=_mysql_config["password"],
            database=_mysql_config["database"],
            port=_mysql_config["port"],
            autocommit=True
        )
        _db_type = "MySQL"
        _db_status = f"Connected to MySQL on {_mysql_config['host']}:{_mysql_config['port']} (Database: {_mysql_config['database']})"
        return conn
    except Exception as mysql_err:
        # If MySQL connection fails (e.g., database doesn't exist, try to connect without database and create it)
        try:
            import pymysql
            conn = pymysql.connect(
                host=_mysql_config["host"],
                user=_mysql_config["user"],
                password=_mysql_config["password"],
                port=_mysql_config["port"]
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{_mysql_config['database']}`")
            conn.select_db(_mysql_config["database"])
            _db_type = "MySQL"
            _db_status = f"Connected to MySQL on {_mysql_config['host']}:{_mysql_config['port']} (Database created & selected)"
            return conn
        except Exception as conn_err:
            # Fall back to SQLite
            _db_type = "SQLite"
            _db_status = f"SQLite Fallback Active. (MySQL error: {str(mysql_err)})"
            
            # Ensure SQLite path parent directories exist
            SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(SQLITE_PATH))
            # Enable foreign keys and dictionary-like row access in SQLite
            conn.row_factory = sqlite3.Row
            return conn

def get_db_type():
    return _db_type

def get_db_status():
    return _db_status

def db_init():
    """
    Initialize database tables.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if _db_type == "MySQL":
        # MySQL Schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                material_id VARCHAR(100) PRIMARY KEY,
                forecast_date DATE,
                forecast_demand FLOAT,
                material_lead_time FLOAT,
                moving_price FLOAT,
                unrestricted FLOAT,
                Safety_Stock FLOAT,
                Reorder_Point FLOAT,
                Inventory_Gap FLOAT,
                Order_Quantity FLOAT,
                Order_Cost FLOAT,
                Suggested_Action VARCHAR(100),
                Inventory_Status VARCHAR(50),
                lead_time_category VARCHAR(50),
                high_lead_time_flag INT,
                xyz_class VARCHAR(10),
                abc_class VARCHAR(10),
                history_months INT,
                last_actual_date DATE,
                last_actual_demand FLOAT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_demand (
                id INT AUTO_INCREMENT PRIMARY KEY,
                material_id VARCHAR(100),
                Date DATE,
                Demand FLOAT,
                UNIQUE KEY uq_material_date (material_id, Date)
            )
        """)
        # Add indexes for fast queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_mat ON historical_demand(material_id)")
    else:
        # SQLite Schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                material_id TEXT PRIMARY KEY,
                forecast_date TEXT,
                forecast_demand REAL,
                material_lead_time REAL,
                moving_price REAL,
                unrestricted REAL,
                Safety_Stock REAL,
                Reorder_Point REAL,
                Inventory_Gap REAL,
                Order_Quantity REAL,
                Order_Cost REAL,
                Suggested_Action TEXT,
                Inventory_Status TEXT,
                lead_time_category TEXT,
                high_lead_time_flag INTEGER,
                xyz_class TEXT,
                abc_class TEXT,
                history_months INTEGER,
                last_actual_date TEXT,
                last_actual_demand REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_demand (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id TEXT,
                Date TEXT,
                Demand REAL,
                UNIQUE(material_id, Date)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_mat ON historical_demand(material_id)")
    
    conn.close()

def import_predictions_csv(csv_path):
    """
    Import the predictions CSV into the database.
    """
    if not os.path.exists(csv_path):
        print(f"Predictions CSV not found: {csv_path}")
        return False
        
    df = pd.read_csv(csv_path)
    # Strip material ID
    df['material_id'] = df['material_id'].astype(str).str.strip()
    
    # Ensure correct dates
    if 'forecast_date' in df.columns:
        df['forecast_date'] = pd.to_datetime(df['forecast_date']).dt.strftime('%Y-%m-%d')
    if 'last_actual_date' in df.columns:
        df['last_actual_date'] = pd.to_datetime(df['last_actual_date']).dt.strftime('%Y-%m-%d')
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ingest rows
    cols = [
        'material_id', 'forecast_date', 'forecast_demand', 'material_lead_time',
        'moving_price', 'unrestricted', 'Safety_Stock', 'Reorder_Point',
        'Inventory_Gap', 'Order_Quantity', 'Order_Cost', 'Suggested_Action',
        'Inventory_Status', 'lead_time_category', 'high_lead_time_flag',
        'xyz_class', 'abc_class', 'history_months', 'last_actual_date', 'last_actual_demand'
    ]
    
    # Filter df to keep only existing columns that we have in our schema
    available_cols = [c for c in cols if c in df.columns]
    
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        # Clean null values to None for database compatibility
        cleaned_row = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
        
        row_cols = [c for c in available_cols if c in cleaned_row]
        vals = [cleaned_row[c] for c in row_cols]
        
        if _db_type == "MySQL":
            placeholders = ", ".join(["%s"] * len(row_cols))
            update_clause = ", ".join([f"`{c}` = VALUES(`{c}`)" for c in row_cols if c != 'material_id'])
            query = f"INSERT INTO predictions ({', '.join(row_cols)}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"
        else:
            placeholders = ", ".join(["?"] * len(row_cols))
            query = f"INSERT OR REPLACE INTO predictions ({', '.join(row_cols)}) VALUES ({placeholders})"
            
        cursor.execute(query, vals)
        
    conn.commit()
    conn.close()
    return True

def import_historical_csv(csv_path):
    """
    Import the historical dataset CSV into the database.
    """
    if not os.path.exists(csv_path):
        print(f"Historical CSV not found: {csv_path}")
        return False
        
    df = pd.read_csv(csv_path)
    df['material_id'] = df['material_id'].astype(str).str.strip()
    
    # Resolve Date column name case insensitively
    date_col = None
    for c in df.columns:
        if c.lower() == 'date':
            date_col = c
            break
            
    demand_col = None
    for c in df.columns:
        if c.lower() == 'demand':
            demand_col = c
            break
            
    if not date_col or not demand_col:
        print("Required Date or Demand column not found in historical file.")
        return False
        
    df['parsed_date'] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # We will insert in chunks for speed
    chunk_size = 1000
    rows_to_insert = []
    
    for _, row in df.iterrows():
        val = (row['material_id'], row['parsed_date'], float(row[demand_col]) if not pd.isna(row[demand_col]) else 0.0)
        rows_to_insert.append(val)
        
    # Bulk insert
    if _db_type == "MySQL":
        query = "INSERT INTO historical_demand (material_id, Date, Demand) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE Demand = VALUES(Demand)"
    else:
        query = "INSERT OR REPLACE INTO historical_demand (material_id, Date, Demand) VALUES (?, ?, ?)"
        
    for i in range(0, len(rows_to_insert), chunk_size):
        chunk = rows_to_insert[i:i+chunk_size]
        cursor.executemany(query, chunk)
        
    conn.commit()
    conn.close()
    return True

def get_material_details(material_id):
    """
    Fetch all metrics for a specific material, plus its historical demand series.
    """
    material_id = str(material_id).strip()
    conn = get_connection()
    
    # Get prediction details
    if _db_type == "MySQL":
        cursor = conn.cursor(dictionary=True) if hasattr(conn, 'cursor') else conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE material_id = %s", (material_id,))
        pred = cursor.fetchone()
        
        # If MySQL cursor doesn't support dictionary=True natively:
        if pred and not isinstance(pred, dict):
            columns = [desc[0] for desc in cursor.description]
            pred = dict(zip(columns, pred))
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE material_id = ?", (material_id,))
        row = cursor.fetchone()
        pred = dict(row) if row else None
        
    if not pred:
        conn.close()
        return None
        
    # Get historical demand
    if _db_type == "MySQL":
        cursor.execute("SELECT Date, Demand FROM historical_demand WHERE material_id = %s ORDER BY Date ASC", (material_id,))
        history_rows = cursor.fetchall()
        if history_rows and not isinstance(history_rows[0], dict):
            history = [{"Date": str(r[0]), "Demand": float(r[1])} for r in history_rows]
        else:
            history = [{"Date": str(r["Date"]), "Demand": float(r["Demand"])} for r in history_rows]
    else:
        cursor.execute("SELECT Date, Demand FROM historical_demand WHERE material_id = ? ORDER BY Date ASC", (material_id,))
        history = [{"Date": str(r["Date"]), "Demand": float(r["Demand"])} for r in cursor.fetchall()]
        
    conn.close()
    
    return {
        "metrics": pred,
        "history": history
    }

def get_analytics_summary():
    """
    Fetch aggregated summary statistics for the dashboard.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Helper to clean cursor output
    def fetch_one_val(query):
        cursor.execute(query)
        res = cursor.fetchone()
        return res[0] if res else 0
        
    total_materials = fetch_one_val("SELECT COUNT(*) FROM predictions")
    if total_materials == 0:
        conn.close()
        return None
        
    total_order_cost = fetch_one_val("SELECT SUM(Order_Cost) FROM predictions") or 0.0
    materials_to_order = fetch_one_val("SELECT COUNT(*) FROM predictions WHERE Order_Quantity > 0")
    avg_lead_time = fetch_one_val("SELECT AVG(material_lead_time) FROM predictions") or 0.0
    
    # Breakdowns
    def fetch_breakdown(query):
        cursor.execute(query)
        rows = cursor.fetchall()
        # Handles both SQLite and MySQL cursor formats
        if _db_type == "MySQL":
            if rows and hasattr(rows[0], 'keys') or isinstance(rows[0], dict):
                return {r[0]: r[1] for r in rows}
        return {r[0]: r[1] for r in rows}
        
    suggested_actions = fetch_breakdown("SELECT Suggested_Action, COUNT(*) FROM predictions GROUP BY Suggested_Action")
    inventory_status = fetch_breakdown("SELECT Inventory_Status, COUNT(*) FROM predictions GROUP BY Inventory_Status")
    abc_class = fetch_breakdown("SELECT abc_class, COUNT(*) FROM predictions GROUP BY abc_class")
    xyz_class = fetch_breakdown("SELECT xyz_class, COUNT(*) FROM predictions GROUP BY xyz_class")
    
    # Cost by ABC class
    abc_costs = fetch_breakdown("SELECT abc_class, SUM(Order_Cost) FROM predictions GROUP BY abc_class")
    
    # ABC-XYZ Cross-tabulation Matrix
    cursor.execute("SELECT abc_class, xyz_class, COUNT(*) FROM predictions GROUP BY abc_class, xyz_class")
    matrix_rows = cursor.fetchall()
    matrix = {}
    for r in matrix_rows:
        if isinstance(r, dict):
            abc = r.get('abc_class')
            xyz = r.get('xyz_class')
            count = r.get('COUNT(*)') or list(r.values())[2]
        elif hasattr(r, 'keys') and not isinstance(r, tuple):
            abc = r['abc_class']
            xyz = r['xyz_class']
            count = r[2]
        else:
            abc = r[0]
            xyz = r[1]
            count = r[2]
            
        if abc and xyz:
            matrix[f"{str(abc).strip()}{str(xyz).strip()}"] = count
            
    conn.close()
    
    return {
        "total_materials": total_materials,
        "total_order_cost": round(total_order_cost, 2),
        "materials_to_order": materials_to_order,
        "avg_lead_time": round(avg_lead_time, 1),
        "breakdowns": {
            "suggested_actions": suggested_actions,
            "inventory_status": inventory_status,
            "abc_class": abc_class,
            "xyz_class": xyz_class,
            "abc_costs": abc_costs
        },
        "matrix": matrix
    }

def get_inventory_list(page=1, per_page=15, search_query="", action_filter=None, status_filter=None, abc_filter=None, xyz_filter=None):
    """
    Fetch a paginated, filtered list of materials.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build query clauses
    clauses = []
    params = []
    
    if search_query:
        clauses.append("material_id LIKE ?")
        params.append(f"%{search_query}%")
        
    if action_filter:
        clauses.append("Suggested_Action = ?")
        params.append(action_filter)
        
    if status_filter:
        clauses.append("Inventory_Status = ?")
        params.append(status_filter)
        
    if abc_filter:
        clauses.append("abc_class = ?")
        params.append(abc_filter)
        
    if xyz_filter:
        clauses.append("xyz_class = ?")
        params.append(xyz_filter)
        
    where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
    
    # Adjust placeholders for MySQL
    if _db_type == "MySQL":
        where_clause = where_clause.replace("LIKE ?", "LIKE %s").replace("= ?", "= %s")
        
    # Get total count
    count_query = f"SELECT COUNT(*) FROM predictions{where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # Get paginated data
    offset = (page - 1) * per_page
    data_query = f"SELECT * FROM predictions{where_clause} ORDER BY material_id ASC LIMIT %s OFFSET %s" if _db_type == "MySQL" else f"SELECT * FROM predictions{where_clause} ORDER BY material_id ASC LIMIT ? OFFSET ?"
    
    data_params = params + [per_page, offset]
    cursor.execute(data_query, data_params)
    
    rows = cursor.fetchall()
    
    # Format rows
    materials_list = []
    if _db_type == "MySQL":
        columns = [desc[0] for desc in cursor.description]
        for r in rows:
            if isinstance(r, dict):
                materials_list.append(r)
            else:
                materials_list.append(dict(zip(columns, r)))
    else:
        for r in rows:
            materials_list.append(dict(r))
            
    conn.close()
    
    return {
        "materials": materials_list,
        "total_count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page if total_count > 0 else 0
    }


def get_predictions_page(page=1, per_page=20, search="", abc=None, xyz=None, status=None, action=None):
    """Fetch a paginated, filtered view of the predictions table."""
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if _db_type == "MySQL" else "?"
    clauses, params = [], []
    if search:
        clauses.append(f"material_id LIKE {ph}"); params.append(f"%{search}%")
    if abc:
        clauses.append(f"abc_class = {ph}"); params.append(abc)
    if xyz:
        clauses.append(f"xyz_class = {ph}"); params.append(xyz)
    if status:
        clauses.append(f"Inventory_Status = {ph}"); params.append(status)
    if action:
        clauses.append(f"Suggested_Action = {ph}"); params.append(action)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    cursor.execute(f"SELECT COUNT(*) FROM predictions {where}", params)
    total = cursor.fetchone()[0]
    offset = (page - 1) * per_page
    cursor.execute(
        f"""SELECT material_id, forecast_date, forecast_demand, Safety_Stock, Reorder_Point,
                   unrestricted, Order_Quantity, Order_Cost, Inventory_Gap,
                   Suggested_Action, Inventory_Status, abc_class, xyz_class,
                   material_lead_time, moving_price, lead_time_category, history_months
            FROM predictions {where} ORDER BY material_id ASC LIMIT {ph} OFFSET {ph}""",
        params + [per_page, offset])
    rows = cursor.fetchall()
    if _db_type == "MySQL":
        cols = [d[0] for d in cursor.description]
        materials = [dict(zip(cols, r)) if not isinstance(r, dict) else r for r in rows]
    else:
        materials = [dict(r) for r in rows]
    conn.close()
    return {"materials": materials, "total_count": total, "page": page,
            "per_page": per_page, "total_pages": max(1, (total + per_page - 1) // per_page)}


def get_all_predictions_df():
    """Return the full predictions table as a pandas DataFrame for CSV download."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM predictions ORDER BY material_id", conn)
    conn.close()
    return df


def get_historical_page(page=1, per_page=25, search="", year=None, abc=None, xyz=None):
    """Fetch a paginated, filtered view of historical_demand joined with class info."""
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if _db_type == "MySQL" else "?"
    clauses, params = [], []
    if search:
        clauses.append(f"h.material_id LIKE {ph}"); params.append(f"%{search}%")
    if year:
        if _db_type == "MySQL":
            clauses.append(f"YEAR(h.Date) = {ph}")
        else:
            clauses.append(f"strftime('%Y', h.Date) = {ph}")
        params.append(str(year))
    if abc:
        clauses.append(f"p.abc_class = {ph}"); params.append(abc)
    if xyz:
        clauses.append(f"p.xyz_class = {ph}"); params.append(xyz)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    join_sql = "LEFT JOIN predictions p ON h.material_id = p.material_id"
    base = f"FROM historical_demand h {join_sql} {where}"
    cursor.execute(f"SELECT COUNT(*) {base}", params)
    total = cursor.fetchone()[0]
    offset = (page - 1) * per_page
    cursor.execute(
        f"""SELECT h.material_id, h.Date, h.Demand, p.abc_class, p.xyz_class, p.moving_price
            {base} ORDER BY h.Date DESC, h.material_id ASC LIMIT {ph} OFFSET {ph}""",
        params + [per_page, offset])
    rows = cursor.fetchall()
    if _db_type == "MySQL":
        cols = [d[0] for d in cursor.description]
        records = [dict(zip(cols, r)) if not isinstance(r, dict) else r for r in rows]
    else:
        records = [dict(r) for r in rows]
    conn.close()
    return {"records": records, "total_count": total, "page": page,
            "per_page": per_page, "total_pages": max(1, (total + per_page - 1) // per_page)}


def get_all_historical_df():
    """Return full historical_demand joined with abc/xyz class as a DataFrame."""
    conn = get_connection()
    sql = """SELECT h.material_id, h.Date, h.Demand, p.abc_class, p.xyz_class, p.moving_price
             FROM historical_demand h
             LEFT JOIN predictions p ON h.material_id = p.material_id
             ORDER BY h.material_id, h.Date"""
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


def get_recommendations():
    """Compute rule-based smart insights from the predictions table."""
    conn = get_connection()
    cursor = conn.cursor()
    def one(q):
        cursor.execute(q); r = cursor.fetchone(); return (r[0] if r else 0) or 0
    total    = one("SELECT COUNT(*) FROM predictions")
    if total == 0:
        conn.close(); return []
    critical = one("SELECT COUNT(*) FROM predictions WHERE Inventory_Status='Critical'")
    low      = one("SELECT COUNT(*) FROM predictions WHERE Inventory_Status='Low'")
    to_order = one("SELECT COUNT(*) FROM predictions WHERE Suggested_Action='Order Material'")
    tot_cost = one("SELECT SUM(Order_Cost) FROM predictions")
    avg_lead = one("SELECT AVG(material_lead_time) FROM predictions")
    a_crit   = one("SELECT COUNT(*) FROM predictions WHERE abc_class='A' AND Inventory_Status='Critical'")
    cursor.execute("""SELECT material_id FROM predictions
                      WHERE xyz_class='Z' AND Suggested_Action='Order Material'
                      ORDER BY Order_Cost DESC LIMIT 5""")
    z_ids = [str(r[0]) for r in cursor.fetchall()]
    conn.close()
    recs = []
    sufficient = total - critical - low
    if critical > 0:
        pct = round(critical / total * 100, 1)
        sev = "critical" if pct > 15 else "warning"
        recs.append({"type": sev, "icon": "🔴" if sev == "critical" else "🟠",
                     "title": f"{critical} Materials in Critical Status ({pct}%)",
                     "body": (f"**{critical}** materials are below their safety stock threshold "
                              f"({pct}% of portfolio). Immediate replenishment is recommended.")})
    if a_crit > 0:
        recs.append({"type": "critical", "icon": "⚠️",
                     "title": f"{a_crit} HIGH-VALUE (Class A) Materials are Critical",
                     "body": f"**{a_crit}** Class A materials are critically low. These drive the most value — prioritize them first."})
    if tot_cost > 0:
        recs.append({"type": "info", "icon": "💰",
                     "title": f"Estimated Replenishment Budget: ${tot_cost:,.0f}",
                     "body": f"Replenishing all **{to_order}** flagged materials requires an estimated **${tot_cost:,.0f}**."})
    if z_ids:
        recs.append({"type": "warning", "icon": "📊",
                     "title": "Erratic Demand (Class Z) Materials Need Attention",
                     "body": f"Class Z materials with high cost needing action: **{', '.join(z_ids)}**. Consider higher safety buffers."})
    if avg_lead > 45:
        recs.append({"type": "warning", "icon": "⏱️",
                     "title": f"High Average Lead Time: {avg_lead:.0f} Days",
                     "body": f"Average lead time is **{avg_lead:.0f} days**. Order in advance — Long lead-time materials are at elevated risk."})
    if sufficient > 0:
        pct = round(sufficient / total * 100, 1)
        recs.append({"type": "success", "icon": "✅",
                     "title": f"{sufficient} Materials ({pct}%) are Well-Stocked",
                     "body": f"**{sufficient}** materials have sufficient inventory above safety stock. No action needed."})
    return recs
# Auto-initialize database on import for Streamlit Cloud
try:
    import streamlit as st
    @st.cache_resource
    def _auto_init_db():
        db_init()
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM predictions')
        count = c.fetchone()[0]
        conn.close()
        if count == 0:
            import_predictions_csv()
            import_historical_csv()
    _auto_init_db()
except Exception:
    pass
