"""Schema SQLite. D1, D2, D4 là các kho logic trong cùng một file DB demo."""
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
 full_name TEXT NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('customer','operator')) DEFAULT 'customer'
);
CREATE TABLE IF NOT EXISTS accounts (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 balance INTEGER NOT NULL CHECK(balance >= 0)
);
CREATE TABLE IF NOT EXISTS sessions (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 expires_at INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reauth_proofs (
 digest TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 session_id TEXT NOT NULL REFERENCES sessions(id),
 fingerprint TEXT NOT NULL, expires_at INTEGER NOT NULL,
 consumed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS transfers (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 source_account_id TEXT NOT NULL REFERENCES accounts(id),
 target_account_id TEXT NOT NULL REFERENCES accounts(id),
 amount INTEGER NOT NULL CHECK(amount > 0),
 created_at TEXT NOT NULL, day_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency (
 user_id TEXT NOT NULL REFERENCES users(id), endpoint TEXT NOT NULL,
 key TEXT NOT NULL, fingerprint TEXT NOT NULL,
 transfer_id TEXT NOT NULL REFERENCES transfers(id),
 PRIMARY KEY (user_id, endpoint, key)
);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
 trace_id TEXT NOT NULL, principal TEXT NOT NULL,
 action TEXT NOT NULL, decision TEXT NOT NULL,
 reason_code TEXT NOT NULL, transaction_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_accounts_owner ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_transfer_day ON transfers(user_id, day_utc);
"""
