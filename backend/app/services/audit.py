from sqlalchemy.orm import Session
from app.db.models import AuditLog

def log_action(db: Session, user_id: str, action: str, entity_type: str, entity_id: str, reason: str = ""):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason
    )
    db.add(log)
    # MUST COMMIT in caller to maintain atomicity!
