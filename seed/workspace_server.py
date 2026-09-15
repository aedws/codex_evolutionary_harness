"""Owner-configured loopback wiki. No default credentials or anonymous source access."""
import argparse
from contextlib import closing
from html import escape
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
from urllib.parse import parse_qs,urlsplit
import workspace as w
import workspace_view as ui


def server(root,port=0):
    workspace=w.Workspace(root)
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup();self.connection.settimeout(10)
        def log_message(self,*args):pass  # No credentials, object IDs or query strings in logs.
        def boundary(self):
            expected='127.0.0.1:'+str(self.server.server_port)
            w.need(self.client_address[0]=='127.0.0.1' and self.headers.get('Host')==expected,'Loopback host required')
            if self.command=='POST':w.need(self.headers.get('Origin')=='http://'+expected,'Origin denied')
        def send(self,status,body,mime='text/html; charset=utf-8',cookie=None):
            raw=body.encode() if isinstance(body,str) else body;self.send_response(status)
            for k,v in [('Content-Type',mime),('Cache-Control','private, no-store'),('X-Content-Type-Options','nosniff'),('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'"),('Content-Length',str(len(raw)))]:self.send_header(k,v)
            if cookie:self.send_header('Set-Cookie',cookie)
            self.end_headers();self.wfile.write(raw)
        def token(self):
            cookies=SimpleCookie();cookies.load(self.headers.get('Cookie',''));return cookies['workspace_session'].value if 'workspace_session' in cookies else ''
        def accounts(self):
            with closing(workspace.connect()) as db:config=workspace.config(db)
            return w.component('wiki_access').Accounts(w.local(workspace.root,config['accounts']),config['roles'],w.sha(w.encoded(config)))
        def do_GET(self):
            try:
                self.boundary();url=urlsplit(self.path);args={k:v[-1] for k,v in parse_qs(url.query).items()}
                with closing(workspace.connect()) as db:offline=workspace.config(db)['access_mode']=='loopback_read_only'
                if url.path=='/login':
                    w.need(not offline,'Offline read mode has no login')
                    self.send(200,'<!doctype html><html lang="ko"><meta name="viewport" content="width=device-width,initial-scale=1"><title>운영 위키 로그인</title><form method="post" action="/login"><label>계정 <input name="username" autocomplete="username"></label><label>비밀번호 <input type="password" name="password" autocomplete="current-password"></label><button>로그인</button></form></html>');return
                view=workspace.read_only_view(args.get('query',''),args.get('kind'),args.get('state')) if offline else workspace.view(self.token(),args.get('query',''),args.get('kind'),args.get('state'))
                if url.path=='/api/view':self.send(200,w.encoded(view),'application/json');return
                if url.path=='/source':
                    source=next((s for s in view['sources'].values() if s['id']==args.get('id')),None);w.need(source,'Unknown/forbidden source')
                    path=w.local(workspace.root,source['path']);w.need(path.is_file() and path.stat().st_size<=4_000_000,'Source missing/too large');raw=path.read_bytes();w.need(w.sha(raw)==source['sha256'],'Source changed since collection')
                    self.send(200,'<!doctype html><meta charset="utf-8"><a href="/?tab=documents">전체 문서</a><h1>'+escape(source['path'])+'</h1><pre style="white-space:pre-wrap">'+escape(raw.decode('utf-8',errors='replace'))+'</pre>');return
                w.need(url.path=='/','Unknown path');tab=args.get('tab','overview');page=int(args.get('page','0'))
                body=ui.render(view,tab,args.get('focus'),args.get('query',''),page)
                if tab in {'overview','decisions','objects'}:ui.audit(body,view,tab,page)
                self.send(200,body)
            except (ValueError,OSError,sqlite3.Error):self.send(403,'접근 또는 현재 근거를 확인할 수 없습니다. <a href="/login">로그인</a>')
        def do_POST(self):
            try:
                self.boundary();size=int(self.headers.get('Content-Length','0'));w.need(0<size<=32768,'Body limit')
                raw=self.rfile.read(size);path=urlsplit(self.path).path
                if path=='/login':
                    body=parse_qs(raw.decode());token=self.accounts().login(body.get('username',[''])[0],body.get('password',[''])[0]);w.need(token,'Login rejected')
                    self.send(200,'<a href="/">운영 위키 열기</a>',cookie='workspace_session='+token+'; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800');return
                if path=='/action-form':
                    w.need(self.headers.get('Content-Type')=='application/x-www-form-urlencoded','Form type required')
                    fields=parse_qs(raw.decode(),keep_blank_values=True);w.need(all(len(v)==1 for v in fields.values()),'Duplicate action field')
                    request={k:v[0] for k,v in fields.items()};request['expected_revision']=int(request.get('expected_revision','-1'))
                    workspace.act(self.token(),request);self.send(200,'판단 이벤트를 기록했습니다. <a href="/?tab=objects">객체 상태 다시 조회</a>');return
                w.need(self.headers.get('X-Workspace-Action')=='1' and self.headers.get('Content-Type')=='application/json','Action request header required')
                if path=='/api/action':self.send(200,w.encoded(workspace.act(self.token(),w.strict(raw))),'application/json');return
                if path=='/logout':self.accounts().logout(self.token());self.send(200,'로그아웃',cookie='workspace_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0');return
                raise ValueError('Unknown action')
            except (ValueError,OSError,sqlite3.Error):self.send(403,'요청의 권한·버전·근거를 확인할 수 없습니다.')
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--port',type=int,default=8766);a=p.parse_args()
    with server(a.root,a.port) as http:http.serve_forever()
