"""Invoice extraction with a vision LLM. AI reads; rules in rules.py verify."""
import base64
import json
import os

PROMPT = ("Extract this Indian GST invoice. Reply with ONLY a JSON object with keys: "
          "party (name of the other party), gstin, invoice_no, invoice_date (YYYY-MM-DD), "
          "due_date (YYYY-MM-DD, or invoice_date + 30 days if absent), taxable, tax, total "
          "(numbers). Use null for anything unreadable. Do not guess.")


def extract_invoice(data: bytes, media_type: str) -> dict:
    import anthropic  # imported lazily so the rest of the app runs without it
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    block_type = "document" if media_type == "application/pdf" else "image"
    block = {"type": block_type, "source": {"type": "base64", "media_type": media_type,
                                            "data": base64.b64encode(data).decode()}}
    msg = client.messages.create(
        model=os.getenv("MUNIM_MODEL", "claude-sonnet-4-6"), max_tokens=1000,
        messages=[{"role": "user", "content": [block, {"type": "text", "text": PROMPT}]}])
    text = "".join(b.text for b in msg.content if b.type == "text")
    return json.loads(text.replace("```json", "").replace("```", "").strip())
