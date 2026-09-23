"""Optional, archive-pinned, read-only loopback host. Never imports Book's DB API.

Run with the exact r6 archive extracted locally and the mygpt review checkout on
PYTHONPATH. This is a development surface, not an Android build or production
server. The stock Reader JS is patched only in memory at verified exact anchors.
"""
from __future__ import annotations
import argparse
import hashlib
from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.metadata
import json
from pathlib import Path
import re
import socket
import threading
from urllib.parse import parse_qs, unquote, urlsplit
from .authority import Authority
from .contract import BridgeError, FileReader, canonical, decode, identifier, require

ARCHIVE_SHA256 = '19315e8aeebe2db5cf2f4b55e0a38f550967966af106491dfef67212b430adc1'
MANIFEST_SHA256 = '15d9a1838023e8cf1d05835ddff80da28dde8cc2feaf01e1dbd3f718dff8c388'
STATIC = {'index.html', 'reader.js', 'reader.css', 'math-config.js', 'vendor/tex-svg.js', 'vendor/MathJax-LICENSE.txt'}
WEB = Path(__file__).resolve().parent / 'web'
CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"


def verify_source(root: Path) -> tuple[dict[str, str], dict]:
    root = root.resolve(strict=True)
    manifest_file = root / 'CURRENT_SOURCE_MANIFEST.json'
    require(not manifest_file.is_symlink(), 'UNVERIFIED_R6_MANIFEST')
    data = manifest_file.read_bytes()
    require(hashlib.sha256(data).hexdigest() == MANIFEST_SHA256, 'UNVERIFIED_R6_MANIFEST')
    manifest = decode(data, 1048576)
    expected, verified = {}, 0
    for item in manifest['files']:
        name = item['path']
        require(name not in expected, 'DUPLICATE_MANIFEST_PATH')
        path = root / name
        require(path.resolve().is_relative_to(root), 'UNSAFE_MANIFEST_PATH')
        expected[name] = item['sha256']
        needed = ((name.startswith('coursepacks/') and name.endswith('.json'))
                  or name in {'reader_assets/' + x for x in STATIC})
        if needed:
            require(path.absolute() == path.resolve(strict=True), 'SYMLINK_SOURCE_PATH_FORBIDDEN')
            blob = path.read_bytes()
            require(len(blob) == item['bytes'] and hashlib.sha256(blob).hexdigest() == item['sha256'],
                    'SOURCE_IDENTITY_MISMATCH', 409)
            verified += 1
    require('coursepacks/catalog.json' in expected and all('reader_assets/' + x in expected for x in STATIC),
            'INCOMPLETE_MANIFEST')
    return expected, {'archive_basis_sha256': ARCHIVE_SHA256, 'manifest_sha256': MANIFEST_SHA256,
                      'verified_reader_and_json_members': verified,
                      'installed_android_apk_verified': False}


def patch_reader(script: str) -> str:
    replacements = {
        '  async function openCourse(cid,sid,mode=\'learn\'){':
            '  async function openCourse(cid,sid,mode=\'learn\'){\n    window.BookCompanionBridge?.invalidate("navigation");',
        '  async function loadSection(sid){':
            '  async function loadSection(sid){\n    window.BookCompanionBridge?.invalidate("navigation");',
        '  function renderMode(){':
            '  function renderMode(){\n    window.BookCompanionBridge?.invalidate("mode");',
        '  function paintItems(){':
            '  function paintItems(){\n    window.BookCompanionBridge?.invalidate("page");',
        '    scheduleMath(list);\n  }':
            '    scheduleMath(list);\n    window.BookCompanionBridge?.rendered({course:state.course,section:state.section,mode:state.mode});\n  }',
        "$('back-courses').addEventListener('click',async()=>{try{":
            "$('back-courses').addEventListener('click',async()=>{window.BookCompanionBridge?.invalidate('leave');try{",
    }
    for old, new in replacements.items():
        require(script.count(old) == 1, 'READER_PATCH_ANCHOR_MISMATCH')
        script = script.replace(old, new, 1)
    return script


class Application:
    def __init__(self, root: Path, *, lease_seconds: int = 90, responder=None):
        from mygpt_brain.book_bridge import BookReceiver
        self.root = root.resolve(strict=True)
        self.expected, self.identity = verify_source(self.root)
        self.reader = FileReader(self.root, expected_files=self.expected)
        self.authority = Authority(self.reader, lease_seconds=lease_seconds)
        self.receiver = BookReceiver(self.authority, evidence_kind='ARCHIVE_BACKED_READONLY', responder=responder)
        self.cookie_name = 'book_mygpt_' + self.authority.issuer_id.removeprefix('book-')
        self.host = self.origin = ''
        self.errors = 0
        self.lock = threading.Lock()
        self.static = {}
        for name in STATIC:
            body = (self.root / 'reader_assets' / name).read_bytes()
            if name == 'reader.js':
                body = patch_reader(body.decode('utf-8')).encode('utf-8')
            if name == 'index.html':
                html = body.decode('utf-8')
                anchor = '<script defer src="/reader/reader.js"></script>'
                require(html.count(anchor) == 1, 'READER_PATCH_ANCHOR_MISMATCH')
                html = html.replace(anchor, '<link rel="stylesheet" href="/companion/bridge.css"><script defer src="/companion/projection.js"></script><script defer src="/companion/bridge.js"></script>' + anchor)
                body = html.encode('utf-8')
            self.static[name] = body

    def asset(self, course: str, name: str) -> tuple[bytes, str]:
        self.reader.manifest(course)
        require('\\' not in name and not Path(name).is_absolute(), 'NOT_FOUND', 404)
        path = self.root / 'coursepacks' / course / 'assets' / name
        resolved = path.resolve(strict=True)
        base = self.root / 'coursepacks' / course / 'assets'
        require(path.absolute() == resolved and resolved.is_relative_to(base), 'NOT_FOUND', 404)
        require(resolved.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'), 'NOT_FOUND', 404)
        relative = resolved.relative_to(self.root).as_posix()
        blob = resolved.read_bytes()
        require(len(blob) <= 16777216 and hashlib.sha256(blob).hexdigest() == self.expected.get(relative),
                'SOURCE_ASSET_CHANGED', 409)
        mime = 'image/jpeg' if resolved.suffix.lower() in ('.jpg', '.jpeg') else 'image/' + resolved.suffix.lower()[1:]
        return blob, mime

    def read_api(self, path: str, query: str) -> dict:
        if path == '/api/reader/catalog':
            courses = []
            for cid in self.reader.catalog()['courses']:
                m = self.reader.manifest(cid)
                courses.append({k: v for k, v in m.items() if k not in ('source_inputs', 'sections', 'missing_assets')}
                               | {'missing_asset_count': len(m['missing_assets'])})
            return {'schema': 'reader_catalog_v1', 'courses': courses}
        pieces = path.strip('/').split('/')
        if len(pieces) == 4 and pieces[:3] == ['api', 'reader', 'course']:
            return self.reader.manifest(pieces[3])
        if len(pieces) == 5 and pieces[:3] == ['api', 'reader', 'section']:
            m, s = self.reader.snapshot(pieces[3], pieces[4])
            return s | {'book_version_id': m['book_version_id']}
        if len(pieces) == 6 and pieces[:3] == ['api', 'reader', 'state']:
            require(pieces[5] in ('preview', 'learn', 'review', 'practice'), 'NOT_FOUND', 404)
            m, _ = self.reader.snapshot(pieces[3], pieces[4])
            return {'book_version_id': m['book_version_id'], 'revision': 0, 'note': '', 'answers': {},
                    'completed': False, 'updated_at': None, 'readonly_companion_host': True}
        if len(pieces) == 4 and pieces[:3] == ['api', 'reader', 'search']:
            params = parse_qs(query, keep_blank_values=True, max_num_fields=3)
            require(set(params) <= {'q', 'offset'} and len(params.get('q', [])) == 1
                    and len(params.get('offset', ['0'])) == 1, 'INVALID_SEARCH')
            q = params['q'][0]
            require(0 < len(q) <= 200 and q.strip(), 'INVALID_SEARCH')
            offset_text = params.get('offset', ['0'])[0]
            require(re.fullmatch(r'[0-9]{1,7}', offset_text) is not None, 'INVALID_SEARCH')
            offset, results, cid = int(offset_text), [], pieces[3]
            for meta in self.reader.manifest(cid)['sections']:
                _, section = self.reader.snapshot(cid, meta['id'])
                for record in section['records']:
                    text = record.get('title', '') + ' ' + ''.join(p.get('text', p.get('latex', '')) for p in record['parts'])
                    pos = text.casefold().find(q.strip().casefold())
                    if pos >= 0:
                        results.append({'section_id': meta['id'], 'section_title': meta['title'],
                            'record_id': record['id'], 'source_pdf_page': record.get('source_pdf_page'),
                            'snippet': text[max(0, pos-50):pos+180]})
            return {'scope': 'available_transcribed_text_only', 'total': len(results),
                    'results': results[offset:offset+50], 'next_offset': offset+50 if len(results)>offset+50 else None}
        raise BridgeError('NOT_FOUND', 404)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False
    def __init__(self, application: Application, port: int = 0):
        require(type(port) is int and 0 <= port <= 65535, 'INVALID_PORT')
        self.application = application
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(('127.0.0.1', port), Handler)
        application.host = f'127.0.0.1:{self.server_port}'
        application.origin = 'http://' + application.host
    def process_request(self, request, client_address):
        request.settimeout(5)
        if not self.slots.acquire(blocking=False):
            try:request.sendall(b'HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
            except OSError:pass
            self.shutdown_request(request)
            return
        try:super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise
    def process_request_thread(self, request, client_address):
        try:super().process_request_thread(request, client_address)
        finally:self.slots.release()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'BookReadOnlyBridge/0.1'
    sys_version = ''
    def log_message(self, *_):
        pass  # No URL, cookie, source text, prompt or private learner data in logs.
    @property
    def app(self) -> Application:
        return self.server.application
    def send_error(self, code, message=None, explain=None):
        self.respond(code, {'error': 'HTTP_REQUEST_REJECTED'})
    def respond(self, status: int, value, mime: str = 'application/json; charset=utf-8', cookie: str | None = None):
        blob = value if isinstance(value, bytes) else canonical(value)
        self.send_response(status)
        for key, text in [('Content-Type', mime), ('Content-Length', str(len(blob))),
                          ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'),
                          ('Content-Security-Policy', CSP), ('Referrer-Policy', 'no-referrer'),
                          ('Connection', 'close')]:
            self.send_header(key, text)
        if cookie:self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.close_connection = True
        try:self.wfile.write(blob)
        except (BrokenPipeError, ConnectionResetError):pass  # Expected client cancellation.
    def guard(self, write: bool = False):
        require(len(self.path) <= 4096 and sum(len(k)+len(v) for k,v in self.headers.items()) <= 16384,
                'REQUEST_TOO_LARGE', 413)
        for name in ('Host', 'Origin', 'Content-Length', 'Content-Type', 'Cookie', 'Sec-Fetch-Site', 'X-Book-Companion'):
            require(len(self.headers.get_all(name, [])) <= 1, 'DUPLICATE_HEADER', 400)
        require(self.headers.get('Host') == self.app.host, 'HOST_REJECTED', 403)
        require(not self.headers.get('Transfer-Encoding'), 'TRANSFER_ENCODING_REJECTED', 400)
        site = self.headers.get('Sec-Fetch-Site')
        require(site in (None, 'same-origin', 'none'), 'CROSS_SITE_REJECTED', 403)
        origin = self.headers.get('Origin')
        require(origin is None or origin == self.app.origin, 'ORIGIN_REJECTED', 403)
        if write:
            require(origin == self.app.origin and self.headers.get('X-Book-Companion') == '1',
                    'EXPLICIT_SAME_ORIGIN_REQUIRED', 403)
            require(self.headers.get('Content-Type') == 'application/json', 'JSON_REQUIRED', 415)
    def token(self) -> str:
        raw = self.headers.get('Cookie', '')
        require(len(raw) <= 4096, 'UNAUTHORIZED', 403)
        try:
            cookie = SimpleCookie();cookie.load(raw)
            token = cookie[self.app.cookie_name].value if self.app.cookie_name in cookie else ''
        except CookieError:
            raise BridgeError('UNAUTHORIZED', 403) from None
        self.app.authority.status(token)
        return token
    def body(self) -> dict:
        length = self.headers.get('Content-Length', '')
        require(re.fullmatch(r'[0-9]{1,5}', length) is not None, 'LENGTH_REQUIRED', 411)
        length = int(length)
        require(length <= 8192, 'BODY_TOO_LARGE', 413)
        blob = self.rfile.read(length)
        require(len(blob) == length, 'INCOMPLETE_BODY', 400)
        value = decode(blob, 8192)
        require(type(value) is dict, 'OBJECT_REQUIRED')
        return value
    @staticmethod
    def fields(body: dict, names: set):
        require(set(body) == names, 'INVALID_REQUEST_FIELDS')
    def do_GET(self):
        self.safe(self.get)
    def do_POST(self):
        self.safe(self.post)
    def do_OPTIONS(self):
        self.respond(405, {'error': 'CORS_NOT_ENABLED'})
    def do_HEAD(self):
        self.respond(405, {'error': 'METHOD_NOT_ALLOWED'})
    def safe(self, operation):
        try:operation()
        except (BridgeError, ValueError) as exc:
            from mygpt_brain.book_bridge import ReceiverError
            if isinstance(exc, (BridgeError, ReceiverError)):
                self.respond(exc.status, {'error': exc.code})
            else:self.respond(422, {'error': 'INVALID_REQUEST'})
        except (FileNotFoundError, IsADirectoryError):self.respond(404, {'error': 'NOT_FOUND'})
        except (TimeoutError, socket.timeout):self.respond(408, {'error': 'REQUEST_TIMEOUT'})
        except Exception:
            with self.app.lock:self.app.errors += 1
            self.respond(500, {'error': 'INTERNAL_ERROR'})
    def get(self):
        self.guard()
        parsed = urlsplit(self.path)
        require(not parsed.scheme and not parsed.netloc and not parsed.fragment, 'INVALID_TARGET', 400)
        path = unquote(parsed.path)
        if path == '/favicon.ico':
            return self.respond(204, b'', 'image/x-icon')
        if path in ('/', '/reader', '/reader/'):
            return self.respond(200, self.app.static['index.html'], 'text/html; charset=utf-8')
        if path.startswith('/reader/'):
            name = path[len('/reader/'):]
            require(name in STATIC, 'NOT_FOUND', 404)
            mime = ('application/javascript' if name.endswith('.js') else 'text/css' if name.endswith('.css')
                    else 'text/html' if name.endswith('.html') else 'text/plain') + '; charset=utf-8'
            return self.respond(200, self.app.static[name], mime)
        if path.startswith('/companion/'):
            name = path[len('/companion/'):]
            require(name in ('bridge.js', 'projection.js', 'bridge.css'), 'NOT_FOUND', 404)
            return self.respond(200, (WEB/name).read_bytes(), ('text/css' if name.endswith('.css') else 'application/javascript')+'; charset=utf-8')
        if path.startswith('/reader-assets/'):
            rest = path[len('/reader-assets/'):].split('/', 1)
            require(len(rest) == 2, 'NOT_FOUND', 404)
            blob, mime = self.app.asset(*rest)
            return self.respond(200, blob, mime)
        if path.startswith('/api/reader/'):
            return self.respond(200, self.app.read_api(path, parsed.query))
        if path == '/api/companion/status':
            token = self.token()
            return self.respond(200, {'session': self.app.authority.status(token), 'receiver': self.app.receiver.status(),
                                     'source_identity': self.app.identity, 'unexpected_server_errors': self.app.errors})
        raise BridgeError('NOT_FOUND', 404)
    def post(self):
        self.guard(write=True)
        parsed = urlsplit(self.path)
        require(not parsed.query and not parsed.scheme and not parsed.netloc and not parsed.fragment,
                'INVALID_TARGET', 400)
        path = parsed.path
        allowed = {'/api/companion/'+x for x in ('authorize','select','clear','revoke','explain','cancel')}
        require(path in allowed, 'NOT_FOUND', 404)
        body = self.body()
        if path.endswith('/authorize'):
            self.fields(body, set())
            token, status = self.app.authority.authorize()
            return self.respond(200, {'session': status, 'receiver': self.app.receiver.status(), 'source_identity': self.app.identity},
                cookie=f'{self.app.cookie_name}={token}; HttpOnly; SameSite=Strict; Path=/api/companion; Max-Age={self.app.authority.session_seconds}')
        token = self.token()
        if path.endswith('/select'):
            self.fields(body, {'selection','expected_sha256','sequence','request_id'})
            result = self.app.authority.grant(token, body['selection'], body['expected_sha256'], body['sequence'], body['request_id'])
        elif path.endswith('/clear'):
            self.fields(body, {'sequence','request_id'})
            result = self.app.authority.clear(token, body['sequence'], body['request_id'])
        elif path.endswith('/revoke'):
            self.fields(body, set());self.app.authority.revoke(token)
            return self.respond(200, {'state':'revoked'}, cookie=f'{self.app.cookie_name}=; HttpOnly; SameSite=Strict; Path=/api/companion; Max-Age=0')
        elif path.endswith('/cancel'):
            self.fields(body, {'request_id'});result = self.app.receiver.cancel(token, body['request_id'])
        else:
            self.fields(body, {'ticket','request_id'});result = self.app.receiver.explain(token, body['ticket'], body['request_id'])
        self.respond(200, result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--r6-root', required=True, type=Path)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    for name, version in [('pydantic', '2.13.4'), ('pydantic-ai-slim', '2.46.0')]:
        require(importlib.metadata.version(name) == version, 'SDK_VERSION_MISMATCH')
    application = Application(args.r6_root)
    with Server(application, args.port) as server:
        print(json.dumps({'url': application.origin+'/reader/', 'bind':'127.0.0.1',
                          'mode':'READONLY_ARCHIVE_TESTMODEL_ONLY', 'identity': application.identity}), flush=True)
        try:server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:pass

if __name__ == '__main__':
    main()
