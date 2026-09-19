"""Pinned delivery adapter protocol: inspect, activate, health, rollback, health.

Adapters are explicitly authorized executables, not a sandbox. Unknown effects
remain pending; failed health requires observed recovery, never a success claim.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import os
import threading
import time
import re
import workspace as w


class Delivery:
    def __init__(self,root):
        self.root=Path(root).absolute();self.path=w.local(self.root,'.harness-workspace/delivery.sqlite3')
    def initialize(self,policy_path):
        p=self.check_policy(policy_path);digest=w.sha(w.encoded(p))
        if self.path.exists():
            with closing(self.connect()) as db:w.need(db.execute('SELECT path,digest FROM policy').fetchone()==(policy_path,digest),'Delivery policy conflict')
            return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('xb'):pass
        with closing(sqlite3.connect(self.path)) as db,db:
            db.executescript('CREATE TABLE policy(path TEXT,digest TEXT); CREATE TABLE events(seq INTEGER PRIMARY KEY,key TEXT,kind TEXT,body BLOB,prev TEXT,hash TEXT,UNIQUE(key,kind)); CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,"append only"); END; CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,"append only"); END; PRAGMA user_version=1;')
            db.execute('INSERT INTO policy VALUES(?,?)',(policy_path,digest))
        with closing(sqlite3.connect(w.local(self.root,'.harness-workspace/delivery-lock.sqlite3'))) as lock:
            lock.execute('PRAGMA user_version=1')
    def connect(self):
        w.local(self.root,'.harness-workspace/delivery.sqlite3');w.need(self.path.is_file(),'Delivery unconfigured')
        db=sqlite3.connect(self.path.as_uri()+'?mode=rw',uri=True,timeout=5)
        if db.execute('PRAGMA user_version').fetchone()[0]!=1:db.close();raise ValueError('Unsupported delivery storage')
        return db
    def check_policy(self,path):
        p=w.strict(w.local(self.root,path).read_bytes())
        w.need(type(p) is dict and set(p)=={'schema_version','authority_ref','commands','bindings','executables','timeout_seconds','artifact_paths','canary'},'Delivery policy fields differ')
        w.need(type(p['schema_version']) is int and p['schema_version']==1 and w.text(p['authority_ref']),'Delivery owner authorization required')
        w.need(type(p['timeout_seconds']) is int and 1<=p['timeout_seconds']<=60,'Bounded timeout required')
        w.need(type(p['commands']) is dict and set(p['commands'])=={'inspect','activate','health','rollback'},'Complete recovery adapters required')
        for argv in p['commands'].values():w.need(type(argv) is list and 1<=len(argv)<=32 and all(w.text(a) for a in argv) and Path(argv[0]).is_absolute(),'Pinned argv required')
        w.need(type(p['executables']) is dict and set(p['executables'])=={v[0] for v in p['commands'].values()},'Executable pins required')
        for name,digest in p['executables'].items():w.need(w.sha(Path(name).read_bytes())==digest,'Executable drift')
        w.need(type(p['bindings']) is dict and p['bindings'],'Adapter source bindings required')
        for name,digest in p['bindings'].items():w.need(w.sha(w.local(self.root,name).read_bytes())==digest,'Adapter source drift')
        w.need(type(p['artifact_paths']) is list and 1<=len(p['artifact_paths'])<=1000 and all(type(n) is str for n in p['artifact_paths']) and len(p['artifact_paths'])==len(set(n.casefold() for n in p['artifact_paths'])),'Explicit artifact inventory required')
        for name in p['artifact_paths']:w.local(self.root,name)
        c=p['canary'];w.need(type(c) is dict and set(c)=={'target','checks','interval_seconds'} and w.ident(c['target']) and type(c['checks']) is int and 2<=c['checks']<=10 and type(c['interval_seconds']) is int and 1<=c['interval_seconds'] and (c['checks']-1)*c['interval_seconds']<=60,'Explicit bounded canary observation required')
        return p
    def policy(self,db):
        self.events(db)
        path,digest=db.execute('SELECT path,digest FROM policy').fetchone();p=self.check_policy(path)
        w.need(w.sha(w.encoded(p))==digest,'Pinned delivery policy changed');return p
    def events(self,db):
        rows=[];previous=w.ZERO
        for seq,key,kind,body,prev,digest in db.execute('SELECT * FROM events ORDER BY seq'):
            value=w.strict(body)
            w.need(seq==len(rows)+1 and prev==previous and digest==w.sha(w.encoded([seq,key,kind,value,prev])),'Delivery audit corruption')
            rows.append({'key':key,'kind':kind,'body':value});previous=digest
        return rows
    def append(self,db,key,kind,value):
        rows=self.events(db);seq=len(rows)+1;last=db.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone();prev=last[0] if last else w.ZERO
        db.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(seq,key,kind,w.encoded(value),prev,w.sha(w.encoded([seq,key,kind,value,prev]))))
    def call(self,db,phase,context):
        p=self.policy(db);argv=p['commands'][phase]
        request=w.encoded(dict(context,phase=phase));w.need(len(request)<=32768,'Adapter input limit')
        env={k:v for k,v in os.environ.items() if k in {'PATH','SystemRoot','WINDIR','TEMP','TMP'}}
        env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
        process=subprocess.Popen(argv,cwd=self.root,env=env,shell=False,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        buffers=[bytearray(),bytearray()];failed=threading.Event()
        def read(stream,index):
            try:
                while True:
                    chunk=stream.read(4096)
                    if not chunk:break
                    remaining=65536-len(buffers[index]);buffers[index].extend(chunk[:remaining])
                    if len(chunk)>remaining:failed.set();break
            except OSError:failed.set()
            finally:stream.close()
        def write():
            try:process.stdin.write(request);process.stdin.close()
            except OSError:failed.set()
        workers=[threading.Thread(target=read,args=(process.stdout,0),daemon=True),threading.Thread(target=read,args=(process.stderr,1),daemon=True),threading.Thread(target=write,daemon=True)]
        for worker in workers:worker.start()
        deadline=time.monotonic()+p['timeout_seconds']
        while process.poll() is None and not failed.is_set() and time.monotonic()<deadline:time.sleep(.01)
        expired=process.poll() is None
        if expired:process.kill()
        process.wait(timeout=2)
        for worker in workers:worker.join(.25)
        w.need(not expired and not failed.is_set() and not any(t.is_alive() for t in workers) and process.returncode==0,'Adapter effect unknown; reconcile before retry')
        reply=w.strict(bytes(buffers[0]));w.need(type(reply) is dict and set(reply)=={'ok','active'} and type(reply['ok']) is bool and (reply['active'] is None or type(reply['active']) is str and re.fullmatch('[0-9a-f]{64}',reply['active'])),'Adapter response differs')
        return reply
    def guard(self):
        path=w.local(self.root,'.harness-workspace/delivery-lock.sqlite3');w.need(path.is_file(),'Delivery lock missing')
        db=sqlite3.connect(path.as_uri()+'?mode=rw',uri=True,timeout=1);db.execute('BEGIN IMMEDIATE');return db
    def release(self,token,subject,key,expected_active):
        with closing(self.guard()):return self._release(token,subject,key,expected_active)
    def _release(self,token,subject,key,expected_active):
        w.need(w.ident(key) and w.ident(subject) and (expected_active is None or type(expected_active) is str and re.fullmatch('[0-9a-f]{64}',expected_active)),'Stable delivery identity required');workspace=w.Workspace(self.root)
        with closing(workspace.connect()) as source:
            actor,role=workspace.principal(source,token);config,objects,states,view=workspace._project(source,role)
            w.need('deliver' in config['roles'][role] and subject in view['objects'],'Delivery denied')
            state=states[subject];w.need(state['workflow']=='accepted' and state['verification']=='passed','Accepted current subject required')
            observed=w.component('harness').Core(self.root).status(objects[subject]['task_id'])
        with closing(self.connect()) as db:
            p=self.policy(db);files={name:w.sha(w.local(self.root,name).read_bytes()) for name in p['artifact_paths']}
            bound=observed['input_snapshot']['files']
            policy_path=db.execute('SELECT path FROM policy').fetchone()[0]
            w.need(all(bound.get(name)==digest for name,digest in {**files,**p['bindings'],policy_path:w.sha(w.local(self.root,policy_path).read_bytes())}.items()),'Artifact/adapter/policy not covered by current required Run')
            candidate=w.sha(w.encoded(files));w.need(candidate!=expected_active,'Do not overwrite active artifact');context={'subject':subject,'candidate':candidate,'previous':expected_active,'files':files,'actor':actor,'snapshot':state['snapshot'],'target':p['canary']['target']}
            digest=w.sha(w.encoded(context));db.execute('BEGIN IMMEDIATE')
            start=db.execute("SELECT body FROM events WHERE key=? AND kind='started'",(key,)).fetchone()
            if start:
                w.need(w.strict(start[0])['digest']==digest,'Delivery idempotency conflict')
                done=db.execute("SELECT body FROM events WHERE key=? AND kind='finished'",(key,)).fetchone();w.need(done,'Previous delivery pending; do not retry');return w.strict(done[0])
            w.need(not db.execute("SELECT key FROM events WHERE kind='started' EXCEPT SELECT key FROM events WHERE kind='finished'").fetchall(),'Unresolved delivery effect')
            self.append(db,key,'started',{'digest':digest,'context':context});db.commit()
            receipts=[]
            def call(phase,recovery=False,observation=None):
                if not recovery:
                    w.need(all(w.sha(w.local(self.root,name).read_bytes())==digest for name,digest in files.items()),'Artifact changed during delivery')
                    with closing(workspace.connect()) as source:
                        _,current_role=workspace.principal(source,token);current_config,_,current_states,current_view=workspace._project(source,current_role)
                        w.need('deliver' in current_config['roles'][current_role] and subject in current_view['objects'] and current_states[subject]['snapshot']==context['snapshot'] and current_states[subject]['workflow']=='accepted' and current_states[subject]['verification']=='passed','Delivery authorization/evidence changed')
                reply=self.call(db,phase,context);receipt={'phase':phase,**reply};receipts.append(receipt)
                with db:self.append(db,key,('recovery_' if recovery else '')+phase+('' if observation is None else '_'+str(observation)),receipt)
                return reply
            before=call('inspect')
            if not before['ok'] or before['active']!=expected_active:
                result={'outcome':'aborted','candidate':candidate,'active':before['active'],'receipts':receipts}
                with db:self.append(db,key,'finished',result)
                return result
            activate=call('activate');w.need(activate['ok'] and activate['active']==candidate,'Activation result unknown')
            started=time.monotonic()
            for i in range(p['canary']['checks']):
                if i:time.sleep(p['canary']['interval_seconds'])
                health=call('health',observation=i)
                if not health['ok'] or health['active']!=candidate:break
            if health['ok'] and health['active']==candidate:outcome='released'
            else:
                restored=call('rollback',True);w.need(restored['ok'] and restored['active']==expected_active,'Rollback failed; effect unknown')
                context=dict(context,candidate=expected_active)
                check=call('health',True);w.need(check['ok'] and check['active']==expected_active,'Recovery health unverified');outcome='rolled_back'
            result={'outcome':outcome,'candidate':candidate,'active':candidate if outcome=='released' else expected_active,'canary':{'target':p['canary']['target'],'elapsed_seconds':round(time.monotonic()-started,3),'required_checks':p['canary']['checks'],'expansion':'not_authorized'},'receipts':receipts}
            with db:self.append(db,key,'finished',result)
            return result
    def reconcile(self,token,key):
        with closing(self.guard()):return self._reconcile(token,key)
    def _reconcile(self,token,key):
        """Read-only adapter observations resolve pending effects; never reactivate."""
        workspace=w.Workspace(self.root)
        with closing(workspace.connect()) as source:
            actor,role=workspace.principal(source,token);config,_,_,view=workspace._project(source,role)
            w.need('deliver' in config['roles'][role],'Reconciliation denied')
        with closing(self.connect()) as db:
            self.policy(db);db.execute('BEGIN IMMEDIATE')
            start=db.execute("SELECT body FROM events WHERE key=? AND kind='started'",(key,)).fetchone();w.need(start,'Unknown delivery')
            context=w.strict(start[0])['context'];w.need(context['subject'] in view['objects'],'Hidden delivery')
            done=db.execute("SELECT body FROM events WHERE key=? AND kind='finished'",(key,)).fetchone()
            if done:return w.strict(done[0])
            observed=self.call(db,'inspect',context);w.need(observed['ok'] and observed['active'] in {context['candidate'],context['previous']},'Active identity unresolved')
            healthy=self.call(db,'health',dict(context,candidate=observed['active']));w.need(healthy['ok'] and healthy['active']==observed['active'],'Active health unresolved')
            result={'outcome':'reconciled_candidate' if observed['active']==context['candidate'] else 'reconciled_previous','candidate':context['candidate'],'active':observed['active'],'actor':actor,'receipts':[{'phase':'inspect',**observed},{'phase':'health',**healthy}]}
            self.append(db,key,'finished',result);db.commit();return result
    def observations(self):
        if not self.path.exists():return {}
        with closing(self.connect()) as db:
            self.policy(db);events=self.events(db)
        out={};starts={}
        for event in events:
            if event['kind']=='started':
                context=event['body']['context'];starts[event['key']]=context
                out[context['subject']]={'snapshot':context['snapshot'],'outcome':'effect_unknown'}
            elif event['kind']=='finished':
                context=starts[event['key']];outcome=event['body']['outcome']
                if any(not w.local(self.root,n).is_file() or w.sha(w.local(self.root,n).read_bytes())!=h for n,h in context['files'].items()):outcome='stale'
                out[context['subject']]={'snapshot':context['snapshot'],'outcome':outcome}
        return out


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path.cwd());s=p.add_subparsers(dest='cmd',required=True)
    c=s.add_parser('init');c.add_argument('--policy',required=True)
    c=s.add_parser('release');c.add_argument('--subject',required=True);c.add_argument('--key',required=True);c.add_argument('--expected-active',required=True)
    c=s.add_parser('reconcile');c.add_argument('--key',required=True)
    a=p.parse_args()
    try:
        d=Delivery(a.root)
        if a.cmd=='init':d.initialize(a.policy);result={'outcome':'configured'}
        elif a.cmd=='release':result=d.release(sys.stdin.readline().strip(),a.subject,a.key,None if a.expected_active=='none' else a.expected_active)
        else:result=d.reconcile(sys.stdin.readline().strip(),a.key)
        print(w.encoded(result).decode())
    except (ValueError,OSError,sqlite3.Error):print('{"outcome":"blocked","reason":"Inspect policy, current evidence and pending effects before retry"}');raise SystemExit(2)
