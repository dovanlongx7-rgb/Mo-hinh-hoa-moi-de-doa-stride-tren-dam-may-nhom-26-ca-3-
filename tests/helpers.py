from uuid import uuid4
from tests.conftest import PASSWORD

def login(client, username='van_a'):
    response = client.post('/api/auth/login', json={'username':username,'password':PASSWORD})
    assert response.status_code == 200, response.text
    return {'Authorization':'Bearer '+response.json()['access_token']}

def intent(amount=100_000, source='ACC_A', target='ACC_B'):
    return {'source_account_id':source,'target_account_id':target,'amount':amount}

def confirmed(client, headers, amount=100_000, source='ACC_A', target='ACC_B'):
    payload = intent(amount, source, target)
    response = client.post('/api/transfers/reauth', headers=headers, json={**payload,'password':PASSWORD})
    assert response.status_code == 200, response.text
    return {**payload, 'reauth_proof':response.json()['reauth_proof']}

def transfer(client, headers, payload, key=None):
    return client.post('/api/transfers', headers={**headers,'Idempotency-Key':key or str(uuid4())}, json=payload)

def balances(client):
    result = {}
    for username in ('van_a','van_b','van_c'):
        for account in client.get('/api/accounts', headers=login(client,username)).json():
            result[account['id']] = account['balance']
    return result
