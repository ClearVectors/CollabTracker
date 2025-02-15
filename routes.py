from flask import render_template, request, jsonify, redirect, url_for, send_from_directory, flash, Response
from werkzeug.utils import secure_filename
from app import app, db, socketio
from models import Company, Collaboration, Opportunity, Document
from datetime import datetime
from sqlalchemy import or_, func, text
import os
import magic
import csv
import io
from contextlib import closing

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_csv(rows, fieldnames):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()

@app.route('/')
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

@app.route('/company/new', methods=['GET', 'POST'])
def new_company():
    if request.method == 'POST':
        try:
            with db.session.begin():
                company = Company(
                    name=request.form['name'],
                    industry=request.form['industry'],
                    contact_email=request.form['contact_email'],
                    contact_phone=request.form['contact_phone'],
                )
                db.session.add(company)
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating company: {str(e)}', 'error')
            return redirect(url_for('dashboard'))
    return render_template('company_form.html')

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

@app.route('/collaboration/new', methods=['POST'])
def new_collaboration():
    try:
        with db.session.begin():
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
            db.session.flush()
            
            socketio.emit('collaboration_updated', {
                'action': 'new',
                'collaboration': {
                    'id': collab.id,
                    'title': collab.title,
                    'company_name': Company.query.get(collab.company_id).name,
                    'status': collab.status,
                    'kpi_satisfaction': collab.kpi_satisfaction
                }
            })
            
            return jsonify({'success': True, 'collaboration_id': collab.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/opportunity/new', methods=['POST'])
def new_opportunity():
    try:
        with db.session.begin():
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
            db.session.flush()
            
            socketio.emit('opportunity_updated', {
                'action': 'new',
                'opportunity': {
                    'id': opportunity.id,
                    'title': opportunity.title,
                    'company_name': Company.query.get(opportunity.company_id).name,
                    'stage': opportunity.stage,
                    'probability': opportunity.probability,
                    'expected_revenue': opportunity.expected_revenue
                }
            })
            
            return jsonify({'success': True, 'opportunity_id': opportunity.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/opportunity/<int:id>/update', methods=['POST'])
def update_opportunity(id):
    try:
        with db.session.begin():
            opportunity = Opportunity.query.get_or_404(id)
            opportunity.stage = request.form['stage']
            opportunity.probability = int(request.form['probability'])
            opportunity.next_meeting_date = datetime.strptime(request.form['next_meeting_date'], '%Y-%m-%d') if request.form['next_meeting_date'] else None
            opportunity.notes = request.form['notes']
            
            socketio.emit('opportunity_updated', {
                'action': 'update',
                'opportunity': {
                    'id': opportunity.id,
                    'title': opportunity.title,
                    'stage': opportunity.stage,
                    'probability': opportunity.probability
                }
            })
            
            return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/pipeline')
def pipeline():
    try:
        with db.session.begin():
            opportunities = Opportunity.query.order_by(Opportunity.stage, Opportunity.probability.desc()).all()
            companies = Company.query.all()
        return render_template('pipeline.html', opportunities=opportunities, companies=companies)
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading pipeline: {str(e)}', 'error')
        return render_template('pipeline.html', opportunities=[], companies=[])

@app.route('/search')
def search():
    query = request.args.get('q', '')
    try:
        with db.session.begin():
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
    except Exception as e:
        db.session.rollback()
        return jsonify([])

@app.route('/document/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'})
        
        with db.session.begin():
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            mime = magic.Magic()
            file_type = mime.from_file(file_path)
            
            document = Document(
                title=request.form.get('title', filename),
                filename=filename,
                file_type=file_type,
                company_id=request.form['company_id'],
                collaboration_id=request.form.get('collaboration_id'),
                description=request.form.get('description'),
                version=request.form.get('version', '1.0')
            )
            
            db.session.add(document)
            db.session.flush()
            return jsonify({'success': True, 'document_id': document.id})
    except Exception as e:
        db.session.rollback()
        if 'file_path' in locals():
            try:
                os.remove(file_path)
            except:
                pass
        return jsonify({'success': False, 'error': str(e)})

@app.route('/document/<int:id>/download')
def download_document(id):
    try:
        with db.session.begin():
            document = Document.query.get_or_404(id)
            return send_from_directory(app.config['UPLOAD_FOLDER'], document.filename)
    except Exception as e:
        db.session.rollback()
        flash(f'Error downloading document: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/company/<int:id>/documents')
def company_documents(id):
    try:
        with db.session.begin():
            company = Company.query.get_or_404(id)
        return render_template('documents.html', company=company)
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading company documents: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/collaboration/<int:id>/documents')
def collaboration_documents(id):
    try:
        with db.session.begin():
            collaboration = Collaboration.query.get_or_404(id)
        return render_template('documents.html', collaboration=collaboration)
    except Exception as e:
        db.session.rollback()
        flash(f'Error loading collaboration documents: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html')

@app.route('/api/analytics/revenue')
def revenue_analytics():
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
                'stage_revenue': [{
                    'stage': sr[0],
                    'weighted_revenue': float(sr[1] or 0)
                } for sr in stage_revenue],
                'collab_revenue': [{
                    'status': cr[0],
                    'total_revenue': float(cr[1] or 0)
                } for cr in collab_revenue]
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'stage_revenue': [], 'collab_revenue': []})

@app.route('/api/analytics/satisfaction')
def satisfaction_analytics():
    try:
        with db.session.begin():
            satisfaction_scores = db.session.query(
                Company.name,
                func.avg(Collaboration.kpi_satisfaction).label('avg_satisfaction')
            ).join(Collaboration).group_by(Company.name).all()
            
            return jsonify([{
                'company': score[0],
                'satisfaction': float(score[1] or 0)
            } for score in satisfaction_scores])
    except Exception as e:
        db.session.rollback()
        return jsonify([])

@app.route('/api/analytics/pipeline')
def pipeline_analytics():
    try:
        with db.session.begin():
            pipeline_stats = db.session.query(
                Opportunity.stage,
                func.count(Opportunity.id).label('count'),
                func.sum(Opportunity.expected_revenue).label('total_value')
            ).group_by(Opportunity.stage).all()
            
            return jsonify([{
                'stage': stat[0],
                'count': int(stat[1]),
                'total_value': float(stat[2] or 0)
            } for stat in pipeline_stats])
    except Exception as e:
        db.session.rollback()
        return jsonify([])

@app.route('/export/companies')
def export_companies():
    try:
        with db.session.begin():
            companies = Company.query.all()
            rows = [{
                'name': company.name,
                'industry': company.industry,
                'contact_email': company.contact_email,
                'contact_phone': company.contact_phone
            } for company in companies]

            output = generate_csv(rows, ['name', 'industry', 'contact_email', 'contact_phone'])
            
            return Response(
                output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=companies.csv'}
            )
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to export companies: {str(e)}'}), 500

@app.route('/export/collaborations')
def export_collaborations():
    try:
        with db.session.begin():
            collaborations = Collaboration.query.all()
            rows = [{
                'title': collab.title,
                'company_name': collab.company.name,
                'status': collab.status,
                'start_date': collab.start_date.strftime('%Y-%m-%d') if collab.start_date else '',
                'end_date': collab.end_date.strftime('%Y-%m-%d') if collab.end_date else '',
                'revenue': collab.kpi_revenue,
                'satisfaction': collab.kpi_satisfaction
            } for collab in collaborations]

            output = generate_csv(rows, ['title', 'company_name', 'status', 'start_date', 
                                      'end_date', 'revenue', 'satisfaction'])
            
            return Response(
                output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=collaborations.csv'}
            )
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to export collaborations: {str(e)}'}), 500

@app.route('/export/opportunities')
def export_opportunities():
    try:
        with db.session.begin():
            opportunities = Opportunity.query.all()
            rows = [{
                'title': opp.title,
                'company_name': opp.company.name,
                'stage': opp.stage,
                'expected_revenue': opp.expected_revenue,
                'probability': opp.probability,
                'next_meeting_date': opp.next_meeting_date.strftime('%Y-%m-%d') if opp.next_meeting_date else ''
            } for opp in opportunities]

            output = generate_csv(rows, ['title', 'company_name', 'stage', 'expected_revenue', 
                                      'probability', 'next_meeting_date'])
            
            return Response(
                output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=opportunities.csv'}
            )
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to export opportunities: {str(e)}'}), 500