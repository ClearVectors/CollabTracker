from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np
from models import Opportunity, Company, Collaboration
from datetime import datetime
import pandas as pd

def prepare_features(opportunities, companies):
    """Prepare features for the prediction model"""
    # Create encoders for categorical variables
    stage_encoder = LabelEncoder()
    industry_encoder = LabelEncoder()
    
    # Prepare data
    data = []
    for opp in opportunities:
        company = next((c for c in companies if c.id == opp.company_id), None)
        if company:
            # Calculate days since creation
            days_active = (datetime.utcnow() - opp.created_at).days
            
            data.append({
                'stage': opp.stage,
                'probability': opp.probability,
                'expected_revenue': opp.expected_revenue,
                'days_active': days_active,
                'industry': company.industry,
                'success': 1 if opp.stage == 'Closed' else 0
            })
    
    df = pd.DataFrame(data)
    
    # Encode categorical variables
    df['stage_encoded'] = stage_encoder.fit_transform(df['stage'])
    df['industry_encoded'] = industry_encoder.fit_transform(df['industry'])
    
    return df, stage_encoder, industry_encoder

def train_prediction_model(opportunities, companies):
    """Train a random forest model for predicting success rates"""
    df, stage_encoder, industry_encoder = prepare_features(opportunities, companies)
    
    # Prepare features and target
    X = df[['stage_encoded', 'probability', 'expected_revenue', 'days_active', 'industry_encoded']]
    y = df['success']
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model, stage_encoder, industry_encoder

def predict_success_rate(opportunity, company, model, stage_encoder, industry_encoder):
    """Predict success rate for a given opportunity"""
    days_active = (datetime.utcnow() - opportunity.created_at).days
    
    # Prepare features
    features = np.array([[
        stage_encoder.transform([opportunity.stage])[0],
        opportunity.probability,
        opportunity.expected_revenue,
        days_active,
        industry_encoder.transform([company.industry])[0]
    ]])
    
    # Get prediction probability
    success_prob = model.predict_proba(features)[0][1]
    return round(success_prob * 100, 2)

def get_predictive_analytics():
    """Get predictive analytics data for all opportunities"""
    opportunities = Opportunity.query.all()
    companies = Company.query.all()
    
    # Train model
    model, stage_encoder, industry_encoder = train_prediction_model(opportunities, companies)
    
    # Generate predictions for each opportunity
    predictions = []
    for opp in opportunities:
        company = next((c for c in companies if c.id == opp.company_id), None)
        if company and opp.stage != 'Closed':
            success_rate = predict_success_rate(opp, company, model, stage_encoder, industry_encoder)
            predictions.append({
                'id': opp.id,
                'title': opp.title,
                'company': company.name,
                'stage': opp.stage,
                'success_rate': success_rate,
                'expected_revenue': opp.expected_revenue
            })
    
    return predictions
