from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required
from flask_security.decorators import roles_required

from services import services
from db_models import db, MeasurementType, AdminContact

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@login_required
@roles_required("administer")
def admin():
    # カテゴリフィルターの取得
    category_filter = request.args.get('category', '')
    
    # 測定タイプの取得（カテゴリフィルター適用）
    if category_filter:
        measurement_types = MeasurementType.query.filter_by(category=category_filter).all()
    else:
        measurement_types = MeasurementType.query.all()
    
    # 利用可能なカテゴリ一覧を取得
    categories = db.session.query(MeasurementType.category).distinct().filter(MeasurementType.category.isnot(None)).all()
    categories = [cat[0] for cat in categories]
    
    return render_template('admin.html',
                           measurement_types=measurement_types,
                           categories=categories,
                           current_category=category_filter
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
        services.initialize_database(current_app)

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


@admin_bp.route('/admin/contact', methods=['GET', 'POST'])
@login_required
@roles_required("administer")
def manage_contact():
    # 常に最初のレコードを対象とする
    contact = AdminContact.query.first()
    if not contact:
        # もしデータがなければ、空のデータを作成してセッションに追加
        contact = AdminContact()
        contact.email=""
        contact.phone=""
        contact.note=""
        db.session.add(contact)
        db.session.commit()
        # 再度取得し、Noneでないことを保証する
        contact = AdminContact.query.first()
    
    if not contact:
        flash('連絡先情報の取得に失敗しました。', 'danger')
        return redirect(url_for('admin.admin'))

    if request.method == 'POST':
        contact.email = request.form.get('email', '')
        contact.phone = request.form.get('phone', '')
        contact.note = request.form.get('note', '')
        try:
            db.session.commit()
            flash('連絡先情報を更新しました。', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'更新中にエラーが発生しました: {e}', 'danger')
        return redirect(url_for('admin.manage_contact'))

    return render_template('admin/contact.html', contact=contact)


@admin_bp.route('/admin/add_measurement_type', methods=['POST'])
@login_required
@roles_required("administer")
def add_measurement_type():
    name = request.form.get('name')
    display_name = request.form.get('display_name')
    category = request.form.get('category')
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
        new_type = MeasurementType()
        new_type.name=name
        new_type.display_name=display_name
        new_type.category=category if category else None
        new_type.unit=unit if unit else None
        new_type.evaluation_direction=evaluation_direction
        new_type.description=description if description else None

        db.session.add(new_type)
        db.session.commit()
        flash(f'測定項目「{new_type.display_name}」を追加しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'測定項目の追加中にエラーが発生しました: {e}', 'danger')

    return redirect(url_for('admin.admin'))