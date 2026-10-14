"""Thực nghiệm độc lập bằng TestClient, DB tạm, không gửi đến ngân hàng thật.
Chạy: python -m scripts.run_experiments --repeat 10
CSV/JSON chỉ chứa trạng thái và số dư; token/mật khẩu/proof không được xuất.
"""
import argparse
import csv
import json
import secrets
import platform
import hashlib
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from datetime import datetime, timezone
from dataclasses import replace
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.config import Settings, ROOT
from app.main import create_app
from app.db.connection import connect
from scripts.seed_data import seed

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeat', type=int, default=10)
    parser.add_argument('--output-root', type=Path, default=ROOT/'evidence')
    args = parser.parse_args()
    if not 1 <= args.repeat <= 100:
        parser.error('--repeat phải trong khoảng 1..100')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(3)
    result_dir = args.output_root/'results'/run_id
    log_dir = args.output_root/'logs'/run_id
    result_dir.mkdir(parents=True)
    log_dir.mkdir(parents=True)
    rows, all_logs = [], []
    for run in range(1, args.repeat+1):
        with TemporaryDirectory(prefix='stride-experiment-') as directory:
            path=Path(directory)
            settings=replace(Settings(),database_path=path/'bank.sqlite3',key_path=path/'key',login_requests=1000,transfer_requests=1000)
            password=secrets.token_urlsafe(24)
            seed(settings.database_path,password)
            def snapshot():
                with connect(settings.database_path) as db:
                    return {r['id']:r['balance'] for r in db.execute('SELECT id,balance FROM accounts ORDER BY id')}
            def measure(test_id, action, expected, predicate=None):
                before=snapshot(); t=perf_counter()
                response=action(); elapsed=(perf_counter()-t)*1000; after=snapshot()
                passed=response.status_code==expected and (predicate(response,before,after) if predicate else True)
                row={'test_id':test_id,'run':run,'expected_http':expected,'actual_http':response.status_code,
                     'latency_ms':round(elapsed,3),'balance_before':json.dumps(before),
                     'balance_after':json.dumps(after),'passed':passed,'trace_id':response.headers.get('X-Trace-ID','')}
                rows.append(row)
                return response
            with TestClient(create_app(settings)) as client:
                login=measure('AC01_VALID_LOGIN',lambda:client.post('/api/auth/login',json={'username':'van_a','password':password}),200)
                h={'Authorization':'Bearer '+login.json()['access_token']}
                measure('AC01_WRONG_PASSWORD',lambda:client.post('/api/auth/login',json={'username':'van_a','password':'wrong-password'}),401,lambda r,b,a:b==a)
                measure('AC02_BAD_JSON_NO_ECHO',lambda:client.post('/api/auth/login',content='{"password":"sensitive-input"',headers={'Content-Type':'application/json'}),422,
                        lambda r,b,a:b==a and 'sensitive-input' not in r.text and 'Traceback' not in r.text)
                measure('AC05_BODY_LIMIT',lambda:client.post('/api/auth/login',content='x'*(settings.max_body_bytes+1)),413,lambda r,b,a:b==a)
                measure('AC01_INVALID_TOKEN',lambda:client.get('/api/accounts',headers={'Authorization':'Bearer invalid-token'}),401,
                        lambda r,b,a:b==a)
                measure('AC02_VALID_OWNER',lambda:client.get('/api/accounts/ACC_A',headers=h),200)
                measure('AC02_OTHER_OWNER',lambda:client.get('/api/accounts/ACC_B',headers=h),403,lambda r,b,a:b==a)
                intent={'source_account_id':'ACC_A','target_account_id':'ACC_B','amount':100_000}
                proof=client.post('/api/transfers/reauth',headers=h,json={**intent,'password':password})
                assert proof.status_code==200, 'Không tạo được bằng chứng xác thực lại.'
                payload={**intent,'reauth_proof':proof.json()['reauth_proof']}; key=str(uuid4())
                measure('AC04_TAMPER_AFTER_REAUTH',lambda:client.post('/api/transfers',headers={**h,'Idempotency-Key':str(uuid4())},json={**payload,'amount':200_000}),403,
                        lambda r,b,a:b==a and r.json().get('error')=='REAUTH_INVALID')
                measure('AC05_ROLE_INJECTION',lambda:client.post('/api/transfers',headers={**h,'Idempotency-Key':str(uuid4())},json={**payload,'role':'operator','user_id':'U_B'}),422,lambda r,b,a:b==a)
                def send():
                    return client.post('/api/transfers',headers={**h,'Idempotency-Key':key},json=payload)
                before=snapshot();t=perf_counter()
                with ThreadPoolExecutor(max_workers=10) as pool:
                    responses=list(pool.map(lambda _:send(),range(10)))
                after=snapshot(); ids={r.json().get('transaction',{}).get('id') for r in responses}
                passed=(sum(r.status_code==201 for r in responses)==1 and all(r.status_code in (200,201) for r in responses)
                        and len(ids)==1 and None not in ids and after['ACC_A']==before['ACC_A']-100_000
                        and after['ACC_B']==before['ACC_B']+100_000 and sum(after.values())==sum(before.values()))
                rows.append({'test_id':'AC03_CONCURRENT_10','run':run,'expected_http':'1x201+9x200',
                             'actual_http':','.join(str(r.status_code) for r in responses),'latency_ms':round((perf_counter()-t)*1000,3),
                             'balance_before':json.dumps(before),'balance_after':json.dumps(after),'passed':passed,
                             'trace_id':','.join(r.headers.get('X-Trace-ID','') for r in responses)})
                measure('AC03_REPLAY',send,200,lambda r,b,a:b==a)
                measure('AC03_CHANGED_PAYLOAD',lambda:client.post('/api/transfers',headers={**h,'Idempotency-Key':key},json={**payload,'amount':200_000}),409,lambda r,b,a:b==a)
                measure('AC04_MISSING_REAUTH',lambda:client.post('/api/transfers',headers={**h,'Idempotency-Key':str(uuid4())},json=intent),403,lambda r,b,a:b==a)
                measure('AC05_CUSTOMER_ADMIN',lambda:client.get('/api/admin/audit',headers=h),403)
                # Instance mới giữ cùng DB/khóa nhưng có limiter sạch: kiểm chứng restart và rate-limit.
                with TestClient(create_app(replace(settings,transfer_requests=2))) as restarted:
                    def repeat():
                        return restarted.post('/api/transfers',headers={**h,'Idempotency-Key':key},json=payload)
                    measure('AC03_AFTER_RESTART',repeat,200,lambda r,b,a:b==a)
                    measure('AC05_WITHIN_RATE',repeat,200,lambda r,b,a:b==a)
                    measure('AC05_OVER_RATE',repeat,429,lambda r,b,a:b==a)
            with connect(settings.database_path) as db:
                events=[dict(r) for r in db.execute('SELECT * FROM audit_events ORDER BY id')]
                serialized=json.dumps(events)
                financial=[r for r in events if r['reason_code']=='TRANSFER_COMMITTED']
                denied=next(r for r in rows if r['run']==run and r['test_id']=='AC02_OTHER_OWNER')
                audit_ok=(len(financial)==1 and financial[0]['transaction_id'] in ids
                          and any(e['trace_id']==denied['trace_id'] and e['decision']=='DENY' and e['reason_code']=='ACCOUNT_ACCESS_DENIED' for e in events)
                          and all(secret not in serialized for secret in (password,h['Authorization'].split()[1],payload['reauth_proof'])))
                state=snapshot()
                rows.append({'test_id':'AC06_AUDIT_CORRELATION_NO_SECRETS','run':run,'expected_http':'N/A (DB assertion)',
                             'actual_http':'N/A (DB assertion)','latency_ms':0,'balance_before':json.dumps(state),
                             'balance_after':json.dumps(state),'passed':audit_ok,'trace_id':financial[0]['trace_id'] if financial else ''})
                all_logs.extend({'run':run,**event} for event in events)
    with (result_dir/'results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (result_dir/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    with (log_dir/'audit.jsonl').open('w',encoding='utf-8') as f:
        for event in all_logs:f.write(json.dumps(event,ensure_ascii=False)+'\n')
    metadata={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'run_id':run_id,'python':platform.python_version(),
              'platform':platform.platform(),'repeat':args.repeat,'passed':sum(r['passed'] for r in rows),'total':len(rows),
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('app','scripts') for p in sorted((ROOT/folder).rglob('*.py'))},
              'mode':'TestClient in-process; DB tạm mới mỗi lượt; không dùng HTTP mạng thật',
              'packages':{name:version(name) for name in ('fastapi','starlette','pydantic','httpx','PyJWT','argon2-cffi')}}
    (result_dir/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Đạt {metadata['passed']}/{metadata['total']} kết quả; thư mục: {result_dir}")
    if metadata['passed']!=metadata['total']:
        raise SystemExit(1)

if __name__=='__main__':
    main()
