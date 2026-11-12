"""Synthetic demo data only. Every party and number here is made up."""
from datetime import date, timedelta
from .rules import make_gstin, check_invoice
from .db import add_invoice, list_invoices

PARTIES = [("Sri Lakshmi Traders", "AABCS1234A"), ("Mysore Fresh Foods", "AABCM5678B"),
           ("Kaveri Stationers", "AABCK9012C"), ("Chamundi Hardware", "AABCC3456D")]


def seed(conn, today=None):
    today = today or date.today()
    if list_invoices(conn):
        return
    g = {n: make_gstin("29", pan) for n, pan in PARTIES}
    iso = lambda n: (today + timedelta(days=n)).isoformat()
    rows = []  # (kind, party, no, inv_off, due_off, taxable, status, paid_off, tweak)
    for k in range(3):  # Lakshmi: pays ~2 days late -> friendly
        rows.append(("sale", PARTIES[0][0], f"SL-{k}", -90 + k * 20, -60 + k * 20, 20000, "paid", -58 + k * 20, None))
    for k in range(3):  # Mysore Fresh: pays ~25 days late -> firm
        rows.append(("sale", PARTIES[1][0], f"MF-{k}", -120 + k * 25, -90 + k * 25, 35000, "paid", -65 + k * 25, None))
    rows += [("sale", PARTIES[0][0], "SL-10", -40, -10, 28000, "open", None, None),
             ("sale", PARTIES[1][0], "MF-10", -70, -40, 52000, "open", None, "mismatch"),
             ("sale", PARTIES[2][0], "KS-10", -20, 5, 15000, "open", None, None),
             ("sale", PARTIES[2][0], "KS-10", -20, 5, 15000, "open", None, None),  # duplicate
             ("sale", PARTIES[3][0], "CH-10", -15, 12, 41000, "open", None, "badgstin"),
             ("purchase", PARTIES[3][0], "P-100", -10, 8, 60000, "open", None, None),
             ("purchase", PARTIES[2][0], "P-101", -5, 20, 25000, "open", None, None)]
    for kind, party, no, io, do, taxable, status, po, tweak in rows:
        tax = round(taxable * 0.18, 2)
        inv = {"kind": kind, "party": party, "gstin": g[party], "invoice_no": no,
               "invoice_date": iso(io), "due_date": iso(do), "taxable": taxable, "tax": tax,
               "total": taxable + tax, "status": status, "paid_date": iso(po) if po is not None else None}
        if tweak == "mismatch":
            inv["total"] += 1180
        if tweak == "badgstin":
            inv["gstin"] = inv["gstin"][:-1] + ("A" if inv["gstin"][-1] != "A" else "B")
        add_invoice(conn, inv, check_invoice(inv, list_invoices(conn)))
