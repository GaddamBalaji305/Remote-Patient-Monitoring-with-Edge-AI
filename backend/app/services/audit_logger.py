import datetime
from sqlalchemy.orm import Session
from backend.app import models

class AuditLogger:
    """Service recording clinical actions, security events, and patient PII mutations."""
    
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        user_id: int = None,
        ip_address: str = "127.0.0.1",
        details: str = None
    ) -> models.AuditLog:
        """Persists immutable security audit event to the database."""
        now = datetime.datetime.now(datetime.timezone.utc)
        audit_entry = models.AuditLog(
            user_id=user_id,
            action=action,
            timestamp=now,
            ip_address=ip_address,
            details=details
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

audit_logger = AuditLogger()
