# GroundMatch Web Application

## Extra information how to install/use the app

### Installation Requirements
- Python 3.8 or higher
- PostgreSQL
- pip

### Setup Instructions
1. Clone and setup virtual environment:
```bash
git clone https://github.com/A-D-DBS-application/web-application-2025-group-12.git
cd web-application-2025-group-12
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install and configure:
```bash
pip install -r requirements.txt
cp .env.example .env     # Update with your database settings
psql -U your_username < db/schema.sql
```

3. Run the application:
```bash
flask run
```

## Link to UI prototype
_(To be added)_

## Link to Kanban board
[Miro Board](https://miro.com/app/board/uXjVJ0CcO8w=/) ![Miro](https://img.shields.io/badge/Miro-050038?style=for-the-badge&logo=Miro&logoColor=white)

## Link to audio/video recording of feedback sessions
- Partner Meeting 1 _(To be added)_
- Sprint Review 1 _(To be added)_
- Technical Feedback Session _(To be added)_
- Final Demo Recording _(To be added)_

## Other links/info

### Development Workflow
- Branch Strategy:
  - `main` - production code
  - `development` - integration branch
  - Feature branches: `feature/name-of-feature`
  - Bugfix branches: `bugfix/name-of-bug`

### Code Guidelines
- Follow PEP 8 for Python code style
- Use meaningful variable and function names
- Add comments where needed
- Keep functions small and focused

### Database Management
- Update `db/schema.sql` for schema changes
- Communicate changes to the team
- Team members apply changes with: `psql -U username < db/schema.sql`

### Project Structure
```
flask_app/
├── app/                # Application code
│   ├── __init__.py    # App initialization
│   ├── models.py      # Database models
│   ├── routes.py      # URL routing
│   └── templates/     # HTML templates
├── data/              # Data files
├── db/                # Database scripts
├── scripts/           # Utility scripts
└── docs/              # Documentation
```

### Documentation
- User Stories: [`docs/User story.pdf`](docs/assets/User story.pdf)
- [Known Issues](https://github.com/A-D-DBS-application/web-application-2025-group-12/issues)
- API Documentation _(To be added)_

