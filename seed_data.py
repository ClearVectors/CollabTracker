from datetime import datetime, timedelta
import random
from app import app, db
from models import Company, Collaboration

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
    {
        "name": "Amazon/AWS",
        "industry": "Tech/Cloud",
        "contact_email": "aws-partnerships@amazon.com",
        "contact_phone": "+1 (206) 266-1000",
        "logo_url": "/static/img/default_company.svg"
    },
    {
        "name": "Apple",
        "industry": "Tech/Consumer Electronics",
        "contact_email": "developer-relations@apple.com",
        "contact_phone": "+1 (408) 996-1010",
        "logo_url": "/static/img/default_company.svg"
    },
    {
        "name": "Meta",
        "industry": "Social Media",
        "contact_email": "business@meta.com",
        "contact_phone": "+1 (650) 543-4800",
        "logo_url": "/static/img/default_company.svg"
    },
    {
        "name": "NVIDIA",
        "industry": "Tech/AI",
        "contact_email": "partner-relations@nvidia.com",
        "contact_phone": "+1 (408) 486-2000",
        "logo_url": "/static/img/default_company.svg"
    },
    {
        "name": "Tesla",
        "industry": "Automotive/Tech",
        "contact_email": "tech-partnerships@tesla.com",
        "contact_phone": "+1 (888) 518-3752",
        "logo_url": "/static/img/default_company.svg"
    },
    {
        "name": "Oracle",
        "industry": "Enterprise Software",
        "contact_email": "cloud-partners@oracle.com",
        "contact_phone": "+1 (650) 506-7000",
        "logo_url": "/static/img/default_company.svg"
    },
    {
        "name": "Salesforce",
        "industry": "CRM/Cloud",
        "contact_email": "partner-success@salesforce.com",
        "contact_phone": "+1 (415) 901-7000",
        "logo_url": "/static/img/default_company.svg"
    },
    {
        "name": "IBM",
        "industry": "Tech/Consulting",
        "contact_email": "global-alliances@ibm.com",
        "contact_phone": "+1 (914) 499-1900",
        "logo_url": "/static/img/default_company.svg"
    }
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

def random_date(start_date, end_date):
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

def seed_database():
    # Clear existing data
    Collaboration.query.delete()
    Company.query.delete()
    
    # Add companies
    companies = []
    for company_data in companies_data:
        company = Company()
        for key, value in company_data.items():
            setattr(company, key, value)
        db.session.add(company)
        companies.append(company)
    
    db.session.commit()
    
    # Add collaborations
    statuses = ["Active", "Completed", "On Hold"]
    start_date = datetime(2022, 10, 26)  # 2 years ago from today
    end_date = datetime(2024, 10, 26)    # today
    
    for company in companies:
        # Generate 2-3 collaborations per company
        num_collaborations = random.randint(2, 3)
        used_titles = set()
        
        for _ in range(num_collaborations):
            # Select a unique title for this company
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
            collab.kpi_revenue = random.randint(100, 1000) * 10000  # Revenue between $1M and $10M
            collab.kpi_satisfaction = random.randint(7, 10)  # High satisfaction scores
            
            db.session.add(collab)
    
    db.session.commit()
    print("Sample data has been added successfully!")

if __name__ == "__main__":
    with app.app_context():
        seed_database()
