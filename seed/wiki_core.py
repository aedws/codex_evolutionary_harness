"""Project-owned document tree and explicit, interview-bound read policy. No fixed roles."""
import hashlib
import html
import json
import re
from pathlib import PurePosixPath

PROFILE = 'wiki-tree-access-1'
ACTIONS = {'read', 'edit', 'approve', 'execute'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def validate(contract):
    require(type(contract) is dict and set(contract) == {'schema_version', 'profile', 'interview', 'roles', 'access', 'nodes', 'root', 'adapter'}, 'Wiki tree fields missing/unsupported')
    require(type(contract['schema_version']) is int and contract['schema_version'] == 1 and contract['profile'] == PROFILE, 'Unsupported wiki tree version')
    interview = contract['interview']
    require(type(interview) is dict and set(interview) == {'status', 'decision_ref', 'policy_digest'}, 'Owner interview record required')
    require(interview['status'] == 'confirmed' and type(interview['decision_ref']) is str and interview['decision_ref'].strip(), 'Owner interview pending; do not grant access')
    roles = contract['roles']
    require(type(roles) is dict and 1 <= len(roles) <= 32, 'Owner must select project roles')
    for ident, label in roles.items():
        require(re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', ident) and type(label) is str and label.strip(), 'Invalid project role')
    adapter = contract['adapter']
    require(type(adapter) is dict and set(adapter) == {'kind', 'source_paths', 'test_paths', 'required_tests'}, 'Access adapter binding missing')
    require(adapter['kind'] == 'authenticated_read_only', 'Unimplemented access adapter; writes remain denied')
    for key in ['source_paths', 'test_paths', 'required_tests']:
        require(type(adapter[key]) is list and adapter[key] and all(type(p) is str and p for p in adapter[key]), 'Adapter sources/tests required')
    nodes = contract['nodes']
    require(type(nodes) is list and 3 <= len(nodes) <= 10000, 'Document hierarchy required')
    by_id = {}; pages = set()
    for node in nodes:
        require(type(node) is dict and set(node) == {'id', 'title', 'parent', 'page', 'grants'}, 'Node shape invalid')
        ident = node['id']; page = node['page']
        require(type(ident) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', ident) and ident not in by_id, 'Duplicate/unsafe node ID')
        require(type(node['title']) is str and node['title'].strip(), 'Document purpose/title required')
        require(type(page) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.html', page) and page not in pages, 'Duplicate/unsafe page')
        require(node['parent'] is None or type(node['parent']) is str, 'Invalid parent')
        grants = node['grants']
        require(type(grants) is dict and set(grants) == ACTIONS, 'Separate read/edit/approve/execute grants required')
        for action, values in grants.items():
            require(type(values) is list and all(type(v) is str and v in roles for v in values) and len(values) == len(set(values)), 'Unknown/duplicate permission role')
            require(action == 'read' or not values, 'Write/approval/execution adapter absent; cannot grant action')
        require(bool(grants['read']), 'Document has no authorized reader')
        by_id[ident] = node; pages.add(page)
    root = contract['root']
    require(type(root) is str and root in by_id and [n['id'] for n in nodes if n['parent'] is None] == [root], 'Exactly one document root required')
    access = contract['access']
    require(type(access) is dict and set(access) == {'root_read', 'overrides'} and type(access['overrides']) is dict, 'Interview-bound access inheritance required')
    require(set(access['overrides']) <= set(by_id), 'Access override target missing')
    for node in nodes:
        inherited = access['root_read'] if node['parent'] is None else by_id.get(node['parent'], {}).get('grants', {}).get('read')
        require(node['grants']['read'] == access['overrides'].get(node['id'], inherited), 'Node grants differ from approved inheritance policy')
    depths = []
    for node in nodes:
        current = node; seen = set()
        while current['parent'] is not None:
            require(current['id'] not in seen, 'Document hierarchy cycle'); seen.add(current['id'])
            require(current['parent'] in by_id, 'Missing document parent')
            parent = by_id[current['parent']]
            require(set(current['grants']['read']) <= set(parent['grants']['read']), 'Child access broadens parent policy')
            current = parent
        depths.append(len(seen))
    require(max(depths) >= 2, 'Large document -> topic -> detail hierarchy required')
    policy = {'roles': roles, 'access': access, 'adapter_kind': adapter['kind']}
    require(interview['policy_digest'] == hashlib.sha256(canonical(policy)).hexdigest(), 'Owner-approved permissions changed; interview again')
    return by_id


def policy_digest(contract):
    return hashlib.sha256(canonical({'roles': contract['roles'], 'access': contract['access'], 'adapter_kind': contract['adapter']['kind']})).hexdigest()


def allowed(contract, ident, role, action='read'):
    nodes = validate(contract)
    return role in contract['roles'] and ident in nodes and action in ACTIONS and role in nodes[ident]['grants'][action]


def navigation(contract, ident, role):
    nodes = validate(contract)
    require(ident in nodes and role in nodes[ident]['grants']['read'], 'Forbidden document')
    trail = []; current = nodes[ident]
    while current is not None:
        trail.append(current); current = nodes.get(current['parent'])
    def link(node):
        return '<a href="' + html.escape(node['page'], quote=True) + '">' + html.escape(node['title']) + '</a>'
    crumbs = ' / '.join(link(n) for n in reversed(trail))
    children = [n for n in contract['nodes'] if n['parent'] == ident and role in n['grants']['read']]
    return '<nav aria-label="상위 문서 경로">' + crumbs + '</nav><section><h2>하위 문서</h2><ul>' + ''.join('<li>'+link(n)+'</li>' for n in children) + '</ul></section>'


def inspect_artifacts(root, binding, load_path):
    """Binding adapter for bootstrap.py; hashes are checked by its outer gate."""
    reference = binding['wiki_contract']
    require(reference in binding['input_sha256'], 'Wiki contract must be hash-bound')
    contract = json.loads(load_path(root, reference).read_bytes()); nodes = validate(contract)
    paths = [contract['interview']['decision_ref'], *contract['adapter']['source_paths'], *contract['adapter']['test_paths']]
    require(all(p in binding['input_sha256'] for p in paths), 'Interview, adapter and negative tests must be hash-bound')
    require(set(n['page'] for n in nodes.values()) == {PurePosixPath(p).name for p in binding['documents']}, 'Tree must cover every canonical document exactly')
    for role in contract['roles']:
        for node in nodes.values():
            if role in node['grants']['read']:
                relative = 'docs/wiki/roles/' + role + '/' + node['page']
                require(relative in binding['input_sha256'], 'Role-filtered document missing')
                raw = load_path(root, relative).read_text(encoding='utf-8')
                require(navigation(contract, node['id'], role) in raw, 'Derived hierarchy navigation missing/stale')
                for href in re.findall(r'href="([^"]+)"', raw):
                    if href.startswith('#'):
                        continue
                    targets = [n for n in nodes.values() if n['page'] == href]
                    require(len(targets) == 1 and role in targets[0]['grants']['read'], 'Role view leaks forbidden or ungoverned link')
    return contract
