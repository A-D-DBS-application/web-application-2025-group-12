# 🏗️ GroundMatch - Building Plot Matching Platform

Intelligent matching system connecting construction companies with their clients' ideal building plots using a 3-score algorithm.

## � Over GroundMatch

### Inleiding
GroundMatch ondersteunt bouwbedrijven bij het efficiënt beheren, selecteren en opvolgen van geschikte bouwgronden voor hun klanten. Dankzij automatische data-scraping en een intelligent matchalgoritme beschikt uw bedrijf altijd over een actueel overzicht van beschikbare gronden, inclusief een berekende matchscore per klant. Dit bespaart tijd, verhoogt de nauwkeurigheid en vereenvoudigt de interne besluitvorming. U behoudt de volledige controle: u beslist welke gronden aan welke klant worden voorgesteld, en u ontvangt onmiddellijk meldingen zodra nieuwe relevante bouwgronden beschikbaar komen. Klanten zien enkel de door u geselecteerde top 10 grondmatches en kunnen eenvoudig hun voorkeuren aanpassen, waardoor u sneller en gerichter kunt inspelen op hun behoeften. GroundMatch is een duidelijke meerwaarde voor elk bouwbedrijf dat efficiëntie en service wil verhogen.

### Wat u kunt doen als bouwbedrijf:
- Registreren en inloggen om toegang te krijgen tot uw bedrijfsdashboard
- Klanten beheren: klanten toevoegen, gegevens bekijken en hun voorkeuren opvolgen
- Gronden beheren:
  - Eigen gronden toevoegen
  - Externe gescrapete gronden raadplegen
  - Gronden filteren op m², prijs, locatie, etc.
- Meldingen ontvangen wanneer een nieuwe grond beschikbaar komt
- Matchscores bekijken tussen klantvoorkeuren en beschikbare gronden
- Matches accepteren of afwijzen om te bepalen of de grond zichtbaar wordt voor de klant
- Top 10 matches instellen: u beslist welke gronden de klant te zien krijgt
- Voorkeuren van klanten opvolgen en nieuwe matches activeren wanneer een klant iets wijzigt
- Steeds een actueel overzicht koesteren, dankzij scraping + meldingen + algoritme

### Wat uw klant kan doen:
- Inloggen via de speciale client-login (geen registratie nodig)
- Zijn persoonlijke dashboard bekijken met uitsluitend matchscores
- Top 10 beste matches bekijken die door uw bouwbedrijf geselecteerd zijn
- Matchdetails bekijken: locatie, prijs, oppervlakte, foto's, total_score
- Voorkeuren aanpassen (budget, m², locatie, subdivision type, etc.)
- Automatische updates ontvangen: gewijzigde voorkeuren worden meteen doorgestuurd naar het bedrijf
- Een gefilterd en volledig gepersonaliseerd aanbod zien van de 10 best passende gronden

## �🚀 Quick Start

### Prerequisites
- Python 3.12+
- Supabase account (PostgreSQL database)

### Installation
```bash
# 1. Clone repository
git clone https://github.com/A-D-DBS-application/web-application-2025-group-12.git
cd web-application-2025-group-12

# 2. Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database
cp .env.example .env
# Edit .env with your Supabase DATABASE_URL

# 5. Initialize database
python scripts/reset_database.py

# 6. Run application
python run.py
# Visit: http://127.0.0.1:5000
```

## ✨ Features

### For Companies (Brokers)
- 👥 **Client Management** - Add, edit, delete clients with search
- 🏗️ **Ground Inventory** - Manage building plots with filtering
- ⚙️ **Preference Settings** - Configure client requirements
- 🎯 **Smart Matching** - AI-powered 3-score algorithm (Budget + Size + Location)
- 📊 **Match Dashboard** - View and update match status
- 🌐 **Web Scraper** - Automatically import new plots

### For Clients
- 🔍 **View Preferences** - See your configured requirements
- 📋 **Browse Matches** - View compatible plots sorted by score (0-300)
- ✅ **Match Status** - Track pending/accepted/rejected status

## 📁 Project Structure

```
web-application-2025-group-12/
├── app/                    # Flask application
│   ├── __init__.py        # App factory
│   ├── config.py          # Database config
│   ├── models.py          # SQLAlchemy models (5 tables)
│   ├── routes.py          # All routes (25+ endpoints)
│   ├── matching.py        # 3-score algorithm
│   ├── templates/         # HTML templates (16 files)
│   └── static/            # CSS/JS (currently empty, uses inline styles)
├── db/
│   ├── schema.sql         # Database schema
│   └── dumps/             # Database backups
├── docs/                  # Project documentation
│   ├── ERD.png           # Entity Relationship Diagram
│   ├── User story.pdf    # User stories
│   └── Logo              # Project logo
├── scripts/               # Utility scripts
│   ├── reset_database.py # Database initialization
│   └── check_db_schema.py # Schema verification
├── scraper.py            # Web scraper for grounds
├── run.py                # Application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🗄️ Database Schema

5 core tables in PostgreSQL (Supabase):
- **Company** - Construction companies/brokers
- **Client** - Company clients seeking land
- **Ground** - Available building plots
- **Preferences** - Client requirements (1-to-1 with Client)
- **Match** - Ground-to-Preference matches (many-to-many)

## 🎯 Matching Algorithm

3-score system (each 0-100, total 0-300):
1. **Budget Score** - How well ground price fits budget range
2. **Size Score** - How well m² matches size requirements  
3. **Location Score** - Location string matching (exact/partial/none)

Higher total scores = better matches (displayed first)

## 🔗 Project Links

- **Kanban Board**: [Miro Board](https://miro.com/app/board/uXjVJ0CcO8w=/)
- **User Stories**: See `docs/User story.pdf`
- **Database ERD**: See `docs/ERD.png`

## 🛠️ Development Commands

```bash
# Database management
python scripts/reset_database.py    # Initialize/reset database
python scripts/check_db_schema.py  # Verify schema

# Run application
python run.py                       # Start Flask server (port 5000)

# Code quality (optional)
pytest                              # Run tests
flake8 app/                        # Lint code
black app/                         # Format code
```

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Database connection error | Check `.env` DATABASE_URL, run `python scripts/check_db_schema.py` |
| Port 5000 already in use | Run `lsof -ti:5000 \| xargs kill -9` |
| Module not found | Run `pip install -r requirements.txt` |
| Import errors | Activate venv: `source .venv/bin/activate` |

## 👥 Contributors

Database Systems Course - Group 12 - 2025

## 📄 License

University course assignment

