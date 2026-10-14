"""Ứng dụng chạy: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000."""
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import Settings, load_or_create_key
from app.db.connection import initialize
from app.security.rate_limit import RateLimiter
from app.services.audit_service import request_event
from app.routers import auth, accounts, transfers

APP_DIR = Path(__file__).resolve().parent

def create_app(settings: Settings | None = None):
    s = settings or Settings.from_env()
    @asynccontextmanager
    async def lifespan(application):
        initialize(s.database_path)
        application.state.jwt_secret = load_or_create_key(s.key_path)
        yield
    application = FastAPI(title="Ngân hàng giả lập STRIDE", lifespan=lifespan,
                          docs_url='/api-docs', redoc_url=None)
    application.state.settings = s
    application.state.limiter = RateLimiter()
    templates = Jinja2Templates(directory=str(APP_DIR / 'templates'))

    @application.exception_handler(HTTPException)
    async def http_error(request, exc):
        request.state.reason_code = exc.detail if isinstance(exc.detail, str) else 'REQUEST_DENIED'
        return JSONResponse({'error': request.state.reason_code, 'trace_id': getattr(request.state, 'trace_id', '')},
                            status_code=exc.status_code, headers=exc.headers)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        request.state.reason_code = 'INVALID_INPUT'
        return JSONResponse({'error': 'INVALID_INPUT', 'trace_id': getattr(request.state, 'trace_id', '')}, status_code=422)

    @application.exception_handler(Exception)
    async def internal_error(request, exc):
        # Không gửi exception/SQL/config hoặc raw body cho client hay audit.
        return JSONResponse({'error':'INTERNAL_ERROR', 'trace_id':getattr(request.state,'trace_id','')}, status_code=500)

    @application.middleware('http')
    async def guard(request: Request, call_next):
        request.state.trace_id = str(uuid4())
        request.state.principal = 'anonymous'
        request.state.reason_code = 'OK'
        body = bytearray()
        too_large = False
        async for chunk in request.stream():
            if len(body)+len(chunk) > s.max_body_bytes:
                too_large = True
                break
            body.extend(chunk)
        if too_large:
            request.state.reason_code = 'BODY_TOO_LARGE'
            response = JSONResponse({'error':'BODY_TOO_LARGE', 'trace_id':request.state.trace_id}, status_code=413)
        else:
            # Starlette dùng lại body cho tầng router; không đọc/ghi bí mật vào log.
            request._body = bytes(body)
            try:
                response = await call_next(request)
            except Exception:
                request.state.reason_code = 'INTERNAL_ERROR'
                response = JSONResponse({'error':'INTERNAL_ERROR', 'trace_id':request.state.trace_id}, status_code=500)
        response.headers['X-Trace-ID'] = request.state.trace_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'self'" if not request.url.path.startswith('/api-docs') else "default-src 'self' https: 'unsafe-inline'"
        response.headers['Cache-Control'] = 'no-store'
        if request.url.path.startswith('/api/'):
            try:
                request_event(s.database_path, trace_id=request.state.trace_id,
                              principal=request.state.principal, action=f'{request.method} {request.url.path}',
                              decision='ALLOW' if response.status_code < 400 else 'DENY',
                              reason_code=request.state.reason_code if request.state.reason_code != 'OK' else f'HTTP_{response.status_code}')
            except Exception:
                logging.getLogger('bank').error('AUDIT_WRITE_FAILED trace_id=%s', request.state.trace_id)
        return response

    application.mount('/static', StaticFiles(directory=str(APP_DIR / 'static')), name='static')
    application.include_router(auth.router)
    application.include_router(accounts.router)
    application.include_router(transfers.router)

    @application.get('/health')
    def health():
        return {'status':'ok', 'mode':'local-demo'}

    @application.get('/')
    def home(request: Request):
        return templates.TemplateResponse(request=request, name='login.html')

    @application.get('/account')
    def account_page(request: Request):
        return templates.TemplateResponse(request=request, name='account.html')

    @application.get('/transfer')
    def transfer_page(request: Request):
        return templates.TemplateResponse(request=request, name='transfer.html')

    @application.get('/history')
    def history_page(request: Request):
        return templates.TemplateResponse(request=request, name='history.html')
    return application

app = create_app()
