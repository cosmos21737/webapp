import csv
import io


def parse_csv_file(file_stream):
    """
    ファイルストリームからCSVデータを読み込み、辞書のリストとして返す。
    自動で区切り文字を判定する。
    """
    file_content = file_stream.read().decode("UTF8")
    if not file_content.strip():
        return []  # ファイルが空の場合

    # 最初の行から区切り文字を推測
    try:
        dialect = csv.Sniffer().sniff(file_content.split('\n')[0])
    except csv.Error:
        # 推測できない場合はデフォルトのカンマ区切りとして扱う
        dialect = 'excel'

    stream = io.StringIO(file_content, newline=None)
    csv_reader = csv.DictReader(stream, dialect=dialect)
    return list(csv_reader)


def normalize_csv_row_keys(row):
    """
    CSV行の辞書のキーを正規化する（トリム、小文字化、全角スペースを半角スペースに変換）。
    """
    return {
        key.strip().lower().translate(str.maketrans('　', ' ')): value
        for key, value in row.items()
    }
