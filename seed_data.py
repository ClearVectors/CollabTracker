from datetime import datetime, timedelta
import random
import sys
from app import app, db
from models import Company, Collaboration
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

# Sample data
companies_data = [
    {
        "name": "Google",
        "industry": "Tech",
        "contact_email": "partnerships@google.com",
        "contact_phone": "+1 (650) 253-0000",
        "logo_url": "/static/img/default_company.svg"
    },
    {
        "name": "Microsoft",
        "industry": "Tech",
        "contact_email": "enterprise@microsoft.com",
        "contact_phone": "+1 (425) 882-8080",
        "logo_url": "/static/img/default_company.svg"
    },
    # Add other companies back...
]

collaboration_titles = [
    "AI Research Partnership",
    "Cloud Infrastructure Integration",
    "Data Analytics Platform Development",
    "Quantum Computing Research",
    "Sustainability Initiative",
    "Smart Cities Project",
    "Blockchain Development",
    "5G Network Implementation",
    "Cybersecurity Framework",
    "Edge Computing Solutions",
    "Digital Transformation Program",
    "IoT Platform Development",
    "Machine Learning Research",
    "AR/VR Technology Partnership",
    "Green Energy Innovation"
]

def verify_database_connection():
    try:
        # Use SQLAlchemy text() construct for raw SQL
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        print(f"Database connection error: {e}")
        return False

def random_date(start_date, end_date):
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

def seed_database():
    if not verify_database_connection():
        print("Failed to connect to database. Aborting.")
        sys.exit(1)

    try:
        # Clear existing data
        print("Clearing existing data...")
        Collaboration.query.delete()
        Company.query.delete()
        db.session.commit()
        
        # Add companies
        print("Adding companies...")
        companies = []
        for company_data in companies_data:
            company = Company()
            for key, value in company_data.items():
                setattr(company, key, value)
            db.session.add(company)
            companies.append(company)
        
        db.session.commit()
        print(f"Successfully added {len(companies)} companies")
        
        # Verify companies were added
        company_count = Company.query.count()
        if company_count != len(companies):
            raise Exception(f"Company count mismatch. Expected: {len(companies)}, Got: {company_count}")
        
        # Add collaborations
        print("Adding collaborations...")
        statuses = ["Active", "Completed", "On Hold"]
        start_date = datetime(2022, 10, 26)
        end_date = datetime(2024, 10, 26)
        
        collaboration_count = 0
        for company in companies:
            num_collaborations = random.randint(2, 3)
            used_titles = set()
            
            for _ in range(num_collaborations):
                available_titles = [t for t in collaboration_titles if t not in used_titles]
                title = random.choice(available_titles)
                used_titles.add(title)
                
                status = random.choice(statuses)
                start = random_date(start_date, end_date)
                
                collab = Collaboration()
                collab.company_id = company.id
                collab.title = title
                collab.status = status
                collab.start_date = start
                collab.end_date = start + timedelta(days=random.randint(90, 365)) if status == "Completed" else None
                collab.description = f"Strategic partnership with {company.name} focusing on {title.lower()}."
                collab.kpi_revenue = random.randint(100, 1000) * 10000
                collab.kpi_satisfaction = random.randint(7, 10)
                
                db.session.add(collab)
                collaboration_count += 1
        
        db.session.commit()
        
        # Verify collaborations were added
        actual_collab_count = Collaboration.query.count()
        if actual_collab_count != collaboration_count:
            raise Exception(f"Collaboration count mismatch. Expected: {collaboration_count}, Got: {actual_collab_count}")
        
        print(f"Successfully added {collaboration_count} collaborations")
        print("\nVerification Summary:")
        print(f"Companies: {Company.query.count()}")
        print(f"Collaborations: {Collaboration.query.count()}")
        print("All data has been successfully persisted!")
        
    except SQLAlchemyError as e:
        print(f"Database error occurred: {e}")
        db.session.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {e}")
        db.session.rollback()
        sys.exit(1)

if __name__ == "__main__":
    with app.app_context():
        seed_database()
