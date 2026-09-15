"""Evidence-oriented workspace: local sources, authenticated workflow events, OOP projections.

No state is stored on an object. This component does not impersonate an owner or
run deployments. Its authenticated action boundary is shared by CLI and HTTP.
"""
import argparse
from contextlib import closing
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import sys
from datetime import datetime, timezone

PROFILE = 'operating-workspace-1'
TYPES = {'requirement','task','decision','module','test','release'}
ACTIONS = {'propose','authorize','start','submit','accept','defer','block','resume'}
ZERO = '0'*64


def encoded(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def strict(raw):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'Duplicate JSON key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def ident(v):return type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}',v) is not None
def text(v):return type(v) is str and 0<len(v.strip())<=4000
def relative(v):
    need(type(v) is str and v and not any(x in v for x in ('\\',':','\0')) and not v.startswith('/'),'Relative path required')
    need(all(s not in ('','..','.') and s==s.rstrip(' .') for s in v.split('/')),'Unsafe path')
    need(not any(s.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for s in v.split('/')),'Reserved device path')
    return v
def local(root,name):
    path=root/relative(name)
    for p in [path,*path.parents]:
        if p.exists():need(not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'Reparse path forbidden')
    return path
def component(name):
    s=importlib.util.spec_from_file_location('workspace_'+name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def engine_pins():
    return {name:sha(Path(__file__).with_name(name+'.py').read_bytes()) for name in ['workspace','workspace_view','workspace_server','delivery','harness','wiki_access']}


def policy(value):
    need(type(value) is dict and set(value)=={'schema_version','profile','project_id','authority_ref','roles','principals','sources','registry','accounts','access_mode'},'Workspace policy fields differ')
    need(type(value['schema_version']) is int and value['schema_version']==1 and value['profile']==PROFILE,'Unsupported workspace policy')
    need(ident(value['project_id']) and text(value['authority_ref']),'Owner interview reference required')
    need(type(value['roles']) is dict and 1<=len(value['roles'])<=32,'Explicit owner-selected roles required')
    for role,caps in value['roles'].items():
        need(ident(role) and type(caps) is list and len(caps)==len(set(caps)) and set(caps)<=(ACTIONS|{'read','deliver'}),'Invalid role capabilities')
    need(value['access_mode'] in {'authenticated','loopback_read_only'},'Owner-selected access mode required')
    need(type(value['principals']) is dict,'Explicit principals required')
    if value['access_mode']=='authenticated':need(value['principals'],'Explicit principals required');relative(value['accounts'])
    else:need(len(value['roles'])==1 and list(value['roles'].values())==[['read']] and value['principals']=={} and value['accounts'] is None,'Offline view cannot hold identities or action capabilities')
    for user,role in value['principals'].items():need(ident(user) and role in value['roles'],'Invalid principal')
    need(type(value['sources']) is list and 1<=len(value['sources'])<=32,'Approved source roots required')
    paths=[]
    for source in value['sources']:
        need(type(source) is dict and set(source)=={'path','kind','roles'},'Source policy fields differ')
        relative(source['path']);paths.append(source['path'])
        need(source['kind'] in {'documents','code','data'} and type(source['roles']) is list and source['roles'] and set(source['roles'])<=set(value['roles']),'Invalid source scope')
        need(not any(part.startswith('.') for part in source['path'].split('/')),'Private/control roots cannot be discovered')
    need(len(set(x.casefold() for x in paths))==len(paths),'Duplicate roots')
    need(not any(a!=b and b.casefold().startswith(a.casefold()+'/') for a in paths for b in paths),'Overlapping source roots')
    relative(value['registry']);return value


def inventory(root,config):
    """No network, execution, hidden files, credentials or source body export."""
    records={};folded=set()
    extensions={'documents':{'.md'},'code':{'.py','.gd','.js','.ts','.mjs','.cjs','.tscn'},'data':{'.csv','.json'}}
    for scope in config['sources']:
        base=local(root,scope['path']);need(base.is_dir(),'Approved source root missing')
        for p in sorted(base.rglob('*')):
            name=p.relative_to(root).as_posix();local(root,name)
            if any(s.startswith('.') or s in {'node_modules','__pycache__'} for s in p.relative_to(base).parts):continue
            if not p.is_file() or p.suffix.lower() not in extensions[scope['kind']]:continue
            need(not re.search(r'(?:secret|credential|api[-_]?key|password|token)',p.stem,re.I),'Sensitive-named source must be excluded from approved roots')
            need(p.stat().st_size<=4_000_000 and len(records)<5000,'Source budget exceeded')
            need(name.casefold() not in folded,'Case-colliding sources');folded.add(name.casefold())
            raw=p.read_bytes();records[name]={'id':'SRC-'+sha(name.encode())[:24],'path':name,'sha256':sha(raw),'kind':scope['kind'],'roles':scope['roles'],'bytes':len(raw)}
    return records


def registry(root,config,records):
    value=strict(local(root,config['registry']).read_bytes());need(type(value) is dict and set(value)=={'schema_version','objects'} and type(value['schema_version']) is int and value['schema_version']==1,'Registry schema differs')
    need(type(value['objects']) is list and 1<=len(value['objects'])<=1000,'Bounded object registry required')
    objects={}
    for obj in value['objects']:
        need(type(obj) is dict and set(obj)=={'id','type','title','purpose','sources','depends_on','task_id','acceptance_class'},'Object intent fields differ; authored state forbidden')
        need(ident(obj['id']) and obj['id'] not in objects and obj['type'] in TYPES and text(obj['title']) and text(obj['purpose']),'Invalid object')
        for field in ['sources','depends_on']:need(type(obj[field]) is list and len(obj[field])==len(set(obj[field])),'Unique object references required')
        need(obj['sources'] and all(type(p) is str and p in records for p in obj['sources']),'Missing/unapproved object source')
        need(obj['task_id'] is None or ident(obj['task_id']),'Invalid core Task binding')
        need(obj['acceptance_class'] in {'machine_verifiable','human_verifiable','mixed'},'Acceptance boundary required')
        objects[obj['id']]=dict(obj)
    visited=set()
    def visit(key,ancestors):
        need(key in objects and key not in ancestors,'Missing/cyclic dependency')
        need(len(ancestors)<100,'Dependency depth budget exceeded')
        if key in visited:return
        for dep in objects[key]['depends_on']:visit(dep,ancestors|{key})
        visited.add(key)
    for key in objects:visit(key,set())
    return objects


class Workspace:
    def __init__(self,root):
        self.root=Path(root).absolute();self.path=local(self.root,'.harness-workspace/ledger.sqlite3')
    def connect(self,write=False):
        local(self.root,'.harness-workspace/ledger.sqlite3');need(self.path.is_file(),'Workspace unconfigured')
        db=sqlite3.connect(self.path.as_uri()+('?mode=rw' if write else '?mode=ro'),uri=True,timeout=5)
        if db.execute('PRAGMA user_version').fetchone()[0]!=1:db.close();raise ValueError('Unknown workspace schema')
        return db
    def initialize(self,config_path):
        p=local(self.root,config_path);value=policy(strict(p.read_bytes()));digest=sha(encoded(value))
        if self.path.exists():
            with closing(self.connect()) as db:need(db.execute('SELECT config_path,digest,engines FROM config').fetchone()==(config_path,digest,encoded(engine_pins())),'Workspace policy/engine conflict')
            return {'outcome':'unchanged'}
        # Exclusive create preserves partial initializations rather than resetting them.
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('xb'):pass
        with closing(sqlite3.connect(self.path)) as db,db:
            db.executescript('CREATE TABLE config(config_path TEXT,digest TEXT,engines BLOB); CREATE TABLE events(seq INTEGER PRIMARY KEY,body BLOB NOT NULL,prev TEXT NOT NULL,hash TEXT NOT NULL); CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,"append only"); END; CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,"append only"); END; PRAGMA user_version=1;')
            db.execute('INSERT INTO config VALUES(?,?,?)',(config_path,digest,encoded(engine_pins())))
        (self.path.parent/'.gitignore').write_text('*\n',encoding='utf-8');return {'outcome':'created'}
    def config(self,db):
        path,digest,engines=db.execute('SELECT config_path,digest,engines FROM config').fetchone();need(strict(engines)==engine_pins(),'Pinned workspace engine changed');v=policy(strict(local(self.root,path).read_bytes()))
        need(sha(encoded(v))==digest,'Pinned workspace policy changed');return v
    def events(self,db):
        out=[];previous=ZERO;keys=set();revisions={}
        for seq,body,prev,digest in db.execute('SELECT seq,body,prev,hash FROM events ORDER BY seq'):
            need(seq==len(out)+1 and prev==previous and sha(encoded({'seq':seq,'prev':prev,'body':strict(body)}))==digest,'Workspace event corruption')
            value=strict(body);need(value.get('kind') in {'collection','action'},'Unsupported workspace event')
            need(ident(value.get('key')) and value['key'] not in keys,'Duplicate event key');keys.add(value['key'])
            if value['kind']=='collection':
                need(set(value)=={'kind','key','digest','content','observed_at'} and sha(encoded(value['content']))==value['digest'],'Collection record differs')
            else:
                need(set(value)=={'kind','key','subject','action','actor','role','revision','snapshot','reason','request_digest','observed_at'} and value['action'] in ACTIONS,'Action record differs')
                need(value['revision']==revisions.get(value['subject'],0)+1,'Action revision gap');revisions[value['subject']]=value['revision']
            out.append(dict(seq=seq,ref=digest,**value));previous=digest
        return out
    def append(self,db,value):
        rows=self.events(db);previous=db.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone();prev=previous[0] if previous else ZERO;seq=len(rows)+1
        digest=sha(encoded({'seq':seq,'prev':prev,'body':value}));db.execute('INSERT INTO events VALUES(?,?,?,?)',(seq,encoded(value),prev,digest));return seq
    def collect(self,key):
        need(ident(key),'Stable collection key required')
        with closing(self.connect(True)) as db,db:
            db.execute('BEGIN IMMEDIATE');config=self.config(db);records=inventory(self.root,config);objects=registry(self.root,config,records)
            content={'sources':records,'objects':objects};digest=sha(encoded(content));rows=self.events(db)
            old=next((e for e in rows if e['key']==key),None)
            if old:need(old['kind']=='collection' and old['digest']==digest,'Idempotency conflict');return {'outcome':'unchanged','seq':old['seq'],'digest':digest}
            seq=self.append(db,dict(kind='collection',key=key,digest=digest,content=content,observed_at=datetime.now(timezone.utc).isoformat()))
            return {'outcome':'observed','seq':seq,'digest':digest}
    def backup(self,out):
        """Quiescent audit export; credentials and live deployment authority excluded."""
        delivery=component('delivery').Delivery(self.root)
        guard=delivery.guard() if delivery.path.exists() else None
        try:
            with closing(self.connect(True)) as db:
                db.execute('BEGIN IMMEDIATE');self.config(db);self.events(db)
                config=list(db.execute('SELECT config_path,digest,engines FROM config').fetchone());config[2]=strict(config[2])
                events=[[seq,strict(body),prev,digest] for seq,body,prev,digest in db.execute('SELECT * FROM events ORDER BY seq')]
                deliveries=[]
                if delivery.path.exists():
                    with closing(delivery.connect()) as target:
                        delivery.events(target);deliveries=[[seq,key,kind,strict(body),prev,digest] for seq,key,kind,body,prev,digest in target.execute('SELECT * FROM events ORDER BY seq')]
                value={'format':'workspace-audit-1','config':config,'events':events,'deliveries':deliveries,'authority':'inspection_only'}
                raw=encoded(value);need(len(raw)<=64_000_000,'Backup budget exceeded');path=local(self.root,out);path.parent.mkdir(parents=True,exist_ok=True)
                if path.exists():need(path.read_bytes()==raw,'Backup path conflict');return {'outcome':'unchanged','sha256':sha(raw)}
                with path.open('xb') as stream:stream.write(raw)
                return {'outcome':'backup_created','sha256':sha(raw)}
        finally:
            if guard:guard.close()
    def restore(self,backup):
        """Restore into an isolated inspection archive, never an active operation DB."""
        need(not self.path.exists(),'Active workspace cannot be overwritten')
        need(backup.stat().st_size<=64_000_000,'Backup budget exceeded');raw=backup.read_bytes();value=strict(raw)
        need(type(value) is dict and set(value)=={'format','config','events','deliveries','authority'} and value['format']=='workspace-audit-1' and value['authority']=='inspection_only','Unsupported backup')
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('CREATE TABLE events(seq INTEGER,body BLOB,prev TEXT,hash TEXT)')
            for seq,body,prev,digest in value['events']:db.execute('INSERT INTO events VALUES(?,?,?,?)',(seq,encoded(body),prev,digest))
            self.events(db)
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('CREATE TABLE events(seq INTEGER,key TEXT,kind TEXT,body BLOB,prev TEXT,hash TEXT)')
            for seq,key,kind,body,prev,digest in value['deliveries']:db.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(seq,key,kind,encoded(body),prev,digest))
            component('delivery').Delivery(self.root).events(db)
        # The audit export is not an authority import or an automatic data rollback.
        path=local(self.root,'.harness-workspace/inspection.json');path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():need(path.read_bytes()==raw,'Inspection archive conflict');return {'outcome':'unchanged','authority':'inspection_only'}
        with path.open('xb') as stream:stream.write(raw)
        (path.parent/'.gitignore').write_text('*\n',encoding='utf-8')
        return {'outcome':'restored_for_inspection','authority':'inspection_only','events':len(value['events'])}
    def principal(self,db,token):
        config=self.config(db);need(config['access_mode']=='authenticated','Offline view has no authenticated action authority');store=local(self.root,config['accounts']);account=component('wiki_access').Accounts(store,config['roles'],sha(encoded(config)))
        role=account.role(token);need(role in config['roles'],'Authenticated principal required')
        with closing(account.connect()) as users:
            name=users.execute('SELECT username FROM sessions WHERE token_hash=?',(sha(token.encode()),)).fetchone()[0]
        need(config['principals'].get(name)==role,'Principal revoked or unapproved');return name,role
    def _project(self,db,role,cache_core=True):
        config=self.config(db);need(role in config['roles'] and 'read' in config['roles'][role],'Read denied')
        events=self.events(db);collections=[e for e in events if e['kind']=='collection'];need(collections,'Collect approved sources first')
        content=collections[-1]['content'];sources=content['sources'];objects=content['objects'];states={};action_index={};core_cache={};core_event_refs={}
        for event in events:
            if event['kind']=='action':action_index.setdefault(event['subject'],[]).append(event)
        core=component('harness')
        try:deliveries=component('delivery').Delivery(self.root).observations()
        except (ValueError,OSError,sqlite3.Error):deliveries=None
        # Each actual source is read once for the whole projection, not once per object.
        current={};bodies={}
        for path in sources:
            p=local(self.root,path)
            if p.is_file():
                need(p.stat().st_size<=4_000_000,'Source budget exceeded');bodies[path]=p.read_bytes();current[path]=sha(bodies[path])
            else:current[path]=None
        try:declarations=registry(self.root,config,sources)
        except (ValueError,OSError):declarations={}
        def derive(key):
            if key in states:return states[key]
            obj=objects[key];deps={d:derive(d) for d in obj['depends_on']}
            observed=None
            if obj['task_id']:
                try:
                    if not cache_core or obj['task_id'] not in core_cache:core_cache[obj['task_id']]=core.Core(self.root).status(obj['task_id'])
                    observed=core_cache[obj['task_id']]
                except (OSError,ValueError,sqlite3.Error,core.HarnessError):pass
            core_contract={'revision':observed['task_revision'],'inputs':observed.get('input_snapshot')} if observed else None
            fingerprint=sha(encoded({'intent':obj,'sources':{p:current[p] for p in obj['sources']},'core_contract':core_contract,'dependencies':{d:v['snapshot'] for d,v in deps.items()}}))
            stale=declarations.get(key)!=obj or any(current[p]!=sources[p]['sha256'] for p in obj['sources'])
            actions=action_index.get(key,[]);applicable=[e for e in actions if e['snapshot']==fingerprint]
            revision=actions[-1]['revision'] if actions else 0;last=applicable[-1] if applicable else None
            workflow={'propose':'needs_decision','authorize':'ready','start':'in_progress','submit':'review_pending','accept':'accepted','defer':'deferred','block':'blocked','resume':'needs_decision'}.get(last['action'] if last else '', 'needs_decision')
            blocked=any(v['workflow']!='accepted' for v in deps.values());verification='unverified';core_ref=None
            if obj['task_id']:
                if observed:
                    bound=(observed.get('input_snapshot') or {}).get('files',{})
                    if all(bound.get(p)==current[p] for p in obj['sources']):
                        verification=observed['verification']
                        if not core_event_refs:core_event_refs.update({e['seq']:e['hash'] for e in core.Core(self.root).read()})
                        core_ref={'task':obj['task_id'],'events':[core_event_refs[n] for n in observed['evidence_event_sequences']],'rule':observed['rule_version']}
                    else:verification='stale'
                else:verification='unknown'
            if stale:workflow='needs_decision';verification='stale'
            elif blocked and workflow not in {'deferred','needs_decision'}:workflow='blocked'
            elif workflow in {'review_pending','accepted'} and verification!='passed' and obj['acceptance_class']!='human_verifiable':workflow='in_progress'
            next_action={'needs_decision':'확인된 원본과 범위 승인','ready':'선행 조건 확인 후 착수','in_progress':'구현과 현재 검사 근거 제출','review_pending':'독립 승인자의 수락 판단','accepted':'변경 감시와 출시 판단','blocked':'선행 조건 또는 차단 원인 해결','deferred':'오너의 재개 판단 대기'}[workflow]
            states[key]={'workflow':workflow,'verification':verification,'acceptance':'human_recorded' if workflow=='accepted' else 'pending','delivery':'unobserved','snapshot':fingerprint,'revision':revision,'source_stale':stale,'dependency_blocked':blocked,'core_evidence':core_ref,'events':[{k:e[k] for k in ['ref','action','actor','reason','observed_at']} for e in applicable],'next_action':next_action}
            if deliveries is None:states[key]['delivery']='unknown'
            elif key in deliveries:
                delivery=deliveries[key];states[key]['delivery']=delivery['outcome'] if delivery['snapshot']==fingerprint and not stale else 'stale'
            return states[key]
        for key in objects:derive(key)
        visible={k:o for k,o in objects.items() if all(role in sources[p]['roles'] for p in o['sources'])}
        safe_states={}
        for k in visible:
            v=dict(states[k]);hidden=any(d not in visible for d in objects[k]['depends_on'])
            safe_states[k]=dict(v,dependency_blocked=True) if hidden else v
        source_view={p:s for p,s in sources.items() if role in s['roles']};documents={};collections_view={}
        for path,s in source_view.items():
            parts=path.split('/')[:-1];parent=None
            for i in range(len(parts)):
                folder='/'.join(parts[:i+1]);group='GROUP-'+sha(folder.encode())[:24]
                collections_view[group]={'id':group,'title':parts[i],'parent':parent};parent=group
            body=bodies.get(path,b'').decode('utf-8',errors='replace')
            heading=next((line.lstrip('#').strip() for line in body.splitlines() if line.startswith('# ')),Path(path).name)
            documents[s['id']]={'id':s['id'],'title':heading if s['kind']=='documents' else Path(path).name,'path':path,'kind':s['kind'],'parent':parent,'sha256':current[path],'stale':current[path]!=s['sha256']}
        return config,objects,states,dict(profile=PROFILE,objects={k:{**o,'depends_on':[d for d in o['depends_on'] if d in visible]} for k,o in visible.items()},states=safe_states,sources=source_view,documents=documents,collections=collections_view)
    def view(self,token,query='',kind=None,state=None):
        with closing(self.connect()) as db:
            _,role=self.principal(db,token);config,_,_,view=self._project(db,role)
        matches=[k for k,o in view['objects'].items() if query.casefold() in (o['title']+' '+o['purpose']+' '+k).casefold() and (not kind or o['type']==kind) and (not state or view['states'][k]['workflow']==state)]
        view['matches']=sorted(matches);view['filters']={'query':query,'kind':kind or '', 'state':state or ''};view['capabilities']=sorted(set(config['roles'][role])&ACTIONS);return view
    def read_only_view(self,query='',kind=None,state=None):
        """Call only behind an owner-approved loopback read boundary; no identities."""
        with closing(self.connect()) as db:
            config=self.config(db);need(config['access_mode']=='loopback_read_only','Anonymous view not configured');_,_,_,view=self._project(db,next(iter(config['roles'])))
        view['matches']=sorted(k for k,o in view['objects'].items() if query.casefold() in (o['title']+' '+o['purpose']+' '+k).casefold() and (not kind or o['type']==kind) and (not state or view['states'][k]['workflow']==state))
        view['filters']={'query':query,'kind':kind or '', 'state':state or ''};view['capabilities']=[];return view
    def act(self,token,request):
        need(type(request) is dict and set(request)=={'subject','action','key','expected_revision','snapshot','reason'},'Action shape differs')
        need(all(ident(request[k]) for k in ['subject','key']) and request['action'] in ACTIONS and type(request['expected_revision']) is int and request['expected_revision']>=0 and text(request['reason']),'Invalid action')
        with closing(self.connect(True)) as db,db:
            db.execute('BEGIN IMMEDIATE');actor,role=self.principal(db,token);config,objects,states,view=self._project(db,role)
            need(request['subject'] in view['objects'] and request['action'] in config['roles'][role],'Action denied')
            digest=sha(encoded({'actor':actor,'request':request}));events=self.events(db);prior=next((e for e in events if e['key']==request['key']),None)
            if prior:need(prior['kind']=='action' and prior['request_digest']==digest,'Idempotency conflict');return {'outcome':'unchanged','seq':prior['seq']}
            s=states[request['subject']];a=request['action'];need(s['revision']==request['expected_revision'] and s['snapshot']==request['snapshot'],'Stale revision/snapshot')
            need(not s['source_stale'],'Collect changed sources before workflow action')
            allowed={'propose':{'needs_decision'},'authorize':{'needs_decision'},'start':{'ready'},'submit':{'in_progress'},'accept':{'review_pending'},'defer':{'needs_decision','ready','in_progress','review_pending','blocked'},'block':{'ready','in_progress','review_pending'},'resume':{'deferred','blocked'}}
            need(s['workflow'] in allowed[a],'Invalid workflow transition')
            related=[e for e in events if e['kind']=='action' and e['subject']==request['subject'] and e['snapshot']==s['snapshot']]
            if a in {'authorize','accept'}:
                contributors={e['actor'] for e in related if e['action'] in {'propose','start','submit'}}
                need(actor not in contributors,'Proposer/implementer cannot approve own work')
            if a in {'start','submit','accept'}:need(not s['dependency_blocked'],'Prerequisite not accepted')
            if a in {'submit','accept'} and objects[request['subject']]['acceptance_class']!='human_verifiable':need(s['verification']=='passed','Current version-bound required Run must pass')
            value=dict(kind='action',key=request['key'],subject=request['subject'],action=a,actor=actor,role=role,revision=s['revision']+1,snapshot=s['snapshot'],reason=request['reason'],request_digest=digest,observed_at=datetime.now(timezone.utc).isoformat())
            seq=self.append(db,value);return {'outcome':'recorded','seq':seq,'revision':value['revision']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path.cwd());sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('init');p.add_argument('--config',required=True)
    p=sub.add_parser('collect');p.add_argument('--key',required=True)
    p=sub.add_parser('view');p.add_argument('--query',default='');p.add_argument('--kind');p.add_argument('--state')
    p=sub.add_parser('act');p.add_argument('--request',required=True)
    p=sub.add_parser('account');p.add_argument('--username',required=True)
    p=sub.add_parser('login');p.add_argument('--username',required=True)
    p=sub.add_parser('backup');p.add_argument('--out',required=True)
    p=sub.add_parser('restore');p.add_argument('--backup',type=Path,required=True)
    args=parser.parse_args();w=Workspace(args.root)
    try:
        if args.cmd=='init':result=w.initialize(args.config)
        elif args.cmd=='collect':result=w.collect(args.key)
        elif args.cmd=='backup':result=w.backup(args.out)
        elif args.cmd=='restore':result=w.restore(args.backup)
        elif args.cmd in {'account','login'}:
            import getpass
            with closing(w.connect()) as db:config=w.config(db)
            need(config['access_mode']=='authenticated' and args.username in config['principals'],'Unapproved principal')
            accounts=component('wiki_access').Accounts(local(w.root,config['accounts']),config['roles'],sha(encoded(config)));password=getpass.getpass('Local account password: ')
            if args.cmd=='login':
                token=accounts.login(args.username,password);need(token,'Login rejected');print(token);return 0
            if accounts.path.exists():accounts.add_account(args.username,config['principals'][args.username],password)
            else:accounts.provision(args.username,config['principals'][args.username],password)
            result={'outcome':'account_created'}
        else:
            with closing(w.connect()) as db:offline=w.config(db)['access_mode']=='loopback_read_only'
            if args.cmd=='view' and offline:result=w.read_only_view(args.query,args.kind,args.state)
            else:
                token=sys.stdin.readline().strip()
                result=w.view(token,args.query,args.kind,args.state) if args.cmd=='view' else w.act(token,strict(local(w.root,args.request).read_bytes()))
        print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,OSError,sqlite3.Error):print(json.dumps({'outcome':'blocked','reason':'Configuration, authentication, evidence or action contract rejected'}));return 2

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
