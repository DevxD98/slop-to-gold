from datetime import datetime


def build_report(rows):
    """Return a report dict stamped with the creation time."""
    return {"created_at": datetime.utcnow(), "rows": list(rows), "count": len(rows)}
