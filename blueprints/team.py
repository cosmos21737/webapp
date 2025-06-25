from flask import Blueprint, render_template, request
from flask_login import login_required
from flask_security.decorators import roles_accepted

from db_models import User, MeasurementType

from services import services

team_bp = Blueprint('team', __name__)


@team_bp.route('/team')
@login_required
@roles_accepted("administer", "member", "coach")
def team():

    # クエリ実行 (team_statusがTrueのユーザーのみ取得) - ページネーションを削除し、全件取得
    members_list = User.query.filter_by(team_status=True).all() # .order_by(sort_column) も不要

    #チームの偏差値を計算
    team_stats = services.calculate_statuses()

    # 測定項目を明示的な順序で取得
    measurement_types = MeasurementType.query.order_by(MeasurementType.id).all()

    # 各メンバーの全種目偏差値を取得
    member_stddevs = {}
    for member in members_list:
        member_stddevs[member.user_id] = services.calculate_rankings(member.user_id)

    return render_template('team.html',
                           team=members_list, # ここを pagination.items から members_list に変更
                           team_stats=team_stats,
                           member_stddevs=member_stddevs,
                           measurement_types=measurement_types
                           )

