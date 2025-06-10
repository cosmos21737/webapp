from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db_models import db, User

members_bp = Blueprint('members', __name__, url_prefix='/members')

@members_bp.route('/')
def members():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    members_list = User.query.filter_by(role='member', is_active=True).all()
    return render_template('members.html', members=members_list)

@members_bp.route('/new')
def new_member():
    return render_template('new_member.html')  # 部員登録ページへ

@members_bp.route('/register', methods=['POST'])
def register_member():
    name = request.form.get('name')
    grade = request.form.get('grade')
    is_active = request.form.get('is_active') == "true"
    password = "mypassword123"
    hashed_password = generate_password_hash(password)

    member_instance = User(
        name=name,
        grade=int(grade),
        is_active=is_active,
        role='member',
        password_hash=hashed_password
    )

    db.session.add(member_instance)
    db.session.commit()
    return redirect(url_for('members.members'))