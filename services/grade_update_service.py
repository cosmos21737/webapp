import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import and_
from db_models import db, User, Role, UserRoles

logger = logging.getLogger(__name__)

class GradeUpdateService:
    """学年更新サービス"""
    
    @staticmethod
    def should_update_grades():
        """今日が4月1日かどうかをチェック"""
        today = datetime.now(ZoneInfo('Asia/Tokyo'))
        return today.month == 4 and today.day == 1
    
    @staticmethod
    def get_member_and_manager_roles():
        """部員とマネージャーのロールIDを取得"""
        member_role = Role.query.filter_by(name='member').first()
        manager_role = Role.query.filter_by(name='manager').first()
        return member_role, manager_role
    
    @staticmethod
    def update_grades():
        """学年を更新し、4年生以上を削除"""
        try:
            # 部員とマネージャーのロールを取得
            member_role, manager_role = GradeUpdateService.get_member_and_manager_roles()
            
            if not member_role or not manager_role:
                logger.warning("部員またはマネージャーのロールが見つかりません")
                return False
            
            # 部員とマネージャーのユーザーを取得
            target_users = User.query.join(UserRoles).filter(
                UserRoles.role_id.in_([member_role.id, manager_role.id])
            ).all()
            
            deleted_count = 0
            updated_count = 0
            
            for user in target_users:
                if user.grade is None:
                    continue
                
                # 学年をインクリメント
                new_grade = user.grade + 1
                
                if new_grade >= 4:
                    # 4年生以上は削除
                    logger.info(f"ユーザー {user.name} (学年: {user.grade}) を削除します")
                    db.session.delete(user)
                    deleted_count += 1
                else:
                    # 学年を更新
                    logger.info(f"ユーザー {user.name} の学年を {user.grade} → {new_grade} に更新します")
                    user.grade = new_grade
                    user.updated_at = datetime.now(ZoneInfo('Asia/Tokyo'))
                    updated_count += 1
            
            # データベースに変更を保存
            db.session.commit()
            
            logger.info(f"学年更新完了: {updated_count}件更新, {deleted_count}件削除")
            return True
            
        except Exception as e:
            logger.error(f"学年更新中にエラーが発生しました: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def check_and_update_grades():
        """4月1日かどうかをチェックし、必要に応じて学年を更新"""
        if GradeUpdateService.should_update_grades():
            logger.info("4月1日を検出しました。学年更新を開始します。")
            return GradeUpdateService.update_grades()
        else:
            logger.debug("今日は4月1日ではありません。学年更新はスキップします。")
            return False 