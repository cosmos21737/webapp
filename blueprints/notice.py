from flask import request, Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from flask_security import roles_accepted
from db_models import db, User, MeasurementRecord, MeasurementType

notice_bp = Blueprint('notice', __name__)


@notice_bp.route('/my/notice')
@login_required
@roles_accepted("administer", "member", "manager", "coach")
def notice():
    user_id = current_user.get_id()
    user = User.query.get(user_id)
    measurement_types = MeasurementType.query.all()

    if current_user.has_role("member"):
        records = MeasurementRecord.query.filter_by(user_id=user_id, status='draft').all()
    if current_user.has_role("coach"):
        records = MeasurementRecord.query.filter_by(status='pending_coach').all()
    if current_user.has_role("manager"):
        records = MeasurementRecord.query.filter_by(status='rejected').all()


    return render_template('notice.html',
                           user=user,
                           records=records,
                           measurement_types=measurement_types
                           )


@notice_bp.route("/approve_records", methods=["POST"])
@login_required
@roles_accepted("administer", "member", "manager", "coach")
def approve_records():
    selected_record_ids = request.form.getlist("record_ids")  # 選択されたIDのリスト
    action = request.form.get('action')
    comment = request.form.get('comment')

    if selected_record_ids:
        # データベース更新処理
        records = MeasurementRecord.query.filter(MeasurementRecord.id.in_(selected_record_ids)).all()
        for record in records:
            if action == "reject":
                record.status = 'rejected'
                record.comment = record.user.name + "：" + comment
            elif current_user.has_role("member"):
                record.status = 'pending_coach'  # 承認フラグを更新
            elif current_user.has_role("coach"):
                record.status = 'approved'
            elif current_user.has_role("manager"):
                db.session.delete(record)
        db.session.commit()

    return redirect(url_for("notice.notice"))
