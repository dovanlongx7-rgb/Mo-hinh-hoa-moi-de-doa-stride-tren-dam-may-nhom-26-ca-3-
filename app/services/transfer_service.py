"""Xác thực lại gắn với giao dịch và chuyển tiền nguyên tử, bền vững qua restart."""
from datetime import datetime, timezone
import hashlib
import json
import secrets
import time
from uuid import uuid4
from app.db.connection import transaction
from app.repositories import account_repository, transfer_repository, user_repository
from app.security.passwords import verify_password
from app.security.permissions import ensure_owner, deny
from app.services.audit_service import record

def fingerprint(intent):
    fields = {k: getattr(intent, k) for k in ('source_account_id','target_account_id','amount')}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(',',':')).encode()).hexdigest()

def proof_digest(proof):
    return hashlib.sha256(proof.encode()).hexdigest()

def create_proof(settings, user, intent):
    with transaction(settings.database_path) as db:
        ensure_owner(account_repository.find(db, intent.source_account_id), user['id'])
        stored = user_repository.find_username(db, user['username'])
        if not verify_password(stored['password_hash'], intent.password):
            deny(401, "REAUTH_PASSWORD_INVALID")
        proof = secrets.token_urlsafe(32)
        db.execute("INSERT INTO reauth_proofs(digest,user_id,session_id,fingerprint,expires_at) VALUES(?,?,?,?,?)",
                   (proof_digest(proof), user['id'], user['session_id'], fingerprint(intent), int(time.time())+settings.proof_seconds))
    return {"reauth_proof": proof, "expires_in": settings.proof_seconds,
            "method": "password_reentry", "note": "Xác thực lại bằng mật khẩu; không phải MFA/OTP."}

def execute(settings, user, intent, key, trace_id):
    digest = fingerprint(intent)
    with transaction(settings.database_path) as db:
        source = account_repository.find(db, intent.source_account_id)
        ensure_owner(source, user['id'])
        previous = transfer_repository.previous(db, user['id'], key)
        if previous:
            if previous['fingerprint'] != digest:
                deny(409, "IDEMPOTENCY_CONFLICT")
            transfer = transfer_repository.find(db, previous['transfer_id'])
            record(db, trace_id, user['id'], "transfer", "ALLOW", "IDEMPOTENT_REPLAY", transfer['id'])
            return transfer, True
        if not intent.reauth_proof:
            deny(403, "REAUTH_REQUIRED")
        proof = db.execute("SELECT * FROM reauth_proofs WHERE digest=?", (proof_digest(intent.reauth_proof),)).fetchone()
        if (not proof or proof['user_id'] != user['id'] or proof['session_id'] != user['session_id']
                or proof['fingerprint'] != digest or proof['expires_at'] <= int(time.time()) or proof['consumed']):
            deny(403, "REAUTH_INVALID")
        if intent.source_account_id == intent.target_account_id:
            deny(422, "SAME_ACCOUNT")
        target = account_repository.find(db, intent.target_account_id)
        if not target:
            deny(422, "TARGET_INVALID")
        if intent.amount > settings.per_transfer_limit:
            deny(422, "PER_TRANSFER_LIMIT")
        day = datetime.now(timezone.utc).date().isoformat()
        if transfer_repository.total_today(db, user['id'], day)+intent.amount > settings.daily_limit:
            deny(422, "DAILY_LIMIT")
        if source['balance'] < intent.amount:
            deny(422, "INSUFFICIENT_FUNDS")
        transfer_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        db.execute("UPDATE accounts SET balance=balance-? WHERE id=?", (intent.amount, source['id']))
        db.execute("UPDATE accounts SET balance=balance+? WHERE id=?", (intent.amount, target['id']))
        db.execute("INSERT INTO transfers(id,user_id,source_account_id,target_account_id,amount,created_at,day_utc) VALUES(?,?,?,?,?,?,?)",
                   (transfer_id,user['id'],source['id'],target['id'],intent.amount,now,day))
        db.execute("INSERT INTO idempotency(user_id,endpoint,key,fingerprint,transfer_id) VALUES(?,'transfer',?,?,?)",
                   (user['id'],key,digest,transfer_id))
        db.execute("UPDATE reauth_proofs SET consumed=1 WHERE digest=?", (proof_digest(intent.reauth_proof),))
        record(db, trace_id, user['id'], "transfer", "ALLOW", "TRANSFER_COMMITTED", transfer_id)
        return transfer_repository.find(db, transfer_id), False
