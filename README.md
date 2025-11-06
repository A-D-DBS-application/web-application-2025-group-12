[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DxqGQVx4)

# Flask Applicatie - Groepswerk

## 🚀 Aan de slag

### Vereisten
- Python 3.8 of hoger
- PostgreSQL
- pip

### Lokale ontwikkelomgeving opzetten

1. Clone de repository
```bash
git clone https://github.com/A-D-DBS-application/web-application-2025-group-12.git
cd web-application-2025-group-12
```

2. Maak een virtual environment aan
```bash
python -m venv venv
source venv/bin/activate  # Op Windows gebruik: venv\Scripts\activate
```

3. Installeer dependencies
```bash
pip install -r requirements.txt
```

4. Configureer je lokale omgeving
```bash
cp .env.example .env
# Pas de waardes in .env aan met je lokale database gegevens
```

5. Initialiseer de database
```bash
psql -U je_gebruikersnaam < db/schema.sql
```

6. Start de development server
```bash
flask run
```

## 📝 Workflow voor teamleden

### Branch Strategie
- `main` - productie code
- `development` - integratie branch
- Feature branches: `feature/naam-van-feature`
- Bugfix branches: `bugfix/naam-van-bug`

### Voordat je begint met ontwikkelen
1. Pull de laatste wijzigingen
```bash
git pull origin main
```

2. Maak een nieuwe branch
```bash
git checkout -b feature/jouw-feature
```

3. Commit regelmatig
```bash
git add .
git commit -m "Beschrijvende commit message"
```

4. Push je wijzigingen
```bash
git push origin feature/jouw-feature
```

5. Maak een Pull Request aan op GitHub

### Code Conventies
- Volg PEP 8 voor Python code-stijl
- Gebruik betekenisvolle variabele- en functienamen
- Voeg commentaar toe waar nodig
- Houd functies klein en gefocust

## 🔄 Database Updates
Als je schema wijzigingen hebt:
1. Update `db/schema.sql`
2. Communiceer de wijzigingen met het team
3. Team members moeten de nieuwe schema toepassen:
```bash
psql -U je_gebruikersnaam < db/schema.sql
```

## 🐛 Bekende Issues
- Check de GitHub Issues tab voor bekende problemen
- Maak nieuwe issues aan voor bugs die je tegenkomt

## 📚 Projectstructuur
```
flask_app/
├── app/                # Applicatie code
│   ├── __init__.py    # App initialisatie
│   ├── models.py      # Database models
│   ├── routes.py      # URL routing
│   └── templates/     # HTML templates
├── data/              # Data bestanden
├── db/                # Database scripts
├── scripts/           # Utility scripts
└── docs/              # Project documentation (user stories, specs)
```

## 📄 User Stories & Requirements

De finale versie van de user stories staat in [`docs/User story.pdf`](docs/assets/User story.pdf). Dit document bevat:
- Alle user stories en acceptatiecriteria
- Functionele requirements
- Non-functionele requirements
- Technische requirements

## 📎 Project Resources & Links

### Extra Installatie & Gebruik
- [Extra installatie-instructies] _(nog toe te voegen)_
- [Gebruikershandleiding] _(nog toe te voegen)_

### Design & Planning
- [UI Prototype] _(nog toe te voegen)_
- [Kanban Board] _(nog toe te voegen)_

### Feedback & Documentation
- [Feedback Sessie Opnames] _(nog toe te voegen)_
- [Partner Meetings] _(nog toe te voegen)_

### Extra Resources
- [API Documentation] _(nog toe te voegen)_
- [Database Schema] _(nog toe te voegen)_
```