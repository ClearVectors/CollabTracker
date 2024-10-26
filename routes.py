from flask import render_template, request, jsonify, redirect, url_for
from app import app, db
from models import Company, Collaboration, Opportunity
from datetime import datetime
from sqlalchemy import or_

@app.route('/')
def dashboard():
    companies = Company.query.all()
    active_collaborations = Collaboration.query.filter_by(status='Active').all()
    opportunities = Opportunity.query.order_by(Opportunity.probability.desc()).limit(5).all()
    return render_template('dashboard.html', 
                         companies=companies, 
                         collaborations=active_collaborations,
                         opportunities=opportunities)

@app.route('/company/new', methods=['GET', 'POST'])
def new_company():
    if request.method == 'POST':
        company = Company(
            name=request.form['name'],
            industry=request.form['industry'],
            contact_email=request.form['contact_email'],
            contact_phone=request.form['contact_phone'],
        )
        db.session.add(company)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('company_form.html')

@app.route('/company/<int:id>')
def company_detail(id):
    company = Company.query.get_or_404(id)
    return render_template('company_detail.html', company=company)

@app.route('/collaboration/new', methods=['POST'])
def new_collaboration():
    try:
        collab = Collaboration(
            company_id=request.form['company_id'],
            title=request.form['title'],
            status=request.form['status'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d'),
            description=request.form['description'],
            kpi_revenue=float(request.form['kpi_revenue']),
            kpi_satisfaction=int(request.form['kpi_satisfaction'])
        )
        db.session.add(collab)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/opportunity/new', methods=['POST'])
def new_opportunity():
    try:
        opportunity = Opportunity(
            company_id=request.form['company_id'],
            title=request.form['title'],
            stage=request.form['stage'],
            expected_revenue=float(request.form['expected_revenue']),
            probability=int(request.form['probability']),
            next_meeting_date=datetime.strptime(request.form['next_meeting_date'], '%Y-%m-%d') if request.form['next_meeting_date'] else None,
            notes=request.form['notes']
        )
        db.session.add(opportunity)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/opportunity/<int:id>/update', methods=['POST'])
def update_opportunity(id):
    try:
        opportunity = Opportunity.query.get_or_404(id)
        opportunity.stage = request.form['stage']
        opportunity.probability = int(request.form['probability'])
        opportunity.next_meeting_date = datetime.strptime(request.form['next_meeting_date'], '%Y-%m-%d') if request.form['next_meeting_date'] else None
        opportunity.notes = request.form['notes']
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/pipeline')
def pipeline():
    opportunities = Opportunity.query.order_by(Opportunity.stage, Opportunity.probability.desc()).all()
    return render_template('pipeline.html', opportunities=opportunities)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    companies = Company.query.filter(
        or_(
            Company.name.ilike(f'%{query}%'),
            Company.industry.ilike(f'%{query}%')
        )
    ).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'industry': c.industry
    } for c in companies])
