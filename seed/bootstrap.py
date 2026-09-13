"""Mandatory local bootstrap artifact gate; independent of the pinned execution ledger engine."""
from pathlib import Path, PurePosixPath
from html.parser import HTMLParser
import argparse
import hashlib
import json
import re
import sys
from urllib.parse import unquote, urlsplit

PROFILE = "bootstrap-wiki-1"
CATEGORIES = {"onboarding", "product", "design_data", "architecture_modules", "tools_workflows",
              "verification_troubleshooting", "decisions", "release_history", "role_workspaces"}
TYPES = {"requirement", "task", "decision", "module", "test", "release"}


class BootstrapError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise BootstrapError(message)


def strict(raw):
    def pairs(items):
        out = {}
        for key,value in items:
            need(key not in out, "Duplicate JSON key");out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(BootstrapError('Nonfinite JSON')))


def text(value):
    need(type(value) is str and bool(value.strip()), "Required text missing")


def path(root, name):
    text(name);p = PurePosixPath(name)
    need(bool(p.parts) and not p.is_absolute() and p.as_posix()==name and ':' not in name and '\\' not in name
         and all(x not in {'.','..'} and x.rstrip(' .')==x for x in p.parts), "Unsafe bootstrap path")
    target = root/name
    for part in (target,*target.parents):
        if part.exists():
            st=part.lstat();need(not part.is_symlink() and not getattr(st,'st_file_attributes',0)&0x400, "Reparse path forbidden")
    need(target.is_file(), "Required artifact missing: "+name)
    need(target.stat().st_size<=16*1024*1024, "Artifact too large")
    return target


class Links(HTMLParser):
    def __init__(self):super().__init__();self.values=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a':self.values.extend(v for k,v in attrs if k=='href' and v)


def artifacts(root, binding):
    root=Path(root).absolute()
    required={'schema_version','profile','entrypoint','documents','categories','object_views','relations','journeys','input_sha256','validation_task'}
    need(type(binding) is dict and set(binding)==required, "Bootstrap binding fields missing/unsupported")
    need(type(binding['schema_version']) is int and binding['schema_version']==1 and binding['profile']==PROFILE, "Unsupported bootstrap profile")
    docs=binding['documents'];need(type(docs) is list and len(docs)>=3 and all(type(n) is str for n in docs), "Wiki document population required")
    need(len(docs)==len(set(docs)) and binding['entrypoint'] in docs, "Duplicate documents or missing entrypoint")
    hashes=binding['input_sha256'];need(type(hashes) is dict and set(docs)<=set(hashes), "Every wiki artifact must be hash-bound")
    for name,expected in hashes.items():
        need(type(expected) is str and re.fullmatch('[0-9a-f]{64}',expected), "Invalid input hash")
        need(hashlib.sha256(path(root,name).read_bytes()).hexdigest()==expected, "Bootstrap input stale: "+name)
    graph={name:set() for name in docs}
    for name in docs:
        raw=path(root,name).read_text(encoding='utf-8-sig')
        if name.endswith(('.html','.htm')):
            parser=Links();parser.feed(raw);links=parser.values
        elif name.endswith('.md'):links=re.findall(r'\]\(([^\s)]+)\)',raw)
        else:raise BootstrapError('Wiki documents must be Markdown or HTML')
        for href in links:
            parsed=urlsplit(href)
            if parsed.scheme or parsed.netloc or not parsed.path:continue
            target=(root/name).parent.joinpath(unquote(parsed.path)).resolve()
            need(target.is_relative_to(root.resolve()), "Wiki link escapes project")
            rel=target.relative_to(root.resolve()).as_posix()
            need(target.is_file(), "Broken wiki link: "+rel)
            if rel in graph:graph[name].add(rel)
    def reachable(start):
        seen=set();pending=[start]
        while pending:
            n=pending.pop()
            if n not in seen:seen.add(n);pending.extend(graph[n]-seen)
        return seen
    need(reachable(binding['entrypoint'])==set(docs), "Orphan wiki documents")
    cats=binding['categories'];need(type(cats) is dict and set(cats)==CATEGORIES, "All nine navigation categories are mandatory")
    for pages in cats.values():need(type(pages) is list and pages and all(p in graph for p in pages), "Category must resolve to documents")
    views=binding['object_views'];need(type(views) is list and views, "Object views missing")
    ids=set();types=set()
    for v in views:
        need(type(v) is dict and set(v)=={'id','type','path','purpose','source_refs','next_action','rule','acceptance_class','unknowns'}, "View explanation fields missing")
        for key in ('id','type','purpose','next_action','rule'):text(v[key])
        need(v['id'] not in ids and v['path'] in docs, "Duplicate object or unresolved view")
        ids.add(v['id']);types.add(v['type'])
        need(v['id'] in path(root,v['path']).read_text(encoding='utf-8-sig'), "View does not expose its object ID")
        need(type(v['source_refs']) is list and v['source_refs'] and all(s in hashes for s in v['source_refs']), "View source must be hash-bound")
        need(v['acceptance_class'] in {'machine_verifiable','human_verifiable','mixed'} and type(v['unknowns']) is list, "View acceptance/uncertainty missing")
    need(TYPES<=types, "Six governed object types are mandatory")
    relations=binding['relations'];need(type(relations) is list and relations, "Relationships missing")
    for r in relations:
        need(type(r) is dict and set(r)=={'from','to','basis'}, "Relation fields missing")
        need(r['from'] in ids and r['to'] in ids, "Relation endpoint missing")
        need(r['basis'] in {'confirmed_by_code','confirmed_by_test','confirmed_by_runtime','confirmed_by_user','inferred_by_static_analysis','inferred_by_llm','unknown'}, "Unknown relation provenance")
    journeys=binding['journeys'];need(type(journeys) is list and {j.get('role') for j in journeys}=={'owner','developer','reviewer'}, "Three role journeys required")
    for j in journeys:
        route=j['paths'];need(type(route) is list and len(route)>=3 and len(set(route))==len(route) and all(n in docs for n in route), "Journey must include three distinct documents")
        need(all(b in reachable(a) for a,b in zip(route,route[1:])), "Journey not navigable")
    text(binding['validation_task'])
    return {'profile':PROFILE,'state':'wiki_ready','documents':len(docs),'objects':len(views),
            'binding_digest':hashlib.sha256(json.dumps(binding,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
            'limits':['Artifact completeness/integrity/navigation, not semantic quality or authenticated human acceptance.',
                      'Generic harness run passes do not imply bootstrap_ready; this gate is required.']}


def evaluate(root, binding):
    result=artifacts(root,binding)
    import importlib.util
    spec=importlib.util.spec_from_file_location('bootstrap_runtime',Path(root)/'harness.py')
    runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
    try:state=runtime.Core(root).status(binding['validation_task'])
    except runtime.HarnessError as exc:raise BootstrapError(str(exc)) from exc
    need(state['verification']=='passed', 'Bootstrap validation task is not currently passed: '+state['verification'])
    result.update(state='bootstrap_ready',validation_task=binding['validation_task'],event_head=state['event_head'],human_acceptance=state['acceptance'])
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--binding',type=Path,required=True);parser.add_argument('--artifacts-only',action='store_true');args=parser.parse_args()
    try:
        value=strict(args.binding.read_bytes());result=(artifacts if args.artifacts_only else evaluate)(args.root,value)
        print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'state':'bootstrap_partial','reason':str(exc),'profile':PROFILE},ensure_ascii=False));return 6


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');raise SystemExit(main())
