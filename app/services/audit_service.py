"""Audit chỉ dùng trường cho phép. Audit giao dịch ghi cùng transaction DB."""
from datetime import datetime, timezone
from app.db.connection import transaction, connect

def record(db, trace_id, principal, action, decision, reason_code, transaction_id=None):
    db.execute("INSERT INTO audit_events(timestamp,trace_id,principal,action,decision,reason_code,transaction_id) VALUES(?,?,?,?,?,?,?)",
               (datetime.now(timezone.utc).isoformat(), trace_id, principal, action, decision, reason_code, transaction_id))

def request_event(path, **fields):
    with transaction(path) as db:
        record(db, **fields)

def list_events(path):
    with connect(path) as db:
        return [dict(r) for r in db.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 200")]
