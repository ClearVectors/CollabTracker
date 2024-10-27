from flask import render_template, request, jsonify, redirect, url_for, send_from_directory, flash, send_file, Response
from werkzeug.utils import secure_filename
from app import app, db
from models import Company, Collaboration, Opportunity, Document
from datetime import datetime
from sqlalchemy import or_, func, exc
import os
import openpyxl
from openpyxl.styles import Font, PatternFill
from io import BytesIO
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in dashboard: {str(e)}")
        return "Database error occurred", 500

@app.route('/export/data')
def export_data():
    excel_data = None
    try:
        # Verify database connection
        try:
            db.session.execute('SELECT 1')
        except exc.SQLAlchemyError as e:
            logger.error(f"Database connection error: {str(e)}")
            return jsonify({'error': 'Database connection failed'}), 500

        # Create workbook and styles
        wb = openpyxl.Workbook()
        header_style = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")

        # Companies Sheet
        try:
            ws_companies = wb.active
            ws_companies.title = "Companies"
            headers = ["Company ID", "Name", "Industry", "Contact Email", "Contact Phone"]
            ws_companies.append(headers)
            
            for cell in ws_companies[1]:
                cell.font = header_style
                cell.fill = header_fill

            companies = Company.query.all()
            if not companies:
                logger.warning("No companies found in database")
            
            for company in companies:
                ws_companies.append([
                    company.id,
                    company.name,
                    company.industry,
                    company.contact_email,
                    company.contact_phone
                ])
        except exc.SQLAlchemyError as e:
            logger.error(f"Error querying companies: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing companies data: {str(e)}")
            raise

        # Collaborations Sheet
        try:
            ws_collabs = wb.create_sheet("Collaborations")
            headers = ["Collaboration ID", "Company", "Title", "Status", "Start Date", "End Date", "Revenue", "Satisfaction"]
            ws_collabs.append(headers)
            
            for cell in ws_collabs[1]:
                cell.font = header_style
                cell.fill = header_fill

            collaborations = Collaboration.query.all()
            if not collaborations:
                logger.warning("No collaborations found in database")
            
            for collab in collaborations:
                ws_collabs.append([
                    collab.id,
                    collab.company.name,
                    collab.title,
                    collab.status,
                    collab.start_date.strftime('%Y-%m-%d') if collab.start_date else '',
                    collab.end_date.strftime('%Y-%m-%d') if collab.end_date else '',
                    f"${collab.kpi_revenue:,.2f}",
                    collab.kpi_satisfaction
                ])
        except exc.SQLAlchemyError as e:
            logger.error(f"Error querying collaborations: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing collaborations data: {str(e)}")
            raise

        # Opportunities Sheet
        try:
            ws_opps = wb.create_sheet("Opportunities")
            headers = ["Opportunity ID", "Company", "Title", "Stage", "Expected Revenue", "Probability", "Next Meeting"]
            ws_opps.append(headers)
            
            for cell in ws_opps[1]:
                cell.font = header_style
                cell.fill = header_fill

            opportunities = Opportunity.query.all()
            if not opportunities:
                logger.warning("No opportunities found in database")
            
            for opp in opportunities:
                ws_opps.append([
                    opp.id,
                    opp.company.name,
                    opp.title,
                    opp.stage,
                    f"${opp.expected_revenue:,.2f}",
                    f"{opp.probability}%",
                    opp.next_meeting_date.strftime('%Y-%m-%d') if opp.next_meeting_date else ''
                ])
        except exc.SQLAlchemyError as e:
            logger.error(f"Error querying opportunities: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing opportunities data: {str(e)}")
            raise

        # Auto-adjust column widths
        for worksheet in [ws_companies, ws_collabs, ws_opps]:
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value or "")) for cell in column_cells)
                col = openpyxl.utils.get_column_letter(column_cells[0].column)
                worksheet.column_dimensions[col].width = min(length + 2, 50)

        # Save to BytesIO
        excel_data = BytesIO()
        wb.save(excel_data)
        excel_data.seek(0)

        # Set filename with timestamp
        filename = f'collaboration_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return Response(
            excel_data.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )

    except Exception as e:
        logger.error(f"Export error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Error generating export file'}), 500
    
    finally:
        if excel_data:
            excel_data.close()

# Analytics API endpoints
@app.route('/api/analytics/revenue')
def analytics_revenue():
    try:
        # Pipeline revenue by stage
        stage_revenue = db.session.query(
            Opportunity.stage,
            func.sum(Opportunity.expected_revenue * Opportunity.probability / 100).label('weighted_revenue')
        ).group_by(Opportunity.stage).all()

        # Collaboration revenue by status
        collab_revenue = db.session.query(
            Collaboration.status,
            func.sum(Collaboration.kpi_revenue).label('total_revenue')
        ).group_by(Collaboration.status).all()

        return jsonify({
            'stage_revenue': [
                {'stage': stage, 'weighted_revenue': float(revenue) if revenue else 0}
                for stage, revenue in stage_revenue
            ],
            'collab_revenue': [
                {'status': status, 'total_revenue': float(revenue) if revenue else 0}
                for status, revenue in collab_revenue
            ]
        })
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in revenue analytics: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Error in revenue analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/satisfaction')
def analytics_satisfaction():
    try:
        satisfaction_data = db.session.query(
            Company.name,
            func.avg(Collaboration.kpi_satisfaction).label('satisfaction')
        ).join(Collaboration).group_by(Company.name).all()

        return jsonify([
            {
                'company': name,
                'satisfaction': float(satisfaction) if satisfaction else 0
            }
            for name, satisfaction in satisfaction_data
        ])
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in satisfaction analytics: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Error in satisfaction analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/pipeline')
def analytics_pipeline():
    try:
        pipeline_data = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.sum(Opportunity.expected_revenue).label('total_value')
        ).group_by(Opportunity.stage).all()

        return jsonify([
            {
                'stage': stage,
                'count': int(count),
                'total_value': float(value) if value else 0
            }
            for stage, count, value in pipeline_data
        ])
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in pipeline analytics: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Error in pipeline analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    try:
        companies = Company.query.filter(
            or_(
                Company.name.ilike(f'%{query}%'),
                Company.industry.ilike(f'%{query}%')
            )
        ).all()
        
        return jsonify([{
            'id': company.id,
            'name': company.name,
            'industry': company.industry
        } for company in companies])
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in search: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500

@app.route('/company/<int:id>')
def company_detail(id):
    try:
        company = Company.query.get_or_404(id)
        return render_template('company_detail.html', company=company)
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in company detail: {str(e)}")
        return "Database error occurred", 500

@app.route('/company/documents/<int:id>')
def company_documents(id):
    try:
        company = Company.query.get_or_404(id)
        return render_template('documents.html', company=company)
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in company documents: {str(e)}")
        return "Database error occurred", 500

@app.route('/collaboration/documents/<int:id>')
def collaboration_documents(id):
    try:
        collaboration = Collaboration.query.get_or_404(id)
        return render_template('documents.html', collaboration=collaboration)
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in collaboration documents: {str(e)}")
        return "Database error occurred", 500

@app.route('/pipeline')
def pipeline():
    try:
        companies = Company.query.all()
        opportunities = Opportunity.query.all()
        return render_template('pipeline.html', companies=companies, opportunities=opportunities)
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error in pipeline: {str(e)}")
        return "Database error occurred", 500

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html')
