from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from fastapi.testclient import TestClient
from app.db.connection import connect
from app.main import create_app
from tests.helpers import login,confirmed,transfer,balances

def test_sequential_replay_and_changed_payload(bank):
    client, _, _ = bank
    h=login(client); p=confirmed(client,h); key=str(uuid4())
    first=transfer(client,h,p,key); before=balances(client)
    replay=transfer(client,h,p,key)
    assert first.status_code==201 and replay.status_code==200
    assert first.json()['transaction']==replay.json()['transaction']
    assert balances(client)==before
    assert transfer(client,h,{**p,'amount':10},key).status_code==409

def test_ten_concurrent_requests_debit_once(bank):
    client, _, s=bank
    h=login(client); p=confirmed(client,h); key=str(uuid4())
    with ThreadPoolExecutor(max_workers=10) as pool:
        responses=list(pool.map(lambda _:transfer(client,h,p,key),range(10)))
    assert sum(r.status_code==201 for r in responses)==1
    assert all(r.status_code in (200,201) for r in responses)
    assert len({r.json()['transaction']['id'] for r in responses})==1
    assert balances(client)=={'ACC_A':900_000,'ACC_B':600_000,'ACC_C':200_000}
    with connect(s.database_path) as db:
        assert db.execute('SELECT COUNT(*) FROM transfers').fetchone()[0]==1

def test_restart_retains_session_key_and_transaction(bank):
    client, _, s=bank
    h=login(client); p=confirmed(client,h); key=str(uuid4())
    first=transfer(client,h,p,key)
    with TestClient(create_app(s)) as restarted:
        replay=transfer(restarted,h,p,key)
        assert replay.status_code==200
        assert replay.json()['transaction']==first.json()['transaction']

def test_same_key_isolated_between_users_and_proof_not_reused(bank):
    client, _, _=bank
    key=str(uuid4()); a=login(client); p=confirmed(client,a)
    assert transfer(client,a,p,key).status_code==201
    assert transfer(client,a,p).json()['error']=='REAUTH_INVALID'
    b=login(client,'van_b'); pb=confirmed(client,b,50_000,'ACC_B','ACC_A')
    assert transfer(client,b,pb,key).status_code==201
