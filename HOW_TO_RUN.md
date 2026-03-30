# 🚀 CRM Säljsystem — Kom igång

## Systemkrav
- Python 3.9+
- pip

---

## Installation (1 gång)

```bash
# 1. Klona eller ladda ned mappen
cd crm

# 2. Skapa virtuell miljö (rekommenderat)
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 3. Installera beroenden
pip install -r requirements.txt
```

---

## Starta systemet

```bash
streamlit run app.py
```

Öppnas automatiskt i webbläsaren på **http://localhost:8501**

---

## Inloggning (demo)

| Roll    | E-post          | Lösenord  |
|---------|-----------------|-----------|
| Admin   | admin@crm.se    | admin123  |
| Säljare | sara@crm.se     | seller123 |
| Säljare | marcus@crm.se   | seller123 |

---

## Funktioner

### 📊 Dashboard
- KPI-kort: kunder, offerter ute, vunna, pipeline-värde
- Pipeline-översikt per steg
- Snabbknappar

### 👥 Kunder
- Lägg till / redigera / ta bort kunder
- Kundkort med aktivitetslogg, tjänster, offerter
- Statushantering direkt i kundkortet
- Logga samtal, möten, mejl med ett klick

### 📄 Offerter
- Offertbyggare med rad-för-rad jämförelse
- Automatisk beräkning av besparing/mån och /år
- PDF-generering med ett klick
- Statusspårning (Utkast → Skickad → Accepterad/Avvisad)

### 🔄 Pipeline (Kanban)
- Visuell vy över alla kunder per steg
- Snabba "flytta till nästa steg"-knappar
- Manuell statusändring
- Win rate-statistik

### 📈 Rapporter
- Stapeldiagram: pipeline-fördelning
- Cirkeldiagram: lead-källfördelning
- Säljartabell med vunna/förlorade/win rate
- Export till Excel

### ⚙️ Inställningar (Admin)
- Skapa och hantera användare
- Roller: Admin / Säljare
- Byta lösenord

---

## Filstruktur

```
crm/
├── app.py                  ← Startpunkt
├── crm.db                  ← SQLite-databas (skapas automatiskt)
├── requirements.txt
├── HOW_TO_RUN.md
├── pages/
│   ├── dashboard.py
│   ├── customers.py
│   ├── quotes.py
│   ├── pipeline.py
│   ├── reports.py
│   └── settings.py
└── utils/
    ├── database.py         ← All databaslogik
    ├── pdf_generator.py    ← PDF-offertgenerering
    └── ui_helpers.py       ← Gemensamma UI-komponenter
```

---

## Uppgradera till Supabase/PostgreSQL

Byt ut `DB_PATH` och `sqlite3` i `utils/database.py` mot:
```python
import psycopg2
conn = psycopg2.connect(os.environ["DATABASE_URL"])
```

Sätt miljövariabeln:
```bash
export DATABASE_URL="postgresql://user:password@host/dbname"
```

---

## Tips för säljteamet

1. **Börja alltid i Dashboard** — se vad som behöver uppföljning
2. **Logga varje samtal** — klicka "Logga aktivitet" i kundkortet
3. **Offerter skapas på < 2 minuter** — välj kund, fyll i priser, ladda ned PDF
4. **Pipeline = din säljtratt** — håll den uppdaterad varje dag
