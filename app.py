from datetime import date

import pandas as pd
import streamlit as st

from munim import analytics as an
from munim.db import add_invoice, connect, list_invoices, log_action, mark_paid
from munim.reminders import draft
from munim.rules import check_invoice
from munim.seed import seed

st.set_page_config(page_title="Munim AI", page_icon="₹", layout="wide")
conn = connect()
today = date.today()

st.title("Munim AI: Cash-at-Risk Radar")
with st.sidebar:
    lang = st.selectbox("Reminder language", ["en", "hi", "kn"],
                        format_func={"en": "English", "hi": "हिन्दी", "kn": "ಕನ್ನಡ"}.get)
    opening = st.number_input("Opening cash balance (Rs)", value=50000.0, step=5000.0)
    if st.button("Load synthetic demo data"):
        seed(conn)
        st.rerun()
    st.caption("Demo data is synthetic. Nothing is sent or filed without your approval.")

invs = list_invoices(conn)
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Add invoice", "Invoices", "Reminders"])

with tab1:
    if not invs:
        st.info("No invoices yet. Add one, or load the synthetic demo data from the sidebar.")
    else:
        car = an.cash_at_risk(invs, today)
        c1, c2, c3 = st.columns(3)
        c1.metric("Cash-at-Risk", f"Rs {car['total']:,.0f}")
        c2.metric("Stuck in overdue invoices", f"Rs {car['overdue']:,.0f}")
        c3.metric("Error exposure (estimate)", f"Rs {car['error_exposure_estimate']:,.0f}")
        st.caption(f"Estimate = {an.ERROR_EXPOSURE_RATE:.0%} of tax on open invoices with flags. "
                   "An assumption, not an official figure.")
        a1, a2 = st.columns(2)
        a1.subheader("Receivables by age")
        a1.bar_chart(pd.Series(an.aging(invs, "sale", today)))
        a2.subheader("Payables by age")
        a2.bar_chart(pd.Series(an.aging(invs, "purchase", today)))
        st.subheader("30-day cash forecast")
        fc = an.forecast(invs, opening, today)
        st.line_chart(pd.DataFrame(fc["series"], columns=["date", "balance"]).set_index("date"))
        if fc["shortfall"]:
            st.error(f"Predicted shortfall from {fc['shortfall'][0]}: lowest balance "
                     f"Rs {fc['min_balance']:,.0f}. Chase these first:")
        else:
            st.success("No shortfall predicted in the next 30 days. Invoices to follow up:")
        for i in fc["chase"]:
            st.write(f"- {i['party']} · {i['invoice_no']} · Rs {i['total']:,.0f} · due {i['due_date']}")
        st.subheader("Customer payment profiles")
        prof = an.payment_profiles(invs)
        st.dataframe(pd.DataFrame(prof).T.rename(columns={"avg_delay": "avg delay (days)",
                     "n": "paid invoices", "tone": "reminder tone"}))

with tab2:
    st.write("Upload an invoice photo or PDF to extract the details with AI, or type them in.")
    up = st.file_uploader("Invoice", type=["png", "jpg", "jpeg", "pdf"])
    prefill = st.session_state.get("prefill", {})
    if up and st.button("Extract with AI"):
        try:
            from munim.extract import extract_invoice
            st.session_state["prefill"] = prefill = extract_invoice(up.getvalue(), up.type)
            st.success("Extracted. Review every field before saving.")
        except Exception as e:  # missing key, network or parse error
            st.warning(f"AI extraction unavailable ({e}). Enter the details manually.")
    kind = st.radio("Type", ["sale", "purchase"], horizontal=True)
    c1, c2 = st.columns(2)
    party = c1.text_input("Party", prefill.get("party") or "")
    gstin = c2.text_input("GSTIN", prefill.get("gstin") or "")
    no = c1.text_input("Invoice no.", prefill.get("invoice_no") or "")
    idate = c2.text_input("Invoice date (YYYY-MM-DD)", prefill.get("invoice_date") or today.isoformat())
    ddate = c1.text_input("Due date (YYYY-MM-DD)", prefill.get("due_date") or today.isoformat())
    taxable = c2.number_input("Taxable value", value=float(prefill.get("taxable") or 0))
    tax = c1.number_input("Tax", value=float(prefill.get("tax") or 0))
    total = c2.number_input("Total", value=float(prefill.get("total") or 0))
    if st.button("Check and save"):
        inv = {"kind": kind, "party": party, "gstin": gstin.strip().upper(), "invoice_no": no,
               "invoice_date": idate, "due_date": ddate, "taxable": taxable, "tax": tax, "total": total}
        flags = check_invoice(inv, invs)
        add_invoice(conn, inv, flags)
        st.session_state.pop("prefill", None)
        for f in flags:
            st.warning(f"{f['code']}: {f['message']}  (rule: {f['rule']})")
        st.success("Saved." if not flags else "Saved with flags. Please review.")

with tab3:
    for i in invs:
        mark = "🚩 " if i["flags"] and i["status"] == "open" else ""
        with st.expander(f"{mark}{i['kind']} · {i['party']} · {i['invoice_no']} · Rs {i['total']:,.0f} · {i['status']}"):
            st.write(f"GSTIN {i['gstin']} · invoice {i['invoice_date']} · due {i['due_date']}")
            for f in i["flags"]:
                st.warning(f"**{f['code']}**: {f['message']}\n\nWhy: {f['rule']}")
            if i["status"] == "open" and st.button("Mark paid today", key=f"p{i['id']}"):
                mark_paid(conn, i["id"], today.isoformat())
                st.rerun()

with tab4:
    prof = an.payment_profiles(invs)
    overdue = [i for i in invs if i["kind"] == "sale" and i["status"] == "open"
               and an.d(i["due_date"]) < today]
    if not overdue:
        st.info("No overdue receivables.")
    for i in overdue:
        tone = prof.get(i["party"], {}).get("tone", "polite")
        pred = an.predicted_pay_date(i, prof, today)
        st.markdown(f"**{i['party']}** · {i['invoice_no']} · Rs {i['total']:,.0f} · "
                    f"tone: {tone} · predicted payment {pred}")
        text = st.text_area("Draft (edit if needed)", draft(i, tone, lang), key=f"t{i['id']}")
        if st.button("Approve", key=f"a{i['id']}"):
            log_action(conn, i["id"], text)
            st.success("Approved and logged. Copy it into WhatsApp or SMS yourself; Munim never sends on its own.")
