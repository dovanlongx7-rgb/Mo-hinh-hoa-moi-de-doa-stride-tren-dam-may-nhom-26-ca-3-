from tests.helpers import login, intent, transfer, balances

def test_other_account_and_history_forbidden(bank):
    client, _, _ = bank
    h = login(client)
    assert client.get('/api/accounts/ACC_A', headers=h).status_code == 200
    for path in ('/api/accounts/ACC_B','/api/accounts/ACC_B/history','/api/accounts/UNKNOWN'):
        response = client.get(path, headers=h)
        assert response.status_code == 403
        assert '500000' not in response.text

def test_source_owner_checked_without_proof(bank):
    client, _, _ = bank
    before = balances(client)
    response = transfer(client,login(client),intent(100_000,'ACC_B','ACC_A'))
    assert response.status_code == 403 and response.json()['error']=='ACCOUNT_ACCESS_DENIED'
    assert balances(client) == before

def test_customer_cannot_read_operator_audit(bank):
    client, _, _ = bank
    assert client.get('/api/admin/audit',headers=login(client)).status_code == 403

def test_unknown_fields_cannot_override_identity_or_role(bank):
    client, _, _ = bank
    payload = {**intent(), 'user_id':'U_B','role':'operator'}
    assert transfer(client,login(client),payload).status_code == 422
