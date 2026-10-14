from app.db.connection import transaction, connect
from tests.helpers import login, confirmed, intent, transfer, balances

def test_valid_transfer_conserves_money_and_history(bank):
    client, _, s = bank
    before = balances(client)
    h = login(client)
    response = transfer(client,h,confirmed(client,h))
    assert response.status_code == 201
    after = balances(client)
    assert after['ACC_A']==before['ACC_A']-100_000
    assert after['ACC_B']==before['ACC_B']+100_000
    assert sum(after.values()) == sum(before.values())
    history = client.get('/api/accounts/ACC_A/history',headers=h).json()
    assert history[0]['id'] == response.json()['transaction']['id']
    with connect(s.database_path) as db:
        assert db.execute("SELECT COUNT(*) FROM audit_events WHERE reason_code='TRANSFER_COMMITTED'").fetchone()[0] == 1

def test_reauth_required_and_bound_to_amount(bank):
    client, _, _ = bank
    h=login(client); before=balances(client)
    assert transfer(client,h,intent()).json()['error']=='REAUTH_REQUIRED'
    payload=confirmed(client,h)
    assert transfer(client,h,{**payload,'amount':200_000}).json()['error']=='REAUTH_INVALID'
    assert balances(client)==before

def test_proof_expiry_and_session_binding(bank):
    client, _, s = bank
    h=login(client); payload=confirmed(client,h)
    assert transfer(client,login(client),payload).json()['error']=='REAUTH_INVALID'
    with transaction(s.database_path) as db:
        db.execute('UPDATE reauth_proofs SET expires_at=0')
    assert transfer(client,h,payload).json()['error']=='REAUTH_INVALID'

def test_per_transfer_daily_and_balance_limits(bank):
    client, _, _ = bank
    h=login(client)
    assert transfer(client,h,confirmed(client,h,300_001)).json()['error']=='PER_TRANSFER_LIMIT'
    for _ in range(2):
        assert transfer(client,h,confirmed(client,h,300_000)).status_code==201
    assert transfer(client,h,confirmed(client,h,1)).json()['error']=='DAILY_LIMIT'
    c=login(client,'van_c')
    assert transfer(client,c,confirmed(client,c,300_000,'ACC_C','ACC_A')).json()['error']=='INSUFFICIENT_FUNDS'

def test_amount_validation_and_same_account(bank):
    client, _, _ = bank
    h=login(client)
    for amount in (0,-1,True,1.5,'100000'):
        assert transfer(client,h,intent(amount)).status_code==422
    assert transfer(client,h,confirmed(client,h,10,'ACC_A','ACC_A')).json()['error']=='SAME_ACCOUNT'

def test_database_failure_rolls_back_debit_and_proof(bank):
    client, _, s = bank
    h=login(client); payload=confirmed(client,h); before=balances(client)
    with connect(s.database_path) as db:
        db.execute("CREATE TRIGGER fail_credit BEFORE UPDATE ON accounts WHEN NEW.id='ACC_B' BEGIN SELECT RAISE(ABORT,'simulated-db-failure'); END")
    response=transfer(client,h,payload)
    assert response.status_code==500 and response.json()['error']=='INTERNAL_ERROR'
    assert 'simulated-db-failure' not in response.text
    assert balances(client)==before
    with connect(s.database_path) as db:
        assert db.execute('SELECT COUNT(*) FROM transfers').fetchone()[0]==0
        assert db.execute('SELECT consumed FROM reauth_proofs').fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM audit_events WHERE decision='DENY' AND reason_code='INTERNAL_ERROR'").fetchone()[0]==1
