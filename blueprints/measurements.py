from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
from flask_security import roles_required
from db_models import db, User, MeasurementRecord
from datetime import datetime
import csv
import io

measurements_bp = Blueprint('measurements', __name__)


@measurements_bp.route('input', methods=['GET', 'POST'])
@login_required
@roles_required("manager")
def records_input():
    user = User.query.get(current_user.get_id())
    return render_template('/measurements/records_input.html', user=user)


@measurements_bp.route('/submit_record', methods=['POST'])
@login_required
@roles_required("manager")
def submit_record():
    created_by = current_user.get_id()  # 記入者（ログインしているユーザー）
    member_name = request.form.get('member_name')  # 記録を保存する対象の部員名
    measurement_date = request.form.get('measurement_date')

    # 指定された名前の部員を検索
    user = User.query.filter_by(name=member_name).first()
    if not user:
        return "部員が見つかりません", 404  # ユーザーが存在しない場合のエラーハンドリング

    # 測定記録を作成
    new_record = MeasurementRecord(
        user_id=user.user_id,  # 記録対象の部員の ID を設定
        measurement_date=datetime.strptime(measurement_date, '%Y-%m-%d'),
        run_50m=request.form.get('run_50m'),
        base_running=request.form.get('base_running'),
        long_throw=request.form.get('long_throw'),
        straight_speed=request.form.get('straight_speed'),
        hit_speed=request.form.get('hit_speed'),
        swing_speed=request.form.get('swing_speed'),
        bench_press=request.form.get('bench_press'),
        squat=request.form.get('squat'),
        status='draft',
        created_by=created_by  # 記入者の ID を記録
    )

    db.session.add(new_record)
    db.session.commit()

    return redirect(url_for('main.dashboard'))


@measurements_bp.route('/csv_import', methods=['GET', 'POST'])
@login_required
@roles_required("manager")
def csv_import():
    """CSV一括インポート画面とファイル処理"""
    if request.method == 'GET':
        user = User.query.get(current_user.get_id())
        return render_template('/measurements/csv_import.html', user=user)

    # POST処理
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

    try:
        # CSVファイルを読み込み
        file_content = file.stream.read().decode("UTF8")
        dialect = csv.Sniffer().sniff(file_content.split('\n')[0])
        stream = io.StringIO(file_content, newline=None)
        csv_reader = csv.DictReader(stream, dialect=dialect)

        success_count = 0
        error_messages = []
        created_by = current_user.get_id()

        for row_num, row in enumerate(csv_reader, start=2):  # ヘッダー行があるので2行目から
            try:
                # 必須フィールドの検証
                grade = row.get('学年', '').strip()
                name = row.get('氏名', '').strip()
                measurement_date = row.get('測定日', '').strip()

                if not name:
                    error_messages.append(f"行{row_num}: 氏名が入力されていません")
                    continue

                if not measurement_date:
                    error_messages.append(f"行{row_num}: 測定日が入力されていません")
                    continue

                # 学年と氏名を結合して部員名を作成（学年がある場合）
                if grade:
                    member_name = f"{grade} {name}"
                else:
                    member_name = name

                # 部員の存在確認（完全一致と氏名だけでの検索を試行）
                user = User.query.filter_by(name=member_name).first()
                if not user:
                    # 完全一致しない場合は氏名だけで検索
                    user = User.query.filter_by(name=name).first()
                    if not user:
                        error_messages.append(f"行{row_num}: 部員「{member_name}」または「{name}」が見つかりません")
                        continue

                # 日付の変換
                try:
                    parsed_date = datetime.strptime(measurement_date, '%Y/%m/%d')
                except ValueError:
                    try:
                        parsed_date = datetime.strptime(measurement_date, '%Y-%m-%d')
                    except ValueError:
                        error_messages.append(
                            f"行{row_num}: 測定日の形式が正しくありません（YYYY/MM/DD または YYYY-MM-DD）")
                        continue

                # 数値フィールドの処理（空の場合はNoneにする）
                def parse_float(value):
                    if not value or str(value).strip() == '':
                        return None
                    try:
                        return float(value)
                    except ValueError:
                        return None

                # 測定記録を作成
                new_record = MeasurementRecord(
                    user_id=user.user_id,
                    measurement_date=parsed_date,
                    run_50m=parse_float(row.get('50m走 [秒]')),
                    base_running=parse_float(row.get('ベースランニング [秒]')),
                    long_throw=parse_float(row.get('遠投 [m]')),
                    straight_speed=parse_float(row.get('ストレート球速 [km/h]')),
                    hit_speed=parse_float(row.get('打球速度 [km/h]')),
                    swing_speed=parse_float(row.get('スイング速度 [km/h]')),
                    bench_press=parse_float(row.get('ベンチプレス [kg]')),
                    squat=parse_float(row.get('スクワット [kg]')),
                    status='draft',
                    created_by=created_by
                )

                db.session.add(new_record)
                success_count += 1

            except Exception as e:
                error_messages.append(f"行{row_num}: 処理中にエラーが発生しました - {str(e)}")

        # データベースにコミット
        if success_count > 0:
            db.session.commit()
            flash(f'{success_count}件の記録を正常に登録しました', 'success')

        # エラーメッセージの表示
        if error_messages:
            for msg in error_messages[:10]:  # 最大10件まで表示
                flash(msg, 'error')
            if len(error_messages) > 10:
                flash(f'その他{len(error_messages) - 10}件のエラーがあります', 'error')

        if success_count == 0 and error_messages:
            db.session.rollback()
            flash('データの登録に失敗しました。CSVファイルの内容を確認してください', 'error')

    except Exception as e:
        db.session.rollback()
        flash(f'CSVファイルの処理中にエラーが発生しました: {str(e)}', 'error')

    return redirect(url_for('measurements.csv_import'))


@measurements_bp.route('/download_csv_template')
@login_required
@roles_required("manager")
def download_csv_template():
    """CSVテンプレートファイルのダウンロード"""
    from flask import Response

    # CSVテンプレートの内容
    template_content = """学年,氏名,50m走 [秒],ベースランニング [秒],遠投 [m],ストレート球速 [km/h],打球速度 [km/h],スイング速度 [km/h],ベンチプレス [kg],スクワット [kg],測定日
1,渡辺 蒼,7.38,13.1,51,101,109,110,66,138,2025/4/1
1,吉田 翔太,7.19,11.8,65,144,106,89,92,110,2025/4/1
1,清水 悠人,6.59,12.3,58,139,105,110,94,94,2025/4/1"""

    return Response(
        template_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=measurement_template.csv"}
    )