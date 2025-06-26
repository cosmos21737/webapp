from flask import Flask
from db_models import db, MeasurementType

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baseball_team.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def create_measurement_types():
    """測定タイプの初期データを作成"""
    measurement_types = [
        # 走力
        {
            'name': 'run_50m',
            'display_name': '50m走',
            'category': '走力',
            'unit': '秒',
            'evaluation_direction': 'asc',
            'description': '50m走の記録（秒）'
        },
        {
            'name': 'base_running',
            'display_name': 'ベースランニング',
            'category': '走力',
            'unit': '秒',
            'evaluation_direction': 'asc',
            'description': 'ベースランニングの記録（秒）'
        },
        # 肩力
        {
            'name': 'throw_distance',
            'display_name': '遠投',
            'category': '肩力',
            'unit': 'm',
            'evaluation_direction': 'desc',
            'description': '遠投の記録（メートル）'
        },
        {
            'name': 'pitch_speed',
            'display_name': 'ストレート球速',
            'category': '肩力',
            'unit': 'km/h',
            'evaluation_direction': 'desc',
            'description': 'ストレートの球速（km/h）'
        },
        # 打力
        {
            'name': 'hit_speed',
            'display_name': '打球速度',
            'category': '打力',
            'unit': 'km/h',
            'evaluation_direction': 'desc',
            'description': '打球速度（km/h）'
        },
        {
            'name': 'swing_speed',
            'display_name': 'スイング速度',
            'category': '打力',
            'unit': 'km/h',
            'evaluation_direction': 'desc',
            'description': 'スイング速度（km/h）'
        },
        # 筋力
        {
            'name': 'bench_press',
            'display_name': 'ベンチプレス',
            'category': '筋力',
            'unit': 'kg',
            'evaluation_direction': 'desc',
            'description': 'ベンチプレスの記録（kg）'
        },
        {
            'name': 'squat',
            'display_name': 'スクワット',
            'category': '筋力',
            'unit': 'kg',
            'evaluation_direction': 'desc',
            'description': 'スクワットの記録（kg）'
        }
    ]
    
    for mt_data in measurement_types:
        # 既存のデータがあるかチェック
        existing = MeasurementType.query.filter_by(name=mt_data['name']).first()
        if not existing:
            mt = MeasurementType(**mt_data)
            db.session.add(mt)
            print(f"測定タイプを作成: {mt_data['display_name']} ({mt_data['category']})")
        else:
            # 既存データのカテゴリを更新
            existing.category = mt_data['category']
            print(f"測定タイプを更新: {mt_data['display_name']} -> {mt_data['category']}")
    
    db.session.commit()
    print("測定タイプの初期化が完了しました")

def create_database():
    with app.app_context():
        db.create_all()
        print("Database and tables created!")
        
        # 測定タイプの初期データを作成
        create_measurement_types()

if __name__ == "__main__":
    create_database()

