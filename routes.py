from flask import render_template, request, jsonify, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from app import app, db, logger
from models import Company, Collaboration, Opportunity, Document
from datetime import datetime
from sqlalchemy import or_, func, text
from sqlalchemy.exc import SQLAlchemyError
import os
import magic

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_database_error(error, operation):
    """Handle database errors and return appropriate response"""
    logger.error(f"Database error during {operation}: {str(error)}")
    return jsonify({
        'error': 'Database operation failed',
        'message': 'An error occurred while fetching data'
    }), 500

@app.route('/')
def dashboard():
    try:
        companies = Company.query.all()
        active_collaborations = Collaboration.query.filter_by(status='Active').all()
        opportunities = Opportunity.query.order_by(Opportunity.probability.desc()).limit(5).all()
        return render_template('dashboard.html', 
                             companies=companies, 
                             collaborations=active_collaborations,
                             opportunities=opportunities)
    except SQLAlchemyError as e:
        return handle_database_error(e, 'dashboard view')

@app.route('/company/new', methods=['GET', 'POST'])
def new_company():
    if request.method == 'POST':
        try:
            company = Company(
                name=request.form['name'],
                industry=request.form['industry'],
                contact_email=request.form['contact_email'],
                contact_phone=request.form['contact_phone'],
            )
            db.session.add(company)
            db.session.commit()
            return redirect(url_for('dashboard'))
        except SQLAlchemyError as e:
            return handle_database_error(e, 'company creation')
    return render_template('company_form.html')

@app.route('/company/<int:id>')
def company_detail(id):
    try:
        company = Company.query.get_or_404(id)
        return render_template('company_detail.html', company=company)
    except SQLAlchemyError as e:
        return handle_database_error(e, 'company detail view')

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
    except SQLAlchemyError as e:
        return handle_database_error(e, 'collaboration creation')

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
    except SQLAlchemyError as e:
        return handle_database_error(e, 'opportunity creation')

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
    except SQLAlchemyError as e:
        return handle_database_error(e, 'opportunity update')

@app.route('/pipeline')
def pipeline():
    try:
        opportunities = Opportunity.query.order_by(Opportunity.stage, Opportunity.probability.desc()).all()
        return render_template('pipeline.html', opportunities=opportunities)
    except SQLAlchemyError as e:
        return handle_database_error(e, 'pipeline view')

@app.route('/search')
def search():
    try:
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
    except SQLAlchemyError as e:
        return handle_database_error(e, 'company search')

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
        db.session.commit()
        
        return jsonify({'success': True, 'document_id': document.id})
    except SQLAlchemyError as e:
        return handle_database_error(e, 'document upload')

@app.route('/document/<int:id>/download')
def download_document(id):
    try:
        document = Document.query.get_or_404(id)
        return send_from_directory(app.config['UPLOAD_FOLDER'], document.filename)
    except SQLAlchemyError as e:
        return handle_database_error(e, 'document download')

@app.route('/company/<int:id>/documents')
def company_documents(id):
    try:
        company = Company.query.get_or_404(id)
        return render_template('documents.html', company=company)
    except SQLAlchemyError as e:
        return handle_database_error(e, 'company documents view')

@app.route('/collaboration/<int:id>/documents')
def collaboration_documents(id):
    try:
        collaboration = Collaboration.query.get_or_404(id)
        return render_template('documents.html', collaboration=collaboration)
    except SQLAlchemyError as e:
        return handle_database_error(e, 'collaboration documents view')

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html')

@app.route('/api/analytics/revenue')
def revenue_analytics():
    try:
        logger.info("Fetching revenue analytics data")
        
        stage_revenue = db.session.execute(
            text("""
                SELECT 
                    stage,
                    COALESCE(SUM(CASE 
                        WHEN expected_revenue IS NOT NULL AND probability IS NOT NULL 
                        THEN expected_revenue * probability / 100.0
                        ELSE 0 
                    END), 0) as weighted_revenue
                FROM opportunity
                GROUP BY stage
                ORDER BY stage
            """)
        ).fetchall()
        
        collab_revenue = db.session.execute(
            text("""
                SELECT 
                    status,
                    COALESCE(SUM(CASE 
                        WHEN kpi_revenue IS NOT NULL 
                        THEN kpi_revenue
                        ELSE 0 
                    END), 0) as total_revenue
                FROM collaboration
                GROUP BY status
                ORDER BY status
            """)
        ).fetchall()
        
        stage_revenue_data = [{
            'stage': sr[0],
            'weighted_revenue': float(sr[1] or 0)
        } for sr in stage_revenue]
        
        collab_revenue_data = [{
            'status': cr[0],
            'total_revenue': float(cr[1] or 0)
        } for cr in collab_revenue]
        
        logger.info(f"Stage revenue data: {stage_revenue_data}")
        logger.info(f"Collaboration revenue data: {collab_revenue_data}")
        
        return jsonify({
            'stage_revenue': stage_revenue_data,
            'collab_revenue': collab_revenue_data
        })
    except SQLAlchemyError as e:
        logger.error(f"Database error in revenue analytics: {str(e)}")
        return handle_database_error(e, 'revenue analytics')
    except Exception as e:
        logger.error(f"Unexpected error in revenue analytics: {str(e)}")
        return handle_database_error(e, 'revenue analytics')

@app.route('/api/analytics/satisfaction')
def satisfaction_analytics():
    try:
        logger.info("Fetching satisfaction analytics data")
        
        satisfaction_scores = db.session.execute(
            text("""
                SELECT 
                    c.name,
                    COALESCE(AVG(CASE 
                        WHEN cl.kpi_satisfaction IS NOT NULL 
                        THEN cl.kpi_satisfaction
                        ELSE NULL 
                    END), 0) as avg_satisfaction,
                    COUNT(cl.id) as collaboration_count
                FROM company c
                LEFT JOIN collaboration cl ON c.id = cl.company_id
                GROUP BY c.name
                HAVING COUNT(cl.id) > 0
                ORDER BY avg_satisfaction DESC
            """)
        ).fetchall()
        
        satisfaction_data = [{
            'company': score[0],
            'satisfaction': round(float(score[1] or 0), 2),
            'collaboration_count': int(score[2])
        } for score in satisfaction_scores]
        
        logger.info(f"Satisfaction analytics data: {satisfaction_data}")
        
        return jsonify(satisfaction_data)
    except SQLAlchemyError as e:
        logger.error(f"Database error in satisfaction analytics: {str(e)}")
        return handle_database_error(e, 'satisfaction analytics')
    except Exception as e:
        logger.error(f"Unexpected error in satisfaction analytics: {str(e)}")
        return handle_database_error(e, 'satisfaction analytics')

@app.route('/api/analytics/pipeline')
def pipeline_analytics():
    try:
        logger.info("Fetching pipeline analytics data")
        
        pipeline_stats = db.session.execute(
            text("""
                SELECT 
                    stage,
                    COUNT(*) as count,
                    COALESCE(SUM(CASE 
                        WHEN expected_revenue IS NOT NULL 
                        THEN expected_revenue
                        ELSE 0 
                    END), 0) as total_value,
                    COALESCE(AVG(probability), 0) as avg_probability
                FROM opportunity
                GROUP BY stage
                ORDER BY stage
            """)
        ).fetchall()
        
        pipeline_data = [{
            'stage': stat[0],
            'count': int(stat[1]),
            'total_value': round(float(stat[2] or 0), 2),
            'avg_probability': round(float(stat[3] or 0), 1)
        } for stat in pipeline_stats]
        
        logger.info(f"Pipeline analytics data: {pipeline_data}")
        
        return jsonify(pipeline_data)
    except SQLAlchemyError as e:
        logger.error(f"Database error in pipeline analytics: {str(e)}")
        return handle_database_error(e, 'pipeline analytics')
    except Exception as e:
        logger.error(f"Unexpected error in pipeline analytics: {str(e)}")
        return handle_database_error(e, 'pipeline analytics')

@app.errorhandler(SQLAlchemyError)
def handle_sqlalchemy_error(error):
    logger.error(f"Database error: {str(error)}")
    db.session.rollback()
    return jsonify({
        'error': 'Database error occurred',
        'message': 'Please try again later'
    }), 500

@app.errorhandler(Exception)
def handle_general_error(error):
    logger.error(f"Unexpected error: {str(error)}")
    return jsonify({
        'error': 'An unexpected error occurred',
        'message': 'Please try again later'
    }), 500