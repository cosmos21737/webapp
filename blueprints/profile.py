from flask import Blueprint, request, render_template, flash
from flask_login import login_required, current_user
from db_models import db, User

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def profile():
    user_id = current_user.get_id()
    user = User.query.get(user_id)

    return render_template('profile.html',
                           user=user,
                           current_user=current_user)


@profile_bp.route('/profile/change_password', methods=['GET', 'POST'])
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
