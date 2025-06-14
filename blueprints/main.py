from flask import request, Blueprint, render_template, redirect, url_for, session
from flask_login import login_required, current_user
from flask_security import roles_required, roles_accepted
from db_models import db, User, MeasurementRecord

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return redirect(url_for('auth.login'))  # 最初にログインページへ


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/my/records')
@login_required
@roles_required("member")
def my_records():
    user_id = current_user.get_id()
    records = MeasurementRecord.query.filter_by(user_id=user_id, status='approved').all()
    user = User.query.get(user_id)

    return render_template('/my/records.html', user=user, records=records)


@main_bp.route('/my/notice')
@login_required
@roles_accepted("member", "manager", "coach")
def notice():
    user_id = current_user.get_id()
    user = User.query.get(user_id)
    if current_user.has_role("member"):
        records = MeasurementRecord.query.filter_by(user_id=user_id, status='draft').all()
    if current_user.has_role("coach"):
        records = MeasurementRecord.query.filter_by(status='pending_coach').all()
    if current_user.has_role("manager"):
        records = MeasurementRecord.query.filter_by(status='rejected').all()

    return render_template('notice.html', user=user, records=records)


@main_bp.route("/approve_records", methods=["POST"])
@login_required
@roles_accepted("member", "manager", "coach")
def approve_records():
    selected_record_ids = request.form.getlist("record_ids")  # 選択されたIDのリスト
    action = request.form.get('action')

    if selected_record_ids:
        # データベース更新処理
        records = MeasurementRecord.query.filter(MeasurementRecord.record_id.in_(selected_record_ids)).all()
        for record in records:
            if action == "reject":
                record.status = 'rejected'
            elif current_user.has_role("member"):
                record.status = 'pending_coach'  # 承認フラグを更新
            elif current_user.has_role("coach"):
                record.status = 'approved'
            elif current_user.has_role("manager"):
                db.session.delete(record)
        db.session.commit()

    return redirect(url_for("main.notice"))


@main_bp.route('/profile')
@login_required
def profile():
    user_id = current_user.get_id()
    user = User.query.get(user_id)

    return render_template('profile.html',
                           user=user,
                           current_user=current_user)


@main_bp.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        from werkzeug.security import generate_password_hash, check_password_hash
        from flask import flash

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user = User.query.get(current_user.get_id())

        # 現在のパスワードの確認
        password_verified = False

        if check_password_hash(user.password_hash, current_password):
            password_verified = True

        if not password_verified:
            flash('現在のパスワードが正しくありません。', 'error')
            return render_template('profile.html', user=user)

        # 新しいパスワードの確認
        if new_password != confirm_password:
            flash('新しいパスワードと確認用パスワードが一致しません。', 'error')
            return render_template('profile.html', user=user)

        # パスワードの長さチェック
        if len(new_password) < 6:
            flash('パスワードは6文字以上で入力してください。', 'error')
            return render_template('profile.html', user=user)

        # パスワードの更新（password_hashフィールドを使用）
        try:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('パスワードが正常に変更されました。', 'success')
            return render_template('profile.html', user=user)
        except Exception as e:
            flash('パスワードの変更中にエラーが発生しました。', 'error')
            print(f"Error: {e}")
            db.session.rollback()
            return render_template('profile.html', user=user)

    user = User.query.get(current_user.get_id())
    return render_template('profile.html', user=user)
