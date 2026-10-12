#!/usr/bin/env python3
"""Server kecil untuk Termux: menerima perintah dari terminal Nusa dan menjalankannya.
Hanya library bawaan Python. Hanya mendengarkan 127.0.0.1 dan wajib token."""
import json, os, secrets, shutil, signal, subprocess, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get('NUSA_PORT', '8765'))
TIMEOUT = int(os.environ.get('NUSA_TIMEOUT', '60'))
ORIGINS = {'https://nusa-pro.github.io'} | set(filter(None, os.environ.get('NUSA_ORIGINS', '').split(',')))
TF = os.path.expanduser('~/.nusa-token')
if os.path.exists(TF):
    TOKEN = open(TF).read().strip()
else:
    TOKEN = secrets.token_urlsafe(9)
    open(TF, 'w').write(TOKEN)
    os.chmod(TF, 0o600)
CWD = os.path.expanduser('~')
M = '__NUSA_CWD__'
SH = shutil.which('bash') or shutil.which('sh') or '/bin/sh'

def run(cmd):
    global CWD
    f = tempfile.TemporaryFile()
    script = cmd + '\n__s=$?; printf "\\n' + M + '%s" "$PWD"; exit $__s'
    p = subprocess.Popen(script, shell=True, executable=SH, cwd=CWD, stdin=subprocess.DEVNULL,
                         stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
    note = ''
    try:
        p.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        try: os.killpg(p.pid, signal.SIGKILL)
        except Exception: pass
        note = '\n[waktu habis %ds, perintah dihentikan]' % TIMEOUT
    f.seek(0)
    raw = f.read(200000).decode('utf-8', 'replace')
    f.close()
    if M in raw:
        raw, _, t = raw.rpartition(M)
        t = t.strip()
        if os.path.isdir(t): CWD = t
    return raw.rstrip('\n') + note

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj=None):
        body = json.dumps(obj).encode() if obj is not None else b''
        o = self.headers.get('Origin', '')
        self.send_response(code)
        if o in ORIGINS:
            self.send_header('Access-Control-Allow-Origin', o)
            self.send_header('Vary', 'Origin')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        o = self.headers.get('Origin')
        if o and o not in ORIGINS: return False
        a = self.headers.get('Authorization', '')
        return secrets.compare_digest(a.encode(), ('Bearer ' + TOKEN).encode())

    def do_OPTIONS(self): self._send(204)

    def do_GET(self):
        if not self._auth(): return self._send(401, {'error': 'token salah'})
        self._send(200, {'ok': True, 'cwd': CWD})

    def do_POST(self):
        if not self._auth(): return self._send(401, {'error': 'token salah'})
        try:
            n = int(self.headers.get('Content-Length', 0))
            cmd = str(json.loads(self.rfile.read(n) or b'{}').get('cmd', ''))
        except Exception:
            return self._send(400, {'error': 'permintaan tidak valid'})
        out = run(cmd)
        self._send(200, {'out': out, 'cwd': CWD})

    def log_message(self, *a): pass

if __name__ == '__main__':
    print('Nusa server aktif di http://127.0.0.1:%d' % PORT)
    print('Di Nusa (mode Code) ketik:')
    print('  connect http://127.0.0.1:%d %s' % (PORT, TOKEN))
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
