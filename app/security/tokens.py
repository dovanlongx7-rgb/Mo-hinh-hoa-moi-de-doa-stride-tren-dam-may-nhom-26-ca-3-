"""JWT HS256 cho demo local. Chỉ chấp nhận thuật toán đã định sẵn."""
import time
import jwt

ISSUER = "stride-local-bank"
AUDIENCE = "stride-local-client"

def issue_token(user_id, session_id, secret, lifetime):
    now = int(time.time())
    return jwt.encode({"sub": user_id, "jti": session_id, "iat": now, "exp": now+lifetime,
                       "iss": ISSUER, "aud": AUDIENCE}, secret, algorithm="HS256")

def decode_token(token, secret):
    return jwt.decode(token, secret, algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE,
                      options={"require": ["sub", "jti", "iat", "exp", "iss", "aud"]})
