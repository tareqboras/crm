import base64, json, os, re
from pathlib import Path

# ── AI SYSTEM PROMPT ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Du är en extremt noggrann svensk fakturaanalys-specialist med djup kunskap om IT- och kommunikationstjänster.
Din uppgift är att analysera fakturor och extrahera ALL relevant information med hög precision.

TJÄNSTER DU KÄNNER IGEN:
- Mobiltelefoni (abonnemang, leasing av telefon, surf, samtal)
- Fast telefoni / SIP-trunk / VoIP
- AI-driven telefonväxel / PBX / Växel
- Bredband fiber / 4G / 5G
- Digital körjournal
- Kopieringsmaskin / Skrivare / MFP
- Kaffemaskin / Vattenautomat
- IT-support / Helpdesk
- Molntjänster (Microsoft 365, Google Workspace)
- Försäkring kopplad till hårdvara
- Övrigt IT/kommunikation

FÖR VARJE TJÄNST, EXTRAHERA:
- Tjänstetyp (kategorisera korrekt)
- Leverantör (Telia, Tele2, Telenor, Tre, Comviq, Bahnhof etc.)
- Beskrivning (vad ingår exakt)
- Månadspris i SEK (exkl. moms om möjligt)
- Bindningstid i månader (0 om ingen bindning)
- Startdatum om angivet
- Hårdvara (ja/nej + beskrivning om relevant)
- Antal enheter om relevant

BESPARINGSANALYS:
- Typiska besparingar vi kan uppnå: 35-45% på telefonabonnemang, 20-35% på bredband, 25-40% på växel
- Beräkna realistisk besparing per tjänst baserat på marknadspriser 2025

SVARA ALLTID I DETTA EXAKTA JSON-FORMAT:
{
  "company_name": "Företagsnamn AB",
  "org_number": "556xxx-xxxx",
  "invoice_date": "YYYY-MM-DD",
  "invoice_number": "fakturanummer",
  "supplier": "Leverantörsnamn",
  "total_monthly_excl_vat": 1234.56,
  "services": [
    {
      "service_type": "Mobiltelefoni",
      "provider": "Telia",
      "description": "Jobbmobil Obegränsat 10GB surf",
      "monthly_price": 299.00,
      "binding_months": 24,
      "is_hardware": false,
      "hardware_description": null,
      "quantity": 3,
      "notes": "Inkluderar roaming EU"
    }
  ],
  "savings_analysis": {
    "current_total_monthly": 1234.56,
    "estimated_saving_pct_low": 35,
    "estimated_saving_pct_high": 45,
    "estimated_saving_monthly_low": 432.10,
    "estimated_saving_monthly_high": 555.55,
    "estimated_saving_yearly_low": 5185.20,
    "estimated_saving_yearly_high": 6666.60,
    "savings_per_service": [
      {
        "service_type": "Mobiltelefoni",
        "current_price": 897.00,
        "potential_price": 537.00,
        "saving_monthly": 360.00,
        "saving_pct": 40
      }
    ],
    "analysis_notes": "Förklaring av besparingsmöjligheter"
  },
  "raw_text_extracted": "Kortare sammanfattning av fakturan"
}

VIKTIGT: Returnera BARA giltig JSON, inga andra kommentarer eller text utanför JSON-strukturen."""

def encode_file_to_base64(file_bytes: bytes) -> str:
    return base64.standard_b64encode(file_bytes).decode("utf-8")

def analyze_invoice_with_ai(file_bytes: bytes, file_type: str, api_key: str = None) -> dict:
    """
    Analyze invoice using Claude API vision.
    file_type: 'pdf' or 'image'
    """
    import urllib.request

    # Use env var or passed key
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return _mock_analysis()

    b64 = encode_file_to_base64(file_bytes)

    if file_type == "pdf":
        media_type = "application/pdf"
        content_item = {
            "type": "document",
            "source": {"type": "base64", "media_type": media_type, "data": b64}
        }
    else:
        # image
        if file_bytes[:4] == b'%PDF':
            media_type = "application/pdf"
            content_item = {"type": "document", "source": {"type": "base64", "media_type": media_type, "data": b64}}
        else:
            media_type = "image/jpeg" if file_type in ["jpg","jpeg"] else f"image/{file_type}"
            content_item = {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}}

    payload = json.dumps({
        "model": "claude-opus-4-5",
        "max_tokens": 4000,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": [
                content_item,
                {"type": "text", "text": "Analysera denna faktura noggrant och returnera JSON enligt format."}
            ]
        }]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            text = "".join(b.get("text","") for b in data.get("content",[]) if b.get("type")=="text")
            # Extract JSON from response
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"error": "Kunde inte parsa JSON från AI-svar", "raw": text[:500]}
    except Exception as e:
        return {"error": str(e)}

def _mock_analysis() -> dict:
    """Demo analysis when no API key is set"""
    return {
        "company_name": "Demo Företag AB",
        "org_number": "556123-4567",
        "invoice_date": "2026-03-01",
        "invoice_number": "INV-2026-001",
        "supplier": "Telia Sverige AB",
        "total_monthly_excl_vat": 4850.00,
        "services": [
            {"service_type": "Mobiltelefoni", "provider": "Telia", "description": "Jobbmobil Obegränsat (5 abonnemang)", "monthly_price": 1495.00, "binding_months": 24, "is_hardware": False, "hardware_description": None, "quantity": 5, "notes": "299 kr/st"},
            {"service_type": "Bredband fiber", "provider": "Telia", "description": "Företagsbredband 1000/1000 Mbit", "monthly_price": 895.00, "binding_months": 24, "is_hardware": False, "hardware_description": None, "quantity": 1, "notes": ""},
            {"service_type": "AI-telefonväxel", "provider": "Telia", "description": "Telia Touchpoint växellösning", "monthly_price": 1290.00, "binding_months": 36, "is_hardware": False, "hardware_description": None, "quantity": 1, "notes": "Inkl. 10 användare"},
            {"service_type": "Kopieringsmaskin", "provider": "Telia", "description": "Canon imageRUNNER leasing", "monthly_price": 890.00, "binding_months": 36, "is_hardware": True, "hardware_description": "Canon imageRUNNER ADVANCE DX", "quantity": 1, "notes": "Inkl. service"},
            {"service_type": "Digital körjournal", "provider": "Telia", "description": "Vehco körjournal 3 fordon", "monthly_price": 280.00, "binding_months": 12, "is_hardware": False, "hardware_description": None, "quantity": 3, "notes": ""},
        ],
        "savings_analysis": {
            "current_total_monthly": 4850.00,
            "estimated_saving_pct_low": 35,
            "estimated_saving_pct_high": 45,
            "estimated_saving_monthly_low": 1697.50,
            "estimated_saving_monthly_high": 2182.50,
            "estimated_saving_yearly_low": 20370.00,
            "estimated_saving_yearly_high": 26190.00,
            "savings_per_service": [
                {"service_type": "Mobiltelefoni", "current_price": 1495.00, "potential_price": 895.00, "saving_monthly": 600.00, "saving_pct": 40},
                {"service_type": "Bredband fiber", "current_price": 895.00, "potential_price": 595.00, "saving_monthly": 300.00, "saving_pct": 34},
                {"service_type": "AI-telefonväxel", "current_price": 1290.00, "potential_price": 790.00, "saving_monthly": 500.00, "saving_pct": 39},
                {"service_type": "Kopieringsmaskin", "current_price": 890.00, "potential_price": 590.00, "saving_monthly": 300.00, "saving_pct": 34},
                {"service_type": "Digital körjournal", "current_price": 280.00, "potential_price": 180.00, "saving_monthly": 100.00, "saving_pct": 36},
            ],
            "analysis_notes": "Tydliga besparingsmöjligheter inom mobiltelefoni (byta till Tele2/Telenor) och växel (modernare molnlösning). Bredband kan förhandlas ner."
        },
        "raw_text_extracted": "Demo-faktura för testning. Ladda in en riktig faktura för AI-analys."
    }

def save_invoice_file(file_bytes: bytes, filename: str, customer_id: int) -> str:
    """Save invoice file and return path"""
    upload_dir = Path("uploads/invoices")
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"customer_{customer_id}_{filename.replace(' ','_')}"
    path = upload_dir / safe_name
    path.write_bytes(file_bytes)
    return str(path)
