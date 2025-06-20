from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from flask_security import roles_required, roles_accepted
from sqlalchemy import func

from db_models import db, User, MeasurementRecord, News

news_bp = Blueprint('news', __name__)


@news_bp.route('/')
@login_required
def news():
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 1ページあたりの項目数
    news_posts_pagination = News.query.order_by(News.post_date.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('news.html', news_posts_pagination=news_posts_pagination)


@news_bp.route('/post', methods=['POST'])
@login_required
@roles_accepted("administer", "coach", "director")
def post_news():

    title = request.form['title']
    content = request.form['content']
    new_news = News(title=title, content=content)
    db.session.add(new_news)
    db.session.commit()
    flash('お知らせが投稿されました。')
    return redirect(url_for('news.news'))

@news_bp.route('/delete/<int:news_id>', methods=['POST'])
@login_required
@roles_accepted("administer", "coach", "director")
def delete_news(news_id):
    news_to_delete = News.query.get_or_404(news_id)
    db.session.delete(news_to_delete)
    db.session.commit()
    flash('お知らせが削除されました。')
    return redirect(url_for('news.news'))