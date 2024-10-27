from flask import render_template, request, jsonify, redirect, url_for, send_from_directory, flash, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import Company, Collaboration, Opportunity, Document
from datetime import datetime
from sqlalchemy import or_, func
import os
import magic
from predictive_analytics import get_predictive_analytics
