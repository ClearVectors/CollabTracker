from datetime import datetime, timedelta
import random
from app import app, db
from models import Company, Opportunity

# Opportunity types with detailed descriptions
OPPORTUNITY_TYPES = [
    {
        "type": "Product Integration",
        "descriptions": [
            "Integration of {company} products with our platform",
            "Joint product development with {company} for enterprise solutions",
            "API integration partnership with {company}"
        ]
    },
    {
        "type": "Joint Research",
        "descriptions": [
            "Collaborative research project with {company} on AI/ML",
            "R&D partnership with {company} for next-gen technologies",
            "Innovation lab partnership with {company}"
        ]
    },
    {
        "type": "Market Expansion",
        "descriptions": [
            "Strategic market expansion with {company} in APAC region",
            "Joint market entry initiative with {company}",
            "Channel partnership with {company} for new markets"
        ]
    },
    {
        "type": "Technology Partnership",
        "descriptions": [
            "Cloud infrastructure partnership with {company}",
            "Technology stack modernization with {company}",
            "Digital transformation initiative with {company}"
        ]
    },
    {
        "type": "Data Sharing Initiative",
        "descriptions": [
            "Data exchange program with {company} for ML training",
            "Collaborative data analytics with {company}",
            "Joint data platform development with {company}"
        ]
    }
]

# Stage probabilities
STAGE_PROBABILITIES = {
    "Lead": (10, 30),
    "Meeting": (20, 40),
    "Proposal": (40, 60),
    "Negotiation": (60, 80),
    "Closed": (100, 100)
}

def generate_next_meeting_date():
    """Generate a random date within the next 3 months"""
    today = datetime.now()
    days_ahead = random.randint(1, 90)  # Up to 3 months ahead
    return today + timedelta(days=days_ahead)

def get_random_opportunity_type():
    """Get a random opportunity type and description"""
    opportunity = random.choice(OPPORTUNITY_TYPES)
    return opportunity["type"], random.choice(opportunity["descriptions"])

def seed_opportunities():
    # Clear existing opportunities
    Opportunity.query.delete()
    db.session.commit()

    companies = Company.query.all()
    stages = list(STAGE_PROBABILITIES.keys())
    opportunities_per_stage = {stage: 0 for stage in stages}

    for company in companies:
        # Generate 2-3 opportunities per company
        num_opportunities = random.randint(2, 3)
        used_types = set()

        for _ in range(num_opportunities):
            # Select stage with the least opportunities for even distribution
            available_stages = [s for s in stages if opportunities_per_stage[s] < 6]
            if not available_stages:
                available_stages = stages
            stage = min(available_stages, key=lambda s: opportunities_per_stage[s])
            opportunities_per_stage[stage] += 1

            # Select unique opportunity type for this company
            while True:
                opp_type, description = get_random_opportunity_type()
                if opp_type not in used_types:
                    used_types.add(opp_type)
                    break

            # Generate probability based on stage
            min_prob, max_prob = STAGE_PROBABILITIES[stage]
            probability = random.randint(min_prob, max_prob)

            # Generate expected revenue ($500K to $10M)
            expected_revenue = random.randint(500, 10000) * 1000

            # Create opportunity
            opportunity = Opportunity()
            opportunity.company_id = company.id
            opportunity.title = f"{opp_type} with {company.name}"
            opportunity.stage = stage
            opportunity.expected_revenue = expected_revenue
            opportunity.probability = probability
            opportunity.next_meeting_date = generate_next_meeting_date() if stage != "Closed" else None
            opportunity.notes = description.format(company=company.name)

            db.session.add(opportunity)

    db.session.commit()
    print("Sample opportunity data has been added successfully!")
    print("\nOpportunities per stage:")
    for stage, count in opportunities_per_stage.items():
        print(f"{stage}: {count}")

if __name__ == "__main__":
    with app.app_context():
        seed_opportunities()
