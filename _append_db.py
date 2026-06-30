new_functions = r'''

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
'''

with open("db.py", "a", encoding="utf-8") as f:
    f.write(new_functions)

print("Successfully appended new db functions.")
