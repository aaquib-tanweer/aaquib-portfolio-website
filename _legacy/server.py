"""Portfolio server: SQLite content, password login, and owner-only writes."""
import argparse, getpass, hashlib, hmac, json, os, secrets, sqlite3, time
from pathlib import Path
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('PORTFOLIO_DATA_DIR', ROOT / '.portfolio-data'))
ORIGIN = os.environ.get('PORTFOLIO_ORIGIN', 'http://127.0.0.1:3000').rstrip('/')
ATTEMPTS = {}

@contextmanager
def db():
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    c = sqlite3.connect(DATA / 'portfolio.sqlite3', timeout=10)
    c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, csrf TEXT, expires REAL)')
    seed = json.loads((ROOT / 'content-seed.json').read_text())
    c.execute('INSERT OR IGNORE INTO settings VALUES (?,?)', ('content', json.dumps(seed)))
    c.commit()
    try:
        with c:
            yield c
    finally:
        c.close()

def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

def validate(content):
    if not isinstance(content, dict): raise ValueError('Invalid content.')
    result = {'version': 0}
    for field, limit in [('bio', 5000), ('headline', 200), ('education', 1000), ('skills', 2000)]:
        value = content.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > limit: raise ValueError(f'Invalid {field}.')
        result[field] = value.strip()
    for collection, fields in [('projects', {'id':100, 'title':200, 'preview':2000, 'url':2000, 'tags':300}), ('posts', {'id':100, 'title':200, 'excerpt':1000, 'body':100000, 'date':40})]:
        items = content.get(collection)
        if not isinstance(items, list) or len(items) > 300: raise ValueError(f'Invalid {collection}.')
        result[collection] = []
        ids = set()
        for item in items:
            if not isinstance(item, dict): raise ValueError('Invalid entry.')
            clean = {}
            for key, limit in fields.items():
                value = item.get(key, '')
                if not isinstance(value, str) or len(value) > limit: raise ValueError(f'Invalid {key}.')
                clean[key] = value.strip()
            if not clean['id'] or clean['id'] in ids or not clean['title']: raise ValueError('Each entry needs a unique ID and title.')
            ids.add(clean['id'])
            if collection == 'projects':
                url = urlsplit(clean['url'])
                if clean['url'] and (url.scheme not in ('http', 'https') or not url.netloc or url.username or url.password): raise ValueError('Project links must be HTTP or HTTPS URLs.')
                if not clean['preview']: raise ValueError('Add a project preview.')
            else:
                if not clean['body']: raise ValueError('Add post text.')
                if not isinstance(item.get('published'), bool): raise ValueError('Invalid post status.')
                clean['published'] = item['published']
            result[collection].append(clean)
    return result

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass  # Do not log credentials, tokens, or post bodies.
    def reply(self, status, value, cookie=None):
        raw = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie: self.send_header('Set-Cookie', cookie)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers(); self.wfile.write(raw)
    def session(self, c):
        try:
            cookies = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookies['portfolio_session'].value
        except Exception: return None
        return c.execute('SELECT csrf FROM sessions WHERE token=? AND expires>?', (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith('/api/'):
            with db() as c:
                session = self.session(c)
                if path == '/api/session':
                    configured = bool(c.execute('SELECT 1 FROM settings WHERE key="password"').fetchone())
                    return self.reply(200, {'authenticated':bool(session), 'configured':configured, 'csrf':session[0] if session else None})
                if path in ('/api/content', '/api/admin/content'):
                    if path == '/api/admin/content' and not session: return self.reply(401, {'error':'Please sign in.'})
                    content = json.loads(c.execute('SELECT value FROM settings WHERE key="content"').fetchone()[0])
                    if path == '/api/content': content['posts'] = [p for p in content['posts'] if p['published']]
                    return self.reply(200, content)
            return self.reply(404, {'error':'Not found.'})
        allowed = {'/':'index.html', '/index.html':'index.html', '/admin':'admin.html', '/admin.html':'admin.html', '/app.js':'app.js', '/content.js':'content.js', '/admin.js':'admin.js', '/styles.css':'styles.css', '/assets/luffy.jpeg':'assets/luffy.jpeg'}
        target = allowed.get(path)
        if not target: return self.reply(404, {'error':'Not found.'})
        raw = (ROOT / target).read_bytes()
        mime = 'text/html' if target.endswith('.html') else 'text/javascript' if target.endswith('.js') else 'text/css' if target.endswith('.css') else 'image/jpeg'
        self.send_response(200)
        self.send_header('Content-Type', mime + ('; charset=utf-8' if mime != 'image/jpeg' else ''))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('Cache-Control','no-cache')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers(); self.wfile.write(raw)
    def do_POST(self):
        if self.headers.get('Origin') != ORIGIN: return self.reply(403, {'error':'Request origin rejected.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 2000000: raise ValueError('Request too large or empty.')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict): raise ValueError('Invalid request.')
        except (ValueError, UnicodeError): return self.reply(400, {'error':'Invalid request.'})
        path = urlsplit(self.path).path
        with db() as c:
            if path == '/api/login':
                key = self.client_address[0]
                recent = [t for t in ATTEMPTS.get(key, []) if t > time.time()-900]
                ATTEMPTS[key] = recent
                if len(recent) >= 8: return self.reply(429, {'error':'Too many attempts. Try again in 15 minutes.'})
                row = c.execute('SELECT value FROM settings WHERE key="password"').fetchone()
                if not row: return self.reply(503, {'error':'Owner setup needed. Run npm run setup in your terminal.'})
                password = body.get('password', '')
                if not isinstance(password, str) or len(password)>1000: return self.reply(400, {'error':'Invalid password.'})
                saved = json.loads(row[0]); recent.append(time.time())
                if not hmac.compare_digest(password_hash(password, saved['salt']), saved['hash']): return self.reply(401, {'error':'Incorrect password.'})
                ATTEMPTS[key] = []
                token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                c.execute('DELETE FROM sessions WHERE expires < ?', (time.time(),))
                c.execute('INSERT INTO sessions VALUES (?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), csrf, time.time()+28800))
                c.commit()
                secure = '; Secure' if ORIGIN.startswith('https://') else ''
                return self.reply(200, {'csrf':csrf}, f'portfolio_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800{secure}')
            session = self.session(c)
            if not session: return self.reply(401, {'error':'Please sign in.'})
            if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''), session[0]): return self.reply(403, {'error':'Request rejected. Refresh and sign in again.'})
            if path == '/api/logout':
                cookies = SimpleCookie(self.headers.get('Cookie',''))
                c.execute('DELETE FROM sessions WHERE token=?', (hashlib.sha256(cookies['portfolio_session'].value.encode()).hexdigest(),)); c.commit()
                return self.reply(200, {'ok':True}, 'portfolio_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0')
            if path == '/api/admin/content':
                try: content = validate(body)
                except ValueError as e: return self.reply(400, {'error':str(e)})
                c.execute('BEGIN IMMEDIATE')
                current = json.loads(c.execute('SELECT value FROM settings WHERE key="content"').fetchone()[0])
                if body.get('version') != current['version']: return self.reply(409, {'error':'Content changed in another tab. Reload before editing again.'})
                content['version'] = current['version']+1
                c.execute('UPDATE settings SET value=? WHERE key="content"', (json.dumps(content),)); c.commit()
                return self.reply(200, content)
        return self.reply(404, {'error':'Not found.'})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--setup',action='store_true'); parser.add_argument('--port',type=int,default=3000); args=parser.parse_args()
    if args.setup:
        password = getpass.getpass('Choose your owner password (at least 12 characters): ')
        if len(password)<12: raise SystemExit('Use at least 12 characters.')
        if password != getpass.getpass('Confirm password: '): raise SystemExit('Passwords did not match.')
        salt = secrets.token_hex(16)
        with db() as c:
            c.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('password', json.dumps({'salt':salt,'hash':password_hash(password,salt)})))
            c.execute('DELETE FROM sessions'); c.commit()
        print('Owner login configured. Open /admin to sign in.')
    else:
        host = os.environ.get('PORTFOLIO_HOST','127.0.0.1')
        if host not in ('127.0.0.1','localhost') and not ORIGIN.startswith('https://'): raise SystemExit('Public hosting requires PORTFOLIO_ORIGIN=https://your-domain and an HTTPS reverse proxy.')
        with db(): pass
        print(f'Portfolio: {ORIGIN}\nOwner editor: {ORIGIN}/admin', flush=True)
        ThreadingHTTPServer((host,args.port),Handler).serve_forever()
