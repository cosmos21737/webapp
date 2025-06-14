import csv
import io
from datetime import datetime
from db_models import db, User, MeasurementRecord  # データベースモデルをインポート


def parse_float_or_none(value):
    """
    文字列をfloatに変換するヘルパー関数。
    値がNone、空文字列、または変換できない場合はNoneを返す。
    """
    if not value or str(value).strip() == '':
        return None
    try:
        return float(value)
    except ValueError:
        return None


def create_single_measurement_record(user_id, measurement_date_str, form_data, created_by):
    """
    単一の測定記録をデータベースに追加する。
    """
    try:
        parsed_date = datetime.strptime(measurement_date_str, '%Y-%m-%d').date()  # 日付型として保存
    except ValueError:
        raise ValueError("測定日の形式が正しくありません（YYYY-MM-DD）。例: 2025-04-01")

    new_record = MeasurementRecord(
        user_id=user_id,
        measurement_date=parsed_date,
        run_50m=parse_float_or_none(form_data.get('run_50m')),
        base_running=parse_float_or_none(form_data.get('base_running')),
        long_throw=parse_float_or_none(form_data.get('long_throw')),
        straight_speed=parse_float_or_none(form_data.get('straight_speed')),
        hit_speed=parse_float_or_none(form_data.get('hit_speed')),
        swing_speed=parse_float_or_none(form_data.get('swing_speed')),
        bench_press=parse_float_or_none(form_data.get('bench_press')),
        squat=parse_float_or_none(form_data.get('squat')),
        status='draft',  # ステータスのデフォルト値を設定
        created_by=created_by
    )
    db.session.add(new_record)
    # commitは呼び出し元（routes.py）で行うことで、トランザクション管理を柔軟にする


def process_csv_upload(file_content, created_by):
    """CSVファイルを解析し、複数の測定記録をデータベースに追加する。"""
    dialect = csv.Sniffer().sniff(file_content.split('\n')[0])
    stream = io.StringIO(file_content, newline=None)
    csv_reader = csv.DictReader(stream, dialect=dialect)

    success_count = 0
    error_messages = []

    for row_num, row in enumerate(csv_reader, start=2):
        try:
            # CSVから「学年」と「氏名」を個別に取得
            csv_grade = row.get('学年', '').strip() # CSVの学年データ
            csv_name = row.get('氏名', '').strip()   # CSVの氏名データ
            measurement_date = row.get('測定日', '').strip()

            if not csv_name:
                error_messages.append(f"行{row_num}: 氏名が入力されていません。スキップしました。")
                continue
            if not measurement_date:
                error_messages.append(f"行{row_num}: 測定日が入力されていません。スキップしました。")
                continue

            # ユーザーを検索: 学年と氏名の両方が一致するユーザーを探す
            user = User.query.filter_by(name=csv_name, grade=csv_grade).first()

            if not user:
                # ユーザーが見つからなかった場合のエラーメッセージ
                error_messages.append(f"行{row_num}: 学年「{csv_grade}」の氏名「{csv_name}」の部員が見つかりません。スキップしました。")
                continue

            # 日付の変換
            parsed_date = None
            try:
                parsed_date = datetime.strptime(measurement_date, '%Y/%m/%d').date()
            except ValueError:
                try:
                    parsed_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
                except ValueError:
                    error_messages.append(
                        f"行{row_num}: 測定日の形式が正しくありません（YYYY/MM/DD またはYYYY-MM-DD）。スキップしました。")
                    continue

            # 測定記録を作成
            new_record = MeasurementRecord(
                user_id=user.user_id,
                measurement_date=parsed_date,
                run_50m=parse_float_or_none(row.get('50m走 [秒]')),
                base_running=parse_float_or_none(row.get('ベースランニング [秒]')),
                long_throw=parse_float_or_none(row.get('遠投 [m]')),
                straight_speed=parse_float_or_none(row.get('ストレート球速 [km/h]')),
                hit_speed=parse_float_or_none(row.get('打球速度 [km/h]')),
                swing_speed=parse_float_or_none(row.get('スイング速度 [km/h]')),
                bench_press=parse_float_or_none(row.get('ベンチプレス [kg]')),
                squat=parse_float_or_none(row.get('スクワット [kg]')),
                status='draft',
                created_by=created_by
            )
            db.session.add(new_record)
            success_count += 1

        except Exception as e:
            error_messages.append(f"行{row_num}: 処理中にエラーが発生しました - {str(e)}。スキップしました。")
    # 全て成功したらコミット
    if success_count > 0:
        db.session.commit()
    else:
        db.session.rollback()

    return success_count, error_messages


def generate_csv_template_content():
    """
    CSVテンプレートの内容を文字列で返す。
    """
    return """学年,氏名,50m走 [秒],ベースランニング [秒],遠投 [m],ストレート球速 [km/h],打球速度 [km/h],スイング速度 [km/h],ベンチプレス [kg],スクワット [kg],測定日
1,渡辺 蒼,7.38,13.1,51,101,109,110,66,138,2025/4/1
1,吉田 翔太,7.19,11.8,65,144,106,89,92,110,2025/4/1
1,清水 悠人,6.59,12.3,58,139,105,110,94,94,2025/4/1"""
