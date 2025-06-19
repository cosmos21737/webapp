import math

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from flask_security import roles_required, roles_accepted
from sqlalchemy import func

from db_models import db, User, MeasurementRecord

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return redirect(url_for('auth.login'))  # 最初にログインページへ


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/help')
@login_required
def helppage():
    return render_template('help.html')


@main_bp.route('/admin')
@login_required
@roles_required("administer")
def admin():
    return render_template('admin.html')



