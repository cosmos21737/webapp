from flask import Blueprint, render_template, request
from flask_login import login_required
from flask_security import roles_accepted

from db_models import User

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
    print(team_stats)

    return render_template('team.html',
                           team=members_list, # ここを pagination.items から members_list に変更
                           team_stats=team_stats,
                           )

