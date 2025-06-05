from flask import Flask, render_template, request, redirect, url_for, session
from db_models import db, User,MeasurementRecord
from werkzeug.security import check_password_hash

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

@app.route('/measurements/input')
def measurements_input():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # 未ログインならログインページへ

    return render_template('/measurements/input.html')

@app.route('/my/records')
def my_records():
    if 'user_id' not in session:  # 未ログインの場合リダイレクト
        return redirect(url_for('login'))

    user_id = session['user_id']  # ログインユーザーのIDを取得
    records = MeasurementRecord.query.filter_by(user_id=user_id).all()  # ユーザーの記録のみ取得

    return render_template('/my/records.html', records=records)



@app.route('/members')
def members():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    members = User.query.filter_by(role='member', is_active=True).all()
    return render_template('members.html', members=members)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)