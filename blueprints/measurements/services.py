import csv
import io
import re # 正規表現モジュールをインポート
from flask_login import current_user
from datetime import datetime
from db_models import db, User, MeasurementRecord, MeasurementValue, MeasurementType, Role


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
        parsed_date = datetime.strptime(measurement_date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("測定日の形式が正しくありません（YYYY-MM-DD）。例: 2025-04-01")

    new_record = MeasurementRecord(
        user_id=user_id,
        measurement_date=parsed_date,
        status='draft',
        created_by=created_by
    )
    db.session.add(new_record)
    db.session.flush() # new_record.idを取得するためにflushする

    # すべての測定タイプを取得
    all_measurement_types = MeasurementType.query.all()

    for m_type in all_measurement_types:
        value_str = form_data.get(m_type.name) # フォームからの入力はm_type.nameで取得
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
                # 不正な値は無視するか、エラーとして処理
                pass
    # commitは呼び出し元で行う


def process_csv_upload(file_content, created_user):
    """CSVファイルを解析し、複数の測定記録をデータベースに追加する（リレーショナル設計対応版）"""
    # CSV解析準備
    try:
        dialect = csv.Sniffer().sniff(file_content.split('\n')[0])
        stream = io.StringIO(file_content, newline=None)
        csv_reader = csv.DictReader(stream, dialect=dialect)
    except Exception as e:
        return 0, [f"CSV解析エラー: {str(e)}"]

    success_count = 0
    error_messages = []

    # データベースからMeasurementTypeを全て取得し、CSVヘッダー形式に合わせたマッピングを作成
    # 例: {'50m走 [秒]': <MeasurementType object for run_50m>, ...}
    measurement_types_by_csv_header = {}
    for mt in MeasurementType.query.all():
        header_name = f"{mt.display_name} [{mt.unit}]" if mt.unit else mt.display_name
        measurement_types_by_csv_header[header_name] = mt

    # さらに、単位括弧がない場合も考慮する（より柔軟なマッチングのため）
    # 例: '50m走' も '50m走 [秒]' にマッチさせる
    measurement_types_by_display_name = {mt.display_name: mt for mt in MeasurementType.query.all()}


    for row_num, row in enumerate(csv_reader, start=2):
        try:
            # 基本情報取得
            csv_grade = row.get('学年', '').strip()
            csv_name = row.get('氏名', '').strip()
            measurement_date = row.get('測定日', '').strip()

            # 権限に基づくステータス設定
            status_value = "draft"
            if current_user.has_role("administer"):
                status_value = row.get('承認', '').replace('\u3000', ' ').strip() or "draft"

            # 必須フィールド検証
            if not csv_name:
                raise ValueError("氏名が入力されていません")
            if not measurement_date:
                raise ValueError("測定日が入力されていません")

            # ユーザー検索
            user = User.query.filter_by(name=csv_name, grade=csv_grade).first()
            if not user:
                raise ValueError(f"学年「{csv_grade}」の氏名「{csv_name}」の部員が見つかりません")

            # 日付変換
            parsed_date = parse_date(measurement_date)
            if not parsed_date:
                raise ValueError("測定日の形式が正しくありません（YYYY/MM/DD またはYYYY-MM-DD）")

            # 測定記録作成
            record = MeasurementRecord(
                user_id=user.user_id,
                measurement_date=parsed_date,
                status=status_value,
                created_by=current_user.user_id
            )
            db.session.add(record)
            db.session.flush()  # record.idを取得するために必要

            # 測定値を個別に追加
            for field_name, value in row.items():
                field_name_stripped = field_name.strip()
                if field_name_stripped in ['学年', '氏名', '測定日', '承認']:
                    continue

                # CSVヘッダー名からMeasurementTypeを特定
                m_type = measurement_types_by_csv_header.get(field_name_stripped)

                # 単位括弧がない場合も考慮して再度検索
                if not m_type:
                    # 単位部分（例: ' [秒]'）を削除してマッチングを試みる
                    clean_field_name = re.sub(r' \[.*?\]$', '', field_name_stripped)
                    m_type = measurement_types_by_display_name.get(clean_field_name)


                if not m_type:
                    # マッチするMeasurementTypeが見つからない場合はスキップ
                    continue

                # 値の解析
                parsed_value = parse_float_or_none(value)
                if parsed_value is None:
                    continue

                # MeasurementValue作成
                db.session.add(MeasurementValue(
                    record_id=record.id,
                    type_id=m_type.id,
                    value=parsed_value
                ))

            success_count += 1

        except Exception as e:
            error_messages.append(f"行{row_num}: {str(e)}。スキップしました。")
            db.session.rollback()
            continue

    # トランザクション確定
    if success_count > 0:
        db.session.commit()
    else:
        db.session.rollback()

    return success_count, error_messages


# ヘルパー関数
def parse_date(date_str):
    """日付文字列を解析"""
    for fmt in ('%Y/%m/%d', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_float_or_none(value):
    """文字列をfloatに変換（空欄や不正値はNone）"""
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def generate_csv_template_content():
    """
    CSVテンプレートの内容を文字列で返す。
    動的にMeasurementTypeからヘッダーとサンプルデータを生成する。
    測定値は0.0とし、氏名は固定の「テスト部員１」「テスト部員２」「テスト部員３」とする。
    学年は仮に「1」とする。
    """
    header_parts = ['学年', '氏名']
    # 順番を保証するためにorder_byを使用し、すべてのMeasurementTypeを取得
    measurement_types = MeasurementType.query.order_by(MeasurementType.id).all()
    for m_type in measurement_types:
        # display_nameとunitを組み合わせてCSVヘッダー名を生成
        header_name = f"{m_type.display_name} [{m_type.unit}]" if m_type.unit else m_type.display_name
        header_parts.append(header_name)

    header_parts.append('測定日')
    # 管理者権限を持つユーザーが「承認」カラムをCSVに含めたい場合は追加
    # header_parts.append('承認') # 必要に応じてコメント解除

    header = ",".join(header_parts)

    # サンプルデータを動的に生成
    example_rows = []
    # 固定の部員名リスト
    fixed_member_names = ["テスト部員１", "テスト部員２", "テスト部員３"]

    # 今日の日付をYYYY/MM/DD形式で取得
    today_date_str = datetime.now().strftime('%Y/%m/%d')

    for i, member_name in enumerate(fixed_member_names):
        # 仮に学年を1年生とする
        grade = "1"
        row_values = [grade, member_name]
        for m_type in measurement_types:
            row_values.append("0.0")  # すべての測定値を0.0に設定
        row_values.append(today_date_str)
        example_rows.append(",".join(row_values))

    example_data = "\n".join(example_rows)

    return header + "\n" + example_data