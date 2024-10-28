from flask import render_template, request, jsonify, redirect, url_for, send_from_directory, flash, Response
from werkzeug.utils import secure_filename
from app import app, db, socketio
from models import Company, Collaboration, Opportunity, Document
from datetime import datetime
from sqlalchemy import or_, func, text, and_
import os
import magic
import csv
import io
from contextlib import closing
from io import BytesIO
import pandas as pd

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/export/companies')
def export_companies():
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            companies = Company.query.all()
            companies_data = [{
                'name': company.name,
                'industry': company.industry,
                'contact_email': company.contact_email,
                'contact_phone': company.contact_phone
            } for company in companies]
            pd.DataFrame(companies_data).to_excel(writer, sheet_name='Companies', index=False)
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=companies.xlsx'}
        )
    except Exception as e:
        return jsonify({'error': f'Failed to export companies: {str(e)}'}), 500

@app.route('/export/collaborations')
def export_collaborations():
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            collaborations = Collaboration.query.all()
            collaborations_data = [{
                'title': collab.title,
                'company_name': collab.company.name,
                'status': collab.status,
                'start_date': collab.start_date.strftime('%Y-%m-%d') if collab.start_date else '',
                'end_date': collab.end_date.strftime('%Y-%m-%d') if collab.end_date else '',
                'revenue': collab.kpi_revenue,
                'satisfaction': collab.kpi_satisfaction
            } for collab in collaborations]
            pd.DataFrame(collaborations_data).to_excel(writer, sheet_name='Collaborations', index=False)
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=collaborations.xlsx'}
        )
    except Exception as e:
        return jsonify({'error': f'Failed to export collaborations: {str(e)}'}), 500

@app.route('/export/opportunities')
def export_opportunities():
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            opportunities = Opportunity.query.all()
            opportunities_data = [{
                'title': opp.title,
                'company_name': opp.company.name,
                'stage': opp.stage,
                'expected_revenue': opp.expected_revenue,
                'probability': opp.probability,
                'next_meeting_date': opp.next_meeting_date.strftime('%Y-%m-%d') if opp.next_meeting_date else ''
            } for opp in opportunities]
            pd.DataFrame(opportunities_data).to_excel(writer, sheet_name='Opportunities', index=False)
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=opportunities.xlsx'}
        )
    except Exception as e:
        return jsonify({'error': f'Failed to export opportunities: {str(e)}'}), 500

@app.route('/')
@app.route('/dashboard')
def dashboard():
    try:
        with db.session.begin():
            companies = Company.query.all()
            active_collaborations = Collaboration.query.filter_by(status='Active').all()
            opportunities = Opportunity.query.order_by(Opportunity.probability.desc()).limit(5).all()
        return render_template('dashboard.html', 
                            companies=companies, 
                            collaborations=active_collaborations,
                            opportunities=opportunities)
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', companies=[], collaborations=[], opportunities=[])

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html')

@app.route('/pipeline')
def pipeline():
    try:
        with db.session.begin():
            opportunities = Opportunity.query.all()
            companies = Company.query.all()
        return render_template('pipeline.html', opportunities=opportunities, companies=companies)
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading pipeline: {str(e)}', 'error')
        return render_template('pipeline.html', opportunities=[], companies=[])

@app.route('/advanced-search')
def advanced_search_page():
    try:
        with db.session.begin():
            companies = Company.query.all()
        return render_template('advanced_search.html', companies=companies)
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading advanced search: {str(e)}', 'error')
        return render_template('advanced_search.html', companies=[])

@app.route('/api/advanced-search')
def advanced_search():
    try:
        name_query = request.args.get('name', '').strip()
        industry = request.args.get('industry', '').strip()
        min_revenue = request.args.get('min_revenue', type=float)
        max_revenue = request.args.get('max_revenue', type=float)
        min_satisfaction = request.args.get('min_satisfaction', type=int)
        max_satisfaction = request.args.get('max_satisfaction', type=int)
        status = request.args.get('status', '').strip()
        pipeline_stage = request.args.get('pipeline_stage', '').strip()

        query = db.session.query(Company).distinct()

        if name_query:
            query = query.filter(Company.name.ilike(f'%{name_query}%'))
        
        if industry:
            query = query.filter(Company.industry.ilike(f'%{industry}%'))

        if status:
            query = query.join(Collaboration).filter(Collaboration.status == status)

        if pipeline_stage:
            query = query.join(Opportunity).filter(Opportunity.stage == pipeline_stage)

        if min_revenue is not None or max_revenue is not None:
            query = query.join(Collaboration)
            if min_revenue is not None:
                query = query.filter(Collaboration.kpi_revenue >= min_revenue)
            if max_revenue is not None:
                query = query.filter(Collaboration.kpi_revenue <= max_revenue)

        if min_satisfaction is not None or max_satisfaction is not None:
            query = query.join(Collaboration)
            if min_satisfaction is not None:
                query = query.filter(Collaboration.kpi_satisfaction >= min_satisfaction)
            if max_satisfaction is not None:
                query = query.filter(Collaboration.kpi_satisfaction <= max_satisfaction)

        companies = query.all()
        results = []
        
        for company in companies:
            latest_collab = (Collaboration.query
                           .filter_by(company_id=company.id)
                           .order_by(Collaboration.start_date.desc())
                           .first())
            
            latest_opp = (Opportunity.query
                         .filter_by(company_id=company.id)
                         .order_by(Opportunity.updated_at.desc())
                         .first())

            result = {
                'id': company.id,
                'name': company.name,
                'industry': company.industry,
                'contact_email': company.contact_email,
                'latest_collaboration': {
                    'title': latest_collab.title if latest_collab else None,
                    'status': latest_collab.status if latest_collab else None,
                    'satisfaction': latest_collab.kpi_satisfaction if latest_collab else None,
                    'revenue': latest_collab.kpi_revenue if latest_collab else None
                } if latest_collab else None,
                'latest_opportunity': {
                    'title': latest_opp.title if latest_opp else None,
                    'stage': latest_opp.stage if latest_opp else None,
                    'probability': latest_opp.probability if latest_opp else None
                } if latest_opp else None
            }
            results.append(result)

        return jsonify(results)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/company/<int:id>')
def company_detail(id):
    try:
        with db.session.begin():
            company = Company.query.get_or_404(id)
        return render_template('company_detail.html', company=company)
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading company details: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/export/all')
def export_all():
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            companies = Company.query.all()
            companies_data = [{
                'name': company.name,
                'industry': company.industry,
                'contact_email': company.contact_email,
                'contact_phone': company.contact_phone
            } for company in companies]
            pd.DataFrame(companies_data).to_excel(writer, sheet_name='Companies', index=False)
            
            collaborations = Collaboration.query.all()
            collaborations_data = [{
                'title': collab.title,
                'company_name': collab.company.name,
                'status': collab.status,
                'start_date': collab.start_date.strftime('%Y-%m-%d') if collab.start_date else '',
                'end_date': collab.end_date.strftime('%Y-%m-%d') if collab.end_date else '',
                'revenue': collab.kpi_revenue,
                'satisfaction': collab.kpi_satisfaction
            } for collab in collaborations]
            pd.DataFrame(collaborations_data).to_excel(writer, sheet_name='Collaborations', index=False)
            
            opportunities = Opportunity.query.all()
            opportunities_data = [{
                'title': opp.title,
                'company_name': opp.company.name,
                'stage': opp.stage,
                'expected_revenue': opp.expected_revenue,
                'probability': opp.probability,
                'next_meeting_date': opp.next_meeting_date.strftime('%Y-%m-%d') if opp.next_meeting_date else ''
            } for opp in opportunities]
            pd.DataFrame(opportunities_data).to_excel(writer, sheet_name='Opportunities', index=False)

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=fortune100_data.xlsx'}
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to export data: {str(e)}'}), 500

@app.route('/api/analytics/revenue')
def get_revenue_analytics():
    try:
        with db.session.begin():
            stage_revenue = db.session.query(
                Opportunity.stage,
                func.sum(Opportunity.expected_revenue * Opportunity.probability / 100).label('weighted_revenue')
            ).group_by(Opportunity.stage).all()
            
            collab_revenue = db.session.query(
                Collaboration.status,
                func.sum(Collaboration.kpi_revenue).label('total_revenue')
            ).group_by(Collaboration.status).all()
            
            return jsonify({
                'stage_revenue': [{'stage': s[0], 'weighted_revenue': float(s[1] or 0)} for s in stage_revenue],
                'collab_revenue': [{'status': s[0], 'total_revenue': float(s[1] or 0)} for s in collab_revenue]
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/satisfaction')
def get_satisfaction_analytics():
    try:
        with db.session.begin():
            satisfaction_data = db.session.query(
                Company.name,
                func.avg(Collaboration.kpi_satisfaction).label('satisfaction')
            ).join(Collaboration).group_by(Company.name).all()
            
            return jsonify([
                {'company': s[0], 'satisfaction': float(s[1] or 0)}
                for s in satisfaction_data
            ])
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/pipeline')
def get_pipeline_analytics():
    try:
        with db.session.begin():
            pipeline_data = db.session.query(
                Opportunity.stage,
                func.count().label('count'),
                func.sum(Opportunity.expected_revenue).label('total_value')
            ).group_by(Opportunity.stage).all()
            
            return jsonify([
                {
                    'stage': p[0],
                    'count': int(p[1]),
                    'total_value': float(p[2] if p[2] is not None else 0)
                }
                for p in pipeline_data
            ])
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
