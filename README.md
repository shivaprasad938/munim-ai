# Munim AI: Cash-at-Risk Radar for Micro Enterprises

An AI early-warning system for micro enterprises (problem statement 3.1). It turns invoice photos and PDFs into verified records, then tells the owner what to fix or collect this week.

**AI reads and writes. Plain code does the maths and checks. The owner approves every action.**

## Features
- Invoice extraction from a photo or PDF with a vision LLM (party, GSTIN, amounts, dates, tax)
- Code-based checks: invalid GSTIN (format and check digit), total mismatch, duplicates, date order
- Explain-Why flags: every alert shows the rule behind it
- Receivables and payables aging
- Customer Payment Profile: average delay per customer, predicted payment date, reminder tone
- Cash-at-Risk Meter: overdue receivables plus an estimated error exposure (labelled as an estimate)
- 30-Day Cash Gap Forecast with a "chase these first" list
- Reminder drafts in English, Hindi and Kannada. Nothing is sent automatically.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY for photo/PDF extraction
export ANTHROPIC_API_KEY=your-key
streamlit run app.py
```
Click "Load synthetic demo data" in the sidebar to see every feature without a key. Manual entry works without a key too.

## Test
```bash
pytest
```

## Layout
- `app.py` Streamlit UI
- `munim/rules.py` GSTIN and invoice checks
- `munim/analytics.py` aging, profiles, Cash-at-Risk, forecast
- `munim/extract.py` vision LLM extraction
- `munim/reminders.py` trilingual drafts
- `munim/seed.py` synthetic data

## Responsible AI
- Synthetic or consented data only
- Nothing is sent or filed without the owner's approval
- The error-exposure rate (`ERROR_EXPOSURE_RATE`) and default delay are assumptions. Verify rules and rates against official GST sources before relying on them.
- Hindi and Kannada reminder templates should be reviewed by a native speaker.
