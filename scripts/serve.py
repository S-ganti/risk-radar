"""Local dashboard + bounded, read-only market refresh. Binds loopback only."""
import json
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from market_quotes import ROOT, OUT, refresh

lock=threading.Lock()
last_attempt=0
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
    def do_GET(self):
        global last_attempt
        if self.path.split('?')[0]!='/api/market-quotes': return super().do_GET()
        if not lock.acquire(False):
            self.send_error(409,'Refresh already running');return
        try:
            if time.monotonic()-last_attempt>300 or not OUT.exists():
                last_attempt=time.monotonic();refresh()
            payload=OUT.read_bytes()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(payload)
        except Exception:
            self.send_error(503,'Market refresh failed; saved snapshot may still be available')
        finally: lock.release()

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8768);args=p.parse_args()
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
