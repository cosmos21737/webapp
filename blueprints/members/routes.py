import io
import csv

from flask import Blueprint, request, render_template, redirect, url_for, flash, Response
from flask_security import login_required, current_user, roles_required, roles_accepted

# service をインポート
from . import members_bp
from . import services


@members_bp.route('/')
@login_required
@roles_accepted("coach", "director")
def members():
    members_list = services.get_members_list()
    return render_template('/members/members.html', members=members_list)


@members_bp.route('/new')
@login_required
@roles_accepted("coach", "director")
def new_member():
    return render_template('/members/new_member.html')


@members_bp.route('/register', methods=['POST'])
@login_required
@roles_accepted("coach", "director")
def register_member():
    name = request.form.get('name')
    grade = request.form.get('grade')
    is_active = request.form.get('is_active') == "true"
    password = "password123"  # 固定パスワード

    success, message = services.register_new_member(name, grade, is_active, password)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('members.members'))


@members_bp.route('/records/<int:member_id>')
@login_required
@roles_accepted("coach", "director")
def member_records(member_id):
    user, records = services.get_member_and_records(member_id)
    if not user:
        flash("部員が見つかりません", 'error')
        return redirect(url_for('members.members'))
    return render_template('my/records.html', user=user, records=records)


@members_bp.route('/delete/<int:member_id>', methods=['POST'])
@login_required
@roles_accepted("coach", "director")
def delete_member(member_id):
    success, message = services.delete_member_by_id(member_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('members.members'))


@members_bp.route('/csv_import', methods=['GET', 'POST'])
@login_required
@roles_accepted("coach", "director")
def csv_import():
    if request.method == 'GET':
        return render_template('/members/csv_import.html')

    if 'csv_file' not in request.files:
        flash('ファイルが選択されていません', 'error')
        return redirect(request.url)

    file = request.files['csv_file']
    if file.filename == '':
        flash('ファイルが選択されていません', 'error')
        return redirect(request.url)

    if not file.filename.lower().endswith('.csv'):
        flash('CSVファイルを選択してください', 'error')
        return redirect(request.url)

    success_count, error_messages = services.process_csv_upload(file)

    if success_count > 0:
        flash(f'{success_count}件の部員を正常に登録しました', 'success')

    if error_messages:
        for msg in error_messages[:10]:
            flash(msg, 'error')
        if len(error_messages) > 10:
            flash(f'その他{len(error_messages) - 10}件のエラーがあります', 'error')

    return redirect(url_for('members.csv_import'))


@members_bp.route('/download_csv_template')
@login_required
@roles_accepted("coach", "director")
def download_csv_template():
    template_content = services.generate_csv_template_content()
    return Response(
        template_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=member_template.csv"}
    )