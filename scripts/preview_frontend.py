"""Dựng HTML từ templates và chạy xem trước local với dữ liệu giả.
Chạy: python -m scripts.preview_frontend
Chỉ cần Jinja2; không cần FastAPI/SQLite/seed_data để xem trước.
"""
import argparse
from pathlib import Path
import shutil
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]

def build_preview():
    output = ROOT / 'runtime/frontend-preview'
    output.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(ROOT/'app/templates'), autoescape=select_autoescape(['html']))
    pages = {'login.html':output/'index.html', 'account.html':output/'account/index.html',
             'transfer.html':output/'transfer/index.html', 'history.html':output/'history/index.html'}
    for template, destination in pages.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(env.get_template(template).render(mode='demo'), encoding='utf-8')
    shutil.copytree(ROOT/'app/static', output/'static', dirs_exist_ok=True)
    return output

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5500)
    parser.add_argument('--build-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port phải trong khoảng 1..65535')
    directory = build_preview()
    if args.build_only:
        print('Đã dựng HTML xem trước:', directory)
        return
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
        print(f'Mở http://127.0.0.1:{args.port} bằng trình duyệt. Ctrl+C để dừng.', flush=True)
        print('Mật khẩu chỉ cho xem trước: Demo@2026!', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nĐã dừng xem trước.')

if __name__ == '__main__':
    main()
