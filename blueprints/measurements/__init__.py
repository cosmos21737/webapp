from flask import Blueprint

measurements_bp = Blueprint('measurements', __name__)

from . import routes # 循環参照を避けるため、最後にインポート