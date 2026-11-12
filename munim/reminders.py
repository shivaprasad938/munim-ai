"""Reminder drafts in English, Hindi and Kannada. The owner reviews and approves; nothing is sent."""
T = {
 "en": {
  "friendly": "Hi {name}, a gentle reminder that invoice {no} (Rs {amt}) was due on {due}. Could you please arrange the payment? Thank you!",
  "polite": "Dear {name}, invoice {no} for Rs {amt} was due on {due} and is still unpaid. Kindly clear it at the earliest. Thank you.",
  "firm": "Dear {name}, invoice {no} for Rs {amt} is overdue since {due}. Please pay immediately or tell us the date you will pay."},
 "hi": {
  "friendly": "नमस्ते {name}, चालान {no} (₹{amt}) की देय तिथि {due} थी। कृपया भुगतान कर दें। धन्यवाद!",
  "polite": "आदरणीय {name}, चालान {no} (₹{amt}) की देय तिथि {due} थी और भुगतान अभी बाकी है। कृपया जल्द भुगतान करें। धन्यवाद।",
  "firm": "आदरणीय {name}, चालान {no} (₹{amt}) {due} से अतिदेय है। कृपया तुरंत भुगतान करें या भुगतान की तारीख बताएं।"},
 "kn": {
  "friendly": "ನಮಸ್ಕಾರ {name}, ಇನ್‌ವಾಯ್ಸ್ {no} (₹{amt}) ಪಾವತಿ ದಿನಾಂಕ {due} ಆಗಿತ್ತು. ದಯವಿಟ್ಟು ಪಾವತಿ ಮಾಡಿ. ಧನ್ಯವಾದಗಳು!",
  "polite": "ಆತ್ಮೀಯ {name}, ಇನ್‌ವಾಯ್ಸ್ {no} (₹{amt}) ಪಾವತಿ ದಿನಾಂಕ {due} ಆಗಿದ್ದು ಇನ್ನೂ ಬಾಕಿ ಇದೆ. ದಯವಿಟ್ಟು ಶೀಘ್ರದಲ್ಲಿ ಪಾವತಿಸಿ. ಧನ್ಯವಾದಗಳು.",
  "firm": "ಆತ್ಮೀಯ {name}, ಇನ್‌ವಾಯ್ಸ್ {no} (₹{amt}) {due} ರಿಂದ ಬಾಕಿ ಇದೆ. ದಯವಿಟ್ಟು ತಕ್ಷಣ ಪಾವತಿಸಿ ಅಥವಾ ಪಾವತಿ ದಿನಾಂಕ ತಿಳಿಸಿ."},
}


def draft(inv, tone, lang="en"):
    return T[lang][tone].format(name=inv["party"], no=inv["invoice_no"],
                                amt=f"{inv['total']:,.0f}", due=inv["due_date"])
