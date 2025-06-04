from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション用の秘密キー

# 仮のユーザー情報
VALID_USERNAME = "test_user"
VALID_PASSWORD = "password123"

@app.route('/')
def home():
    return redirect(url_for('login'))  # 最初はログインページへ

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['username'] = username  # セッションに保存
            return redirect(url_for('dashboard'))  # ログイン成功後ダッシュボードへ
        else:
            return "ログイン失敗！ユーザー名またはパスワードが間違っています。"

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))  # 未ログインならログインページへ

    return render_template('dashboard.html')

@app.route('/measurements/input')
def measurements_input():
    if 'username' not in session:
        return redirect(url_for('login'))  # 未ログインならログインページへ

    return render_template('/measurements/input.html')

@app.route('/my/records')
def my_records():
    if 'username' not in session:
        return redirect(url_for('login'))

    # 仮データ（後でデータベースとの連携に差し替え）
    records = [
        {
            "measurement_date": "2025-06-01",
            "run_50m": 6.2,
            "base_running": 8.1,
            "long_throw": 50,
            "straight_speed": 130,
            "hit_speed": 145,
            "swing_speed": 100,
            "bench_press": 80,
            "squat": 120
        },
        {
            "measurement_date": "2025-06-03",
            "run_50m": 6.0,
            "base_running": 7.9,
            "long_throw": 55,
            "straight_speed": 135,
            "hit_speed": 150,
            "swing_speed": 105,
            "bench_press": 85,
            "squat": 125
        }
    ]

    return render_template('/my/records.html', records=records)

@app.route('/members')
def members():
    # ログイン状態のチェック
    if 'username' not in session:
        return redirect(url_for('login'))

    # 仮の部員データ
    member_list = [
        {"user_id": 1, "name": "田中太郎", "role": "部員", "grade": 3, "is_active": True},
        {"user_id": 2, "name": "佐藤花子", "role": "部員", "grade": 2, "is_active": True},
        {"user_id": 3, "name": "鈴木次郎", "role": "部員", "grade": 1, "is_active": False},
    ]

    return render_template('members.html', members=member_list)

@app.route('/logout')
def logout():
    session.pop('username', None)  # ログアウト
    return redirect(url_for('login'))  # ログアウト後はログインページへ

if __name__ == '__main__':
    app.run(debug=True)