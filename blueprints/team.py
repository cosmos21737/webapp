import math

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from flask_security import roles_required, roles_accepted
from sqlalchemy import func

from db_models import db, User, MeasurementRecord, MeasurementType

from services import services

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
    team_stats = services.calculate_statuses()
    print(team_stats)

    return render_template('team.html',
                           team=members_list,
                           team_stats=team_stats,
                           pagination=pagination,
                           sort_by=sort_by,
                           sort_order=sort_order)

