import json
import time
import jwt
from app.db.connection import connect
from app.security.tokens import ISSUER, AUDIENCE
from tests.helpers import login, confirmed
from tests.conftest import PASSWORD

def test_login_and_password_hash(bank):
    client, app, s = bank
    headers = login(client)
    assert client.get('/api/auth/me', headers=headers).json()['full_name'] == 'Nguyễn Văn A'
    with connect(s.database_path) as db:
        stored = db.execute('SELECT password_hash FROM users LIMIT 1').fetchone()[0]
    assert stored.startswith('$argon2id$') and PASSWORD not in stored

def test_wrong_password_and_missing_session(bank):
    client, _, _ = bank
    response = client.post('/api/auth/login', json={'username':'van_a','password':'wrong'})
    assert response.status_code == 401
    assert client.get('/api/accounts').status_code == 401

def test_invalid_signature_expiry_audience_and_algorithm(bank):
    client, app, _ = bank
    headers = login(client)
    good = headers['Authorization'].split()[1]
    payload = jwt.decode(good, options={'verify_signature':False})
    variants = [jwt.encode(payload, 'different-key-that-is-long-enough-12345678', algorithm='HS256'),
                jwt.encode({**payload,'exp':int(time.time())-10},app.state.jwt_secret,algorithm='HS256'),
                jwt.encode({**payload,'aud':'wrong'},app.state.jwt_secret,algorithm='HS256'),
                jwt.encode({**payload,'iss':'wrong'},app.state.jwt_secret,algorithm='HS256'),
                jwt.encode(payload,'',algorithm='none')]
    for token in variants:
        assert client.get('/api/accounts', headers={'Authorization':'Bearer '+token}).status_code == 401

def test_logout_revokes_session(bank):
    client, _, _ = bank
    headers = login(client)
    assert client.post('/api/auth/logout', headers=headers).status_code == 200
    assert client.get('/api/accounts', headers=headers).status_code == 401

def test_audit_contains_denials_but_no_credentials(bank):
    client, _, s = bank
    headers = login(client)
    payload = confirmed(client, headers)
    client.get('/api/accounts/ACC_B',headers=headers)
    with connect(s.database_path) as db:
        rows = [dict(r) for r in db.execute('SELECT * FROM audit_events')]
    audit = json.dumps(rows)
    for secret in (PASSWORD, headers['Authorization'].split()[1],payload['reauth_proof']):
        assert secret not in audit
    assert any(r['decision']=='DENY' and r['reason_code']=='ACCOUNT_ACCESS_DENIED' for r in rows)

def test_bad_json_has_no_echo_or_stack_trace(bank):
    client, _, _ = bank
    response = client.post('/api/auth/login', content='{"password":"sensitive-input"', headers={'Content-Type':'application/json'})
    assert response.status_code == 422
    assert 'sensitive-input' not in response.text and 'Traceback' not in response.text

def test_body_limit(bank):
    client, _, s = bank
    response = client.post('/api/auth/login', content='x'*(s.max_body_bytes+1))
    assert response.status_code == 413
