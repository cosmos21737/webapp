from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_security.decorators import roles_required
from db_models import User, AdminContact, db
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

# Flask-Loginのセットアップ
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # type: ignore
login_manager.login_message = "このページにアクセスするにはログインが必要です。"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')  # 学生番号のみ
        password = request.form.get('password')

        if not password:
            flash('パスワードを入力してください。', 'error')
            return redirect(url_for('auth.login'))

        if not student_id:
            flash('学生番号を入力してください。', 'error')
            return redirect(url_for('auth.login'))

        try:
            # 学生番号でユーザーを検索
            user = User.query.filter_by(student_id=student_id).first()
            
            if not user:
                flash('学生番号が存在しません。', 'error')
                return redirect(url_for('auth.login'))

            if not check_password_hash(user.password_hash, password):
                flash('パスワードが違います。', 'error')
                return redirect(url_for('auth.login'))

            login_user(user)
            flash('ログインに成功しました。', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            import traceback
            traceback.print_exc()
            flash('システムエラーが発生しました。管理者に連絡してください。', 'error')
            return redirect(url_for('auth.login'))

    contact_info = AdminContact.query.first()
    return render_template('login.html', contact=contact_info)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
