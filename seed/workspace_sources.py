"""Compile approved records into intent, never into verified/accepted state.

JSON records and Markdown tables share an explicit, hash-bound mapping recipe.
No network calls, source edits, credentials, inferred execution or hidden writes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import workspace as w


def clean(value):
    value=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',value)
    return re.sub(r'\s+',' ',value.replace('`','').replace('**','')).strip()


def rows(raw, spec):
    if spec['format']=='json_records':
        value=w.strict(raw)
        for part in spec['selector'].split('.') if spec['selector'] else []:
            w.need(type(value) is dict and part in value,'Record selector missing');value=value[part]
        w.need(type(value) is list and len(value)<=1000,'Record list budget exceeded')
        return value
    w.need(spec['format']=='markdown_table' and spec['selector']=='','Unsupported source format')
    result=[]
    for line in raw.decode('utf-8-sig').splitlines():
        if not line.lstrip().startswith('|'):continue
        cells=[clean(c) for c in line.strip().strip('|').split('|')]
        # An explicit ID prefix distinguishes data rows from headings/separators.
        if not cells or not any(cells[0].startswith(p) for p in spec['row_prefixes']):continue
        result.append({str(i):v for i,v in enumerate(cells)})
    w.need(len(result)<=1000,'Table budget exceeded');return result


def compile_registry(root, policy_path, recipe_path):
    root=Path(root);config=w.policy(w.strict(w.local(root,policy_path).read_bytes()))
    sources=w.inventory(root,config)
    w.need(recipe_path in sources,'Recipe must be an approved source')
    recipe=w.strict(w.local(root,recipe_path).read_bytes())
    w.need(type(recipe) is dict and set(recipe)=={'schema_version','inputs','relations'} and recipe['schema_version']==1,'Recipe shape differs')
    w.need(type(recipe['inputs']) is list and 1<=len(recipe['inputs'])<=32,'Input budget exceeded')
    objects=[];contracts={};ids=set();derived=[]
    for spec in recipe['inputs']:
        w.need(type(spec) is dict and set(spec)=={'path','format','selector','prefix','type','fields','row_prefixes'},'Mapping fields differ')
        path=spec['path'];w.need(path in sources,'Unapproved input')
        w.need(w.ident(spec['prefix']) and spec['type'] in w.TYPES,'Invalid mapped type/namespace')
        w.need(spec['format'] in {'json_records','markdown_table'} and type(spec['selector']) is str and len(spec['selector'])<=4000,'Invalid format/selector')
        w.need(type(spec['row_prefixes']) is list and all(w.text(p) for p in spec['row_prefixes']),'Row prefixes required')
        if spec['format']=='markdown_table':w.need(spec['row_prefixes'],'Table requires explicit row prefixes')
        fields=spec['fields'];w.need(type(fields) is dict and set(fields)=={'id','title','purpose','acceptance','owner','declared_state'},'Explicit field mapping required')
        w.need(all(v is None or w.text(v) for v in fields.values()),'Invalid field selector')
        w.need(all(fields[k] is not None for k in ['id','title','purpose']),'Identity/title/purpose mapping required')
        raw=w.local(root,path).read_bytes();w.need(w.sha(raw)==sources[path]['sha256'],'Input changed during compilation')
        for row in rows(raw,spec):
            w.need(type(row) is dict,'Record must be an object')
            def field(name, default='unknown'):
                key=fields[name]
                if key is None:return default
                w.need(key in row and w.text(row[key]),'Mapped field missing/non-text: '+name)
                return row[key]
            native=field('id').split(' · ',1)[0] if spec['format']=='markdown_table' else field('id')
            ident=spec['prefix']+hashlib.sha256(native.encode()).hexdigest()[:24]
            w.need(w.ident(ident) and ident not in ids,'Duplicate mapped identity');ids.add(ident)
            obj=dict(id=ident,type=spec['type'],title=field('title'),purpose=field('purpose'),sources=sorted({path,recipe_path}),depends_on=[],task_id=None,acceptance_class='mixed')
            objects.append(obj)
            contracts[ident]={'native_id':native,'owner':field('owner'),'acceptance':[field('acceptance')],'source_revision':sources[path]['sha256'],'declared_state':field('declared_state')}
            derived.append({'id':'REL-'+w.sha((ident+'\0'+path).encode())[:24],'from':ident,'to':sources[path]['id'],'type':'documented_by','basis':'inferred_by_static_analysis','sources':sorted({path,recipe_path})})
    w.need(objects and len(objects)<=1000,'No mapped objects or population exceeded')
    # Explicit relation endpoints use mapped stable IDs; missing endpoints fail
    # at collection instead of silently dropping facts or inventing target nodes.
    w.need(type(recipe['relations']) is list,'Explicit relations must be a list')
    output={'schema_version':2,'objects':sorted(objects,key=lambda o:o['id']),'contracts':contracts,'relations':sorted(derived+recipe['relations'],key=lambda rel:rel['id'])}
    w.validate_registry(output,sources)
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--policy',required=True);p.add_argument('--recipe',required=True);p.add_argument('--out');p.add_argument('--check',action='store_true');a=p.parse_args()
    value=compile_registry(a.root,a.policy,a.recipe);raw=w.encoded(value)
    if not a.out:sys.stdout.buffer.write(raw+b'\n');return
    path=w.local(a.root,a.out)
    if path.exists():
        w.need(w.encoded(w.strict(path.read_bytes()))==raw,'Registry ownership conflict; preserve old file and review diff')
        print(json.dumps({'outcome':'unchanged','sha256':w.sha(raw)}));return
    w.need(not a.check,'Generated registry missing')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
    print(json.dumps({'outcome':'created','sha256':w.sha(raw)}))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,TypeError) as exc:print(json.dumps({'outcome':'rejected','reason':str(exc)}));raise SystemExit(2)
