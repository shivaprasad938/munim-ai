"""Cash-at-Risk, aging, customer payment profiles and the 30-day cash forecast."""
from collections import defaultdict
from datetime import date, timedelta

# ESTIMATE, not a statutory figure: assumed cost of an unresolved error as a share of its tax.
ERROR_EXPOSURE_RATE = 0.18
DEFAULT_DELAY_DAYS = 7  # used when a customer has no payment history


def d(s):
    return date.fromisoformat(s)


def aging(invoices, kind, today):
    buckets = {"Not due": 0.0, "1-30 days": 0.0, "31-60 days": 0.0, "60+ days": 0.0}
    for i in invoices:
        if i["kind"] != kind or i["status"] != "open":
            continue
        late = (today - d(i["due_date"])).days
        key = ("Not due" if late <= 0 else "1-30 days" if late <= 30
               else "31-60 days" if late <= 60 else "60+ days")
        buckets[key] += i["total"]
    return buckets


def payment_profiles(invoices):
    delays = defaultdict(list)
    for i in invoices:
        if i["kind"] == "sale" and i["status"] == "paid" and i["paid_date"]:
            delays[i["party"]].append((d(i["paid_date"]) - d(i["due_date"])).days)
    out = {}
    for party, v in delays.items():
        avg = sum(v) / len(v)
        tone = "friendly" if avg <= 3 else "polite" if avg <= 15 else "firm"
        out[party] = {"avg_delay": round(avg, 1), "n": len(v), "tone": tone}
    return out


def predicted_pay_date(inv, profiles, today):
    delay = profiles.get(inv["party"], {}).get("avg_delay", DEFAULT_DELAY_DAYS)
    return max(d(inv["due_date"]) + timedelta(days=round(delay)), today)


def cash_at_risk(invoices, today):
    overdue = sum(i["total"] for i in invoices
                  if i["kind"] == "sale" and i["status"] == "open" and d(i["due_date"]) < today)
    exposure = ERROR_EXPOSURE_RATE * sum(i["tax"] for i in invoices
                                         if i["status"] == "open" and i["flags"])
    return {"overdue": overdue, "error_exposure_estimate": round(exposure, 2),
            "total": round(overdue + exposure, 2)}


def forecast(invoices, opening, today, days=30):
    profiles = payment_profiles(invoices)
    delta = defaultdict(float)
    for i in invoices:
        if i["status"] != "open":
            continue
        if i["kind"] == "sale":
            delta[predicted_pay_date(i, profiles, today)] += i["total"]
        else:
            delta[max(d(i["due_date"]), today)] -= i["total"]
    balance, series = opening, []
    for n in range(days + 1):
        day = today + timedelta(days=n)
        balance += delta.get(day, 0.0)
        series.append((day, round(balance, 2)))
    short = next(((day, b) for day, b in series if b < 0), None)
    chase = sorted((i for i in invoices if i["kind"] == "sale" and i["status"] == "open"
                    and d(i["due_date"]) <= today + timedelta(days=days)),
                   key=lambda i: (d(i["due_date"]), -i["total"]))
    return {"series": series, "shortfall": short, "chase": chase[:5],
            "min_balance": min(b for _, b in series)}
