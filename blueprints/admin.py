from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from flask_security import roles_required, roles_accepted
from sqlalchemy import func

from services import services
from db_models import db, User, MeasurementRecord

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
@roles_required("administer")
def admin():
    return render_template('admin.html')


@admin_bp.route('/data_delete')
@login_required
@roles_required("administer")
def data_delete():
    try:
        # すべてのテーブルを削除
        db.drop_all()

        # 必要に応じて再作成
        db.create_all()
        services.initialize_database()

        flash('データベースを初期化しました。', 'success')
    except Exception as e:
        flash(f'初期化中にエラーが発生しました: {e}', 'danger')

    return redirect(url_for('main.dashboard'))
