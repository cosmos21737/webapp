from flask import Blueprint, request, render_template, flash
from flask_login import login_required, current_user
from db_models import db, User

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@profile_bp.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = db.session.get(User, current_user.get_id())
    if not user:
        flash('ユーザーが見つかりません。', 'error')
        return render_template('profile.html')

    if request.method == 'POST':
        from werkzeug.security import generate_password_hash, check_password_hash

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # 現在のパスワードの確認
        if not (current_password and check_password_hash(user.password_hash, current_password)):
            flash('現在のパスワードが正しくありません。', 'error')
            return render_template('profile.html')

        # 新しいパスワードの確認
        if not new_password or new_password != confirm_password:
            flash('新しいパスワードと確認用パスワードが一致しません。', 'error')
            return render_template('profile.html')

        # パスワードの長さチェック
        if len(new_password) < 6:
            flash('パスワードは6文字以上で入力してください。', 'error')
            return render_template('profile.html')

        # パスワードの更新（password_hashフィールドを使用）
        try:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('パスワードが正常に変更されました。', 'success')
            return render_template('profile.html')
        except Exception as e:
            flash('パスワードの変更中にエラーが発生しました。', 'error')
            print(f"Error: {e}")
            db.session.rollback()
            return render_template('profile.html')

    return render_template('profile.html')
