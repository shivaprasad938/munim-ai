import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from datetime import date
from munim.rules import validate_gstin, check_invoice, make_gstin
from munim.db import connect, list_invoices
from munim.seed import seed
from munim import analytics as an
from munim.reminders import draft


def test_gstin():
    assert validate_gstin("27AAPFU0939F1ZV")[0]
    assert not validate_gstin("27AAPFU0939F1ZX")[0]
    assert validate_gstin(make_gstin("29", "AABCS1234A"))[0]


def test_flags_and_analytics(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    today = date(2026, 11, 12)
    seed(conn, today)
    invs = list_invoices(conn)
    codes = {f["code"] for i in invs for f in i["flags"]}
    assert {"INVALID_GSTIN", "TOTAL_MISMATCH", "DUPLICATE"} <= codes
    prof = an.payment_profiles(invs)
    assert prof["Sri Lakshmi Traders"]["tone"] == "friendly"
    assert prof["Mysore Fresh Foods"]["tone"] == "firm"
    car = an.cash_at_risk(invs, today)
    assert car["overdue"] > 0 and car["total"] > car["overdue"]
    fc = an.forecast(invs, 0.0, today)
    assert len(fc["series"]) == 31
    assert invs[0]["party"] in draft(invs[0], "friendly", "en")
