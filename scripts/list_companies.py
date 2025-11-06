from app import create_app
from app.models import Company

app = create_app()

with app.app_context():
    companies = Company.query.all()
    print("\nCurrent companies in Supabase:")
    for company in companies:
        print(f"- {company.name} ({company.email})")