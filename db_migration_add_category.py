#!/usr/bin/env python3
"""
MeasurementTypeテーブルにcategoryカラムを追加するマイグレーションスクリプト
"""

import sqlite3
import os

def migrate_add_category():
    """MeasurementTypeテーブルにcategoryカラムを追加"""
    
    # データベースファイルのパス
    db_path = 'instance/baseball_team.db'
    
    if not os.path.exists(db_path):
        print(f"データベースファイルが見つかりません: {db_path}")
        return
    
    try:
        # データベースに接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 現在のテーブル構造を確認
        cursor.execute("PRAGMA table_info(measurement_types)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category' not in columns:
            # categoryカラムを追加
            cursor.execute("ALTER TABLE measurement_types ADD COLUMN category TEXT")
            print("categoryカラムを追加しました")
            
            # 既存データにカテゴリを設定（実際のデータに合わせて）
            category_mapping = {
                'run_50m': '走力',           # 50m走
                'base_running': '走力',      # ベースランニング
                'throw_distance': '肩力',    # 遠投
                'pitch_speed': '肩力',       # ストレート球速
                'hit_speed': '打力',         # 打球速度
                'swing_speed': '打力',       # スイング速度
                'bench_press': '筋力',       # ベンチプレス
                'squat': '筋力'              # スクワット
            }
            
            for name, category in category_mapping.items():
                cursor.execute(
                    "UPDATE measurement_types SET category = ? WHERE name = ?",
                    (category, name)
                )
                print(f"更新: {name} -> {category}")
            
            print("既存データにカテゴリを設定しました")
        else:
            print("categoryカラムは既に存在します")
        
        # 変更をコミット
        conn.commit()
        print("マイグレーションが完了しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_category() 