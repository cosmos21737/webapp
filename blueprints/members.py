from flask import Blueprint, request, render_template, redirect, url_for, session
from db_models import User, Role, db
from flask_security import login_required, current_user, roles_required, roles_accepted
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from db_models import db, User

members_bp = Blueprint('members', __name__, url_prefix='/members')


@members_bp.route('/')
@login_required
@roles_accepted("coach", "director")
def members():
    # "member" ロールを持つアクティブなユーザーを取得
    members_list = User.query.options(joinedload(User.roles)).filter(
        User.is_active == True,
        User.roles.any(Role.name == "member")  # ここが修正点
    ).all()

    return render_template('members.html', members=members_list)


@members_bp.route('/new')
@login_required
@roles_accepted("coach", "director")
def new_member():
    return render_template('new_member.html')  # 部員登録ページへ


@members_bp.route('/register', methods=['POST'])
@login_required
@roles_accepted("coach", "director")
def register_member():
    name = request.form.get('name')
    grade = request.form.get('grade')
    is_active = request.form.get('is_active') == "true"
    password = "mypassword123"
    hashed_password = generate_password_hash(password)

    # "member" ロールを取得
    member_role = Role.query.filter_by(name="member").first()
    if not member_role:
        print("エラー: 'member' ロールがデータベースに存在しません")
        return redirect(url_for('members.members'))

    # ユーザーを作成してロールを追加
    member_instance = User(
        name=name,
        grade=int(grade) if grade else None,
        is_active=is_active,
        password_hash=hashed_password
    )
    member_instance.roles.append(member_role)  # 多対多リレーションを適用

    db.session.add(member_instance)
    db.session.commit()

    return redirect(url_for('members.members'))