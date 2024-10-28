from flask import render_template, request, jsonify, redirect, url_for, send_from_directory, flash, Response
from werkzeug.utils import secure_filename
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

def init_routes(app, db, socketio):
    def allowed_file(filename):
        ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/company/new', methods=['POST'])
    def new_company():
        try:
            company = Company()
            company.name = request.form['name']
            company.industry = request.form['industry']
            company.contact_email = request.form['contact_email']
            company.contact_phone = request.form['contact_phone']
            company.logo_url = '/static/img/default_company.svg'
            
            db.session.add(company)
            db.session.commit()
            
            socketio.emit('company_added', {
                'id': company.id,
                'name': company.name,
                'industry': company.industry
            })
            flash('Company added successfully!', 'success')
            return redirect(url_for('company_detail', id=company.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding company: {str(e)}', 'error')
            return redirect(url_for('dashboard'))

    @app.route('/')
    @app.route('/dashboard')
    def dashboard():
        try:
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

    @app.route('/company/<int:id>')
    def company_detail(id):
        try:
            company = Company.query.get_or_404(id)
            return render_template('company_detail.html', company=company)
        except Exception as e:
            db.session.rollback()
            flash(f'Error loading company details: {str(e)}', 'error')
            return redirect(url_for('dashboard'))

    @app.route('/pipeline')
    def pipeline():
        try:
            opportunities = Opportunity.query.all()
            companies = Company.query.all()
            return render_template('pipeline.html', opportunities=opportunities, companies=companies)
        except Exception as e:
            db.session.rollback()
            flash(f'Error loading pipeline: {str(e)}', 'error')
            return render_template('pipeline.html', opportunities=[], companies=[])

    @app.route('/analytics')
    def analytics_dashboard():
        return render_template('analytics.html')

    @app.route('/advanced-search')
    def advanced_search_page():
        try:
            companies = Company.query.all()
            return render_template('advanced_search.html', companies=companies)
        except Exception as e:
            db.session.rollback()
            flash(f'Error loading advanced search: {str(e)}', 'error')
            return render_template('advanced_search.html', companies=[])

    @app.route('/export/all')
    def export_all():
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Export companies
                companies = Company.query.all()
                companies_data = [{
                    'name': company.name,
                    'industry': company.industry,
                    'contact_email': company.contact_email,
                    'contact_phone': company.contact_phone
                } for company in companies]
                pd.DataFrame(companies_data).to_excel(writer, sheet_name='Companies', index=False)
                
                # Export collaborations
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
                
                # Export opportunities
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
            return jsonify({'error': f'Failed to export data: {str(e)}'}), 500

    @app.route('/export/companies')
    def export_companies():
        try:
            output = BytesIO()
            companies = Company.query.all()
            companies_data = [{
                'name': company.name,
                'industry': company.industry,
                'contact_email': company.contact_email,
                'contact_phone': company.contact_phone
            } for company in companies]
            df = pd.DataFrame(companies_data)
            df.to_excel(output, index=False)
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
            df = pd.DataFrame(collaborations_data)
            df.to_excel(output, index=False)
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
            opportunities = Opportunity.query.all()
            opportunities_data = [{
                'title': opp.title,
                'company_name': opp.company.name,
                'stage': opp.stage,
                'expected_revenue': opp.expected_revenue,
                'probability': opp.probability,
                'next_meeting_date': opp.next_meeting_date.strftime('%Y-%m-%d') if opp.next_meeting_date else ''
            } for opp in opportunities]
            df = pd.DataFrame(opportunities_data)
            df.to_excel(output, index=False)
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': 'attachment; filename=opportunities.xlsx'}
            )
        except Exception as e:
            return jsonify({'error': f'Failed to export opportunities: {str(e)}'}), 500

    return app
