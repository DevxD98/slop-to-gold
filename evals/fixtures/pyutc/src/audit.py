from datetime import datetime


def audit_entry(user, action):
    return {"user": user, "action": action, "at": datetime.utcnow().isoformat()}
