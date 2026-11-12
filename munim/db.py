import json
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices(
 id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, party TEXT, gstin TEXT,
 invoice_no TEXT, invoice_date TEXT, due_date TEXT,
 taxable REAL, tax REAL, total REAL,
 status TEXT DEFAULT 'open', paid_date TEXT, flags TEXT DEFAULT '[]');
CREATE TABLE IF NOT EXISTS actions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, text TEXT,
 approved_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def connect(path="data/munim.db"):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def list_invoices(conn):
    rows = [dict(r) for r in conn.execute("SELECT * FROM invoices ORDER BY due_date")]
    for r in rows:
        r["flags"] = json.loads(r["flags"] or "[]")
    return rows


def add_invoice(conn, inv: dict, flags: list):
    cur = conn.execute(
        "INSERT INTO invoices(kind,party,gstin,invoice_no,invoice_date,due_date,taxable,tax,total,"
        "status,paid_date,flags) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (inv["kind"], inv["party"], inv["gstin"], inv["invoice_no"], inv["invoice_date"],
         inv["due_date"], inv["taxable"], inv["tax"], inv["total"],
         inv.get("status", "open"), inv.get("paid_date"), json.dumps(flags)))
    conn.commit()
    return cur.lastrowid


def mark_paid(conn, invoice_id, paid_date):
    conn.execute("UPDATE invoices SET status='paid', paid_date=? WHERE id=?", (paid_date, invoice_id))
    conn.commit()


def log_action(conn, invoice_id, text):
    conn.execute("INSERT INTO actions(invoice_id,text) VALUES(?,?)", (invoice_id, text))
    conn.commit()
