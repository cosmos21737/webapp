from flask import request, redirect, url_for, render_template, flash, Response
from flask_login import login_required, current_user
from flask_security import roles_required, roles_accepted
from db_models import db, User, MeasurementRecord, MeasurementType, MeasurementValue
from datetime import datetime

from . import measurements_bp
from . import services


@measurements_bp.route('/input', methods=['GET', 'POST'])
@login_required
@roles_accepted("administer", "manager")
def records_input():
    """
    測定記録入力フォームの表示
    """
    user = User.query.get(current_user.get_id())
    measurement_types = MeasurementType.query.all()
    return render_template('/measurements/records_input.html',
                           user=user,
                           measurement_types=measurement_types
                           )


@measurements_bp.route('/submit_record', methods=['POST'])
@login_required
@roles_accepted("administer", "manager")
def submit_record():
    """
    単一の測定記録の提出処理
    """
    created_by = current_user.get_id()  # 記入者（ログインしているユーザー）
    member_name = request.form.get('member_name')  # 記録を保存する対象の部員名
    member_grade = request.form.get('member_grade')
    measurement_date_str = request.form.get('measurement_date')

    # 部員の検索
    user = User.query.filter_by(name=member_name, grade=member_grade).first()
    if not user:
        flash(f"学年「{member_grade}」の氏名「{member_name}」の部員が見つかりません。")
        print(f"学年「{member_grade}」の氏名「{member_name}」の部員が見つかりません。")
        return redirect(url_for('measurements.records_input'))  # エラー時は入力画面に戻すなど
        # または、return "部員が見つかりません", 404

    # 日付文字列を日付オブジェクトに変換
    try:
        measurement_date = datetime.strptime(measurement_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('無効な日付形式です。', 'danger')
        return redirect(url_for('measurements.record_input'))

    try:
        # 新しいMeasurementRecordを作成
        new_record = MeasurementRecord(
            user_id=user.user_id,
            measurement_date=measurement_date,
            created_by=current_user.user_id,
            status='draft'# または、コーチの承認が必要な場合は 'pending_coach'
        )
        db.session.add(new_record)
        db.session.flush() # new_record.idを取得するためにflushする

        # 送信されたフォームデータを反復処理するために、すべての測定タイプを取得
        all_measurement_types = MeasurementType.query.all()

        for m_type in all_measurement_types:
            # この測定タイプに対応する値が送信されたか確認
            value_str = request.form.get(m_type.name)
            if value_str:
                try:
                    value_float = float(value_str)
                    new_value = MeasurementValue(
                        record_id=new_record.id,
                        type_id=m_type.id,
                        value=value_float
                    )
                    db.session.add(new_value)
                except ValueError:
                    flash(f'{m_type.display_name} の値が不正です。数値を入力してください。', 'warning')
                    # 特定の値をロールバックするか無視するかを選択することもできます
                    continue

        db.session.commit()
        flash('測定記録が正常に保存されました。', 'success')
        return redirect(url_for('measurements.records_input')) # または成功ページ
    except ValueError as e:
        # 日付形式のエラーなど、入力値の問題
        flash(str(e), 'error')
        db.session.rollback()  # エラー時はトランザクションをロールバック
        print("バリューエラー")
    except Exception as e:
        # その他の予期せぬエラー
        flash(f"記録の保存中にエラーが発生しました: {str(e)}", 'error')
        db.session.rollback()
        print(f"デバッグ: 予期せぬエラーが発生しました: {e}")

    return redirect(url_for('main.dashboard'))  # 成功または失敗に関わらずダッシュボードへリダイレクト


@measurements_bp.route('/csv_import', methods=['GET', 'POST'])
@login_required
@roles_accepted("administer", "manager")
def csv_import():
    """CSV一括インポート画面の表示とファイル処理"""
    if request.method == 'GET':
        user = User.query.get(current_user.get_id())
        return render_template('/measurements/csv_import.html', user=user)

    # POST処理：ファイルのバリデーション
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
        file_content = file.stream.read().decode("UTF8")
        # CSVファイルを処理
        success_count, error_messages = services.process_csv_upload(file_content, current_user.get_id())

        if success_count > 0:
            flash(f'{success_count}件の記録を正常に登録しました', 'success')

        # エラーメッセージの表示
        if error_messages:
            for msg in error_messages[:10]:  # 最大10件まで表示
                flash(msg, 'error')
            if len(error_messages) > 10:
                flash(f'その他{len(error_messages) - 10}件のエラーがあります', 'error')

        if success_count == 0 and error_messages:
            # 1件も成功せずエラーがあった場合
            flash('データの登録に失敗しました。CSVファイルの内容を確認してください', 'error')

    except Exception as e:
        # CSVファイル自体を開けない、読み込めないなどの例外
        flash(f'CSVファイルの処理中に予期せぬエラーが発生しました: {str(e)}', 'error')

    return redirect(url_for('measurements.csv_import'))


@measurements_bp.route('/download_csv_template')
@login_required
@roles_accepted("administer", "manager")
def download_csv_template():
    """CSVテンプレートファイルのダウンロード"""
    # サービスレイヤーの関数からテンプレート内容を取得
    template_content = services.generate_csv_template_content()
    return Response(
        template_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=measurement_template.csv"}
    )
