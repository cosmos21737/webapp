from flask import Flask, render_template, request, jsonify, redirect, url_for, session, current_app
from db_models import db, User,MeasurementRecord
from werkzeug.security import check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション用の秘密キー
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baseball_team.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def home():
    return redirect(url_for('login'))  # 最初はログインページへ

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(name=username).first()
        if user and user.password_hash == password:
            session['user_id'] = user.user_id
            session['username'] = user.name
            session['role'] = user.role
            return redirect(url_for('dashboard'))  # ログイン成功後ダッシュボードへ
        else:
            return "ログイン失敗！ユーザー名またはパスワードが間違っています。"

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # 未ログインならログインページへ

    return render_template('dashboard.html')

@app.route('/measurements/input', methods=['GET', 'POST'])
def measurements_input():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('/measurements/input.html', user=user)

@app.route('/submit_record', methods=['POST'])
def submit_record():
    created_by = session['user_id']
    member_name = request.form.get('member_name')
    user = User.query.filter_by(name=member_name).first()  # 部員名からユーザーを検索

    if not user:
        return "指定された部員が見つかりません", 404

    user_id = user.user_id  # 検索結果から user_id を取得

    # フォームデータを取得
    measurement_date = request.form.get('measurement_date')
    run_50m = request.form.get('run_50m')
    base_running = request.form.get('base_running')
    long_throw = request.form.get('long_throw')
    straight_speed = request.form.get('straight_speed')
    hit_speed = request.form.get('hit_speed')
    swing_speed = request.form.get('swing_speed')
    bench_press = request.form.get('bench_press')
    squat = request.form.get('squat')

    # 新しいレコードを作成
    new_record = MeasurementRecord(
        user_id=user_id,  # 名前から取得した user_id を使用
        measurement_date=datetime.strptime(measurement_date, '%Y-%m-%d'),
        run_50m=float(run_50m) if run_50m else None,
        base_running=float(base_running) if base_running else None,
        long_throw=float(long_throw) if long_throw else None,
        straight_speed=float(straight_speed) if straight_speed else None,
        hit_speed=float(hit_speed) if hit_speed else None,
        swing_speed=float(swing_speed) if swing_speed else None,
        bench_press=float(bench_press) if bench_press else None,
        squat=float(squat) if squat else None,
        created_by = created_by,
        status = 'draft'
    )

    # データベースに保存
    db.session.add(new_record)
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/my/records')
def my_records():
    if 'user_id' not in session:  # 未ログインの場合リダイレクト
        return redirect(url_for('login'))

    user_id = session['user_id']  # ログインユーザーのIDを取得
    records = MeasurementRecord.query.filter_by(user_id=user_id).all()  # ユーザーの記録のみ取得
    user = User.query.get(user_id)

    return render_template('/my/records.html', user=user, records=records)

@app.route('/members')
def members():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    members = User.query.filter_by(role='member', is_active=True).all()
    return render_template('members.html', members=members)

@app.route('/members/new')
def new_member():
    return render_template('new_member.html')  # 部員登録用ページへ

@app.route('/register_member', methods=['POST'])
def register_member():
    name = request.form.get('name')
    grade = request.form.get('grade')
    is_active = request.form.get('is_active') == "true"  # `true` の場合、`True` をセット


    # 部員をデータベースに追加
    new_member = User(
        name=name,
        grade=int(grade),
        is_active=is_active,
        role='member',  # 初期状態は "部員" にする
        password_hash="password123"
    )

    db.session.add(new_member)
    db.session.commit()

    return redirect(url_for('members'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/records/<int:member_id>')
def member_records(member_id):
    user = User.query.get(member_id)
    if not user:
        return "部員が見つかりません", 404

    records = MeasurementRecord.query.filter_by(user_id=member_id).all()
    return render_template('/my/records.html', user=user, records=records)

if __name__ == '__main__':
    app.run(debug=True)