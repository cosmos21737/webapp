import math

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from flask_security import roles_required, roles_accepted
from sqlalchemy import func

from db_models import db, User, MeasurementRecord

team_bp = Blueprint('team', __name__)


@team_bp.route('/team')
@login_required
@roles_accepted("administer", "member", "coach")
def team():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    sort_by = 'grade'
    sort_order = 'asc'

    # ソート処理
    sort_column = User.grade
    sort_column = sort_column.desc() if sort_order == 'desc' else sort_column.asc()

    # クエリ実行 (team_statusがTrueのユーザーのみ取得)
    pagination = User.query.filter_by(team_status=True).order_by(sort_column).paginate(page=page, per_page=per_page)
    members_list = pagination.items

    #チームの偏差値を計算
    team_stats = calculate_team_average_standard_score()

    return render_template('team.html',
                           team=members_list,
                           team_stats=team_stats,
                           pagination=pagination,
                           sort_by=sort_by,
                           sort_order=sort_order)


def calculate_team_average_standard_score():
    # 全ユーザー（全体）の統計情報を計算
    overall_stats = {}
    metrics = {
        'run_50m': True,  # 小さい方が良い指標
        'base_running': True,
        'long_throw': False,  # 大きい方が良い指標
        'straight_speed': False,
        'hit_speed': False,
        'swing_speed': False,
        'bench_press': False,
        'squat': False
    }

    # チームメンバー（team_status=True）の平均値を計算
    team_avg_values = {}
    for metric, asc in metrics.items():
        # チームメンバーの平均値
        subquery = db.session.query(
            MeasurementRecord.user_id,
            func.min(getattr(MeasurementRecord, metric)).label("value") if asc
            else func.max(getattr(MeasurementRecord, metric)).label("value")
        ).join(
            User, MeasurementRecord.user_id == User.user_id
        ).filter(
            User.team_status == True,
            MeasurementRecord.status == 'approved'
        ).group_by(
            MeasurementRecord.user_id
        ).subquery()

        # 合計と件数を取得
        result = db.session.query(
            func.sum(subquery.c.value),
            func.count()
        ).one()

        # 平均値を Python 側で計算
        total_sum, user_count = result
        team_avg = total_sum / user_count if user_count else None

        team_avg_values[metric] = team_avg

        # 全ユーザーの統計情報（平均、標準偏差）
        # サブクエリ：各ユーザーの min or max 値を取得
        subquery = db.session.query(
            MeasurementRecord.user_id,
            func.min(getattr(MeasurementRecord, metric)).label("value") if asc
            else func.max(getattr(MeasurementRecord, metric)).label("value")
        ).join(
            User, MeasurementRecord.user_id == User.user_id
        ).filter(
            MeasurementRecord.status == 'approved'
        ).group_by(
            MeasurementRecord.user_id
        ).subquery()

        # 値を全件取得
        values = db.session.query(subquery.c.value).all()
        values = [v[0] for v in values if v[0] is not None]

        # 平均と標準偏差を Python で計算
        if values:
            avg = sum(values) / len(values)
            stddev = math.sqrt(sum((x - avg) ** 2 for x in values) / len(values))  # 母標準偏差（N分の1）
        else:
            avg = stddev = None

        overall = {
            'avg': avg,
            'stddev': stddev
        }

        if overall:
            values = [int(v) if isinstance(v, str) and v.isdigit() else v for v in values]
            if values:
                overall_avg = sum(values) / len(values)
                variance = sum((x - overall_avg) ** 2 for x in values) / len(values)
                overall_stddev = math.sqrt(variance)

                overall_stats[metric] = {
                    'avg': overall_avg,
                    'stddev': overall_stddev,
                    'count': len(values)
                }

    # チーム平均の偏差値を計算
    results = {}
    for metric in metrics.keys():
        team_avg = team_avg_values.get(metric)
        overall = overall_stats.get(metric)

        if team_avg is not None and overall and overall['stddev'] != 0:
            std_score = 50 + 10 * (team_avg - overall['avg']) / overall['stddev']
            results[metric] = {
                'team_avg': round(team_avg, 2),
                'overall_avg': round(overall['avg'], 2),
                'overall_stddev': round(overall['stddev'], 2),
                'standard_score': round(std_score, 1),
                'overall_participants': overall['count']
            }
        else:
            results[metric] = {
                'team_avg': round(team_avg, 2) if team_avg is not None else None,
                'overall_avg': None,
                'overall_stddev': None,
                'standard_score': None,
                'overall_participants': 0
            }

    return results