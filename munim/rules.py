"""Deterministic invoice checks. Plain code, no AI: every flag carries the rule behind it."""
import re
from datetime import date

CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_RE = re.compile(r"^[0-3][0-9][A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def gstin_check_char(first14: str) -> str:
    total = 0
    for i, ch in enumerate(first14):
        v = CHARS.index(ch) * (1 if i % 2 == 0 else 2)
        total += v // 36 + v % 36
    return CHARS[(36 - total % 36) % 36]


def make_gstin(state: str, pan: str, entity: str = "1") -> str:
    base = f"{state}{pan}{entity}Z"
    return base + gstin_check_char(base)


def validate_gstin(g: str):
    g = (g or "").strip().upper()
    if not GSTIN_RE.match(g):
        return False, "GSTIN must be 15 characters: state code, PAN, entity, 'Z', check digit"
    if gstin_check_char(g[:14]) != g[14]:
        return False, "GSTIN check digit does not match (possible typo)"
    return True, ""


def check_invoice(inv: dict, others: list) -> list:
    """Return a list of flags: {code, message, rule}. `others` = other saved invoices."""
    flags = []
    ok, why = validate_gstin(inv.get("gstin", ""))
    if not ok:
        flags.append({"code": "INVALID_GSTIN", "message": why,
                      "rule": "GSTIN format and mod-36 check-digit validation"})
    diff = round(inv["taxable"] + inv["tax"] - inv["total"], 2)
    if abs(diff) > 1:
        flags.append({"code": "TOTAL_MISMATCH",
                      "message": f"Taxable + tax differs from total by Rs {abs(diff):,.2f}",
                      "rule": "taxable + tax must equal total (tolerance Rs 1)"})
    for o in others:
        if (o["gstin"] == inv["gstin"] and o["invoice_no"] == inv["invoice_no"]
                and o["id"] != inv.get("id")):
            flags.append({"code": "DUPLICATE",
                          "message": f"Invoice {inv['invoice_no']} already saved for this party",
                          "rule": "same GSTIN + invoice number is a duplicate"})
            break
    try:
        if date.fromisoformat(inv["due_date"]) < date.fromisoformat(inv["invoice_date"]):
            flags.append({"code": "DATE_ORDER", "message": "Due date is before invoice date",
                          "rule": "due date must not precede invoice date"})
    except (ValueError, KeyError):
        flags.append({"code": "BAD_DATE", "message": "Date missing or not YYYY-MM-DD",
                      "rule": "dates must be valid ISO dates"})
    return flags
