import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from sqlalchemy import or_, func

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure app using environment variables
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key_fortune100"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

with app.app_context():
    import models
    db.create_all()

@app.route('/')
def dashboard():
    companies = models.Company.query.all()
    active_collaborations = models.Collaboration.query.filter_by(status='Active').all()
    opportunities = models.Opportunity.query.order_by(models.Opportunity.probability.desc()).limit(5).all()
    return render_template('dashboard.html', 
                         companies=companies, 
                         collaborations=active_collaborations,
                         opportunities=opportunities)

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
