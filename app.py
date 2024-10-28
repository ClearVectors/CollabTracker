import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure app using environment variables
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key_fortune100"

# Database configuration with retry logic
def get_database_url():
    # Use environment variables that are already set
    return os.environ.get("DATABASE_URL")

def initialize_database(max_retries=5, retry_delay=2):
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Configure SQLAlchemy
            app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
                "pool_pre_ping": True,  # Enable automatic reconnection
                "pool_recycle": 300,    # Recycle connections every 5 minutes
                "pool_timeout": 30,     # Connection timeout of 30 seconds
                "max_overflow": 10,     # Allow up to 10 connections over pool_size
                "pool_size": 5          # Maintain a pool of 5 connections
            }
            
            db.init_app(app)
            
            # Test the connection
            with app.app_context():
                db.session.execute(db.text('SELECT 1'))
                db.session.commit()
                logger.info("Database connection successful")
                return True
                
        except SQLAlchemyError as e:
            retry_count += 1
            logger.error(f"Database connection attempt {retry_count} failed: {str(e)}")
            if retry_count < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error("Maximum database connection retries reached")
                raise
        except Exception as e:
            logger.error(f"Unexpected error during database initialization: {str(e)}")
            raise

# Configure upload folder
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'documents')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database with retry logic
initialize_database()

# Import models and create tables
with app.app_context():
    import models
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

from routes import *
