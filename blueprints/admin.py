from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from flask_security import roles_required

from services import services
from db_models import db, MeasurementType

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@login_required
@roles_required("administer")
def admin():
    measurement_types = MeasurementType.query.all()
    return render_template('admin.html',
                           measurement_types=measurement_types
                           )


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


@admin_bp.route('/admin/delete_measurement_type/<int:type_id>', methods=['POST'])
@login_required
@roles_required("administer")
def delete_measurement_type(type_id):
    measurement_type = MeasurementType.query.get(type_id)

    if not measurement_type:
        flash('指定された測定項目が見つかりませんでした。', 'danger')
        return redirect(url_for('admin.admin'))

    try:
        db.session.delete(measurement_type)
        db.session.commit()
        flash(f'測定項目「{measurement_type.display_name}」を削除しました。', 'success')
    except Exception as e:  # IntegrityErrorを特別に処理する必要がなくなる
        db.session.rollback()
        flash(f'測定項目の削除中にエラーが発生しました: {e}', 'danger')

    return redirect(url_for('admin.admin'))


@admin_bp.route('/admin/add_measurement_type', methods=['POST'])
@login_required
@roles_required("administer")
def add_measurement_type():
    name = request.form.get('name')
    display_name = request.form.get('display_name')
    unit = request.form.get('unit')
    evaluation_direction = request.form.get('evaluation_direction')
    description = request.form.get('description')

    if not name or not display_name or not evaluation_direction:
        flash('識別名、表示名、評価方向は必須項目です。', 'danger')
        return redirect(url_for('admin.admin'))

    existing_type = MeasurementType.query.filter_by(name=name).first()
    if existing_type:
        flash('この識別名はすでに存在します。別の識別名を使用してください。', 'danger')
        return redirect(url_for('admin.admin'))

    try:
        new_type = MeasurementType(
            name=name,
            display_name=display_name,
            unit=unit if unit else None,
            evaluation_direction=evaluation_direction,
            description=description if description else None
        )
        db.session.add(new_type)
        db.session.commit()
        flash(f'測定項目「{new_type.display_name}」を追加しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'測定項目の追加中にエラーが発生しました: {e}', 'danger')

    return redirect(url_for('admin.admin'))