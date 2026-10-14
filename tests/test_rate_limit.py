from dataclasses import replace
from fastapi.testclient import TestClient
from app.main import create_app
from tests.helpers import login,confirmed,transfer

def test_transfer_limit_returns_429_and_other_user_unaffected(bank):
    _, _, s=bank
    with TestClient(create_app(replace(s,transfer_requests=2))) as c:
        a=login(c); p=confirmed(c,a)
        assert transfer(c,a,p).status_code==201
        assert transfer(c,a,p).status_code==403  # Proof đã dùng, yêu cầu mới vẫn tính vào limiter.
        response=transfer(c,a,p)
        assert response.status_code==429 and int(response.headers['Retry-After'])>=1
        b=login(c,'van_b')
        assert transfer(c,b,confirmed(c,b,10,'ACC_B','ACC_A')).status_code==201

def test_login_rate_limited_by_ip_not_usernames(bank):
    _, _, s=bank
    with TestClient(create_app(replace(s,login_requests=2))) as c:
        for username in ('van_a','unknown'):
            assert c.post('/api/auth/login',json={'username':username,'password':'wrong'}).status_code==401
        assert c.post('/api/auth/login',json={'username':'other','password':'wrong'}).status_code==429
