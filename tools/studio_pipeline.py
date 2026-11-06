"""Adaptive task evidence gate; recorded host IDs/models are attribution, not authentication.

The manager selects useful participants, stages and checks. Historical five-worker
journals remain compatible; strict-five is an explicit opt-in profile.
"""
import argparse
import json
from pathlib import Path
import time
import review_loop as loop

ROLES = ('implementer', 'reviewer', 'editor', 'verification', 'qa')
STAGES = ('editor', 'verification', 'qa')


def strict_initialize(path, root, participants, scopes, criteria, max_repairs=3):
    if set(participants) != {'coordinator', *ROLES}:
        raise ValueError('Declare coordinator and all five specialist roles')
    ids = [loop.nonempty(p.get('id'), role + ' host ID') for role, p in participants.items()]
    if len({i.casefold() for i in ids}) != 6:
        raise ValueError('All six host IDs must be distinct; roles cannot self-approve')
    for role, person in participants.items():
        expected = 'gpt-6-astra' if role == 'coordinator' else 'gpt-6.1-sol'
        if person.get('model') != expected:
            raise ValueError(role + ' requires explicit model ' + expected)
    data = loop.initialize(path, root, participants['implementer']['id'],
        participants['reviewer']['id'], participants['coordinator']['id'],
        scopes, criteria, ['studio-editor', 'studio-verification', 'studio-qa'], max_repairs)
    data['studio'] = {'participants': participants, 'custody': None}
    loop.save(path, data)
    return data


def load(path):
    data = loop.load(path)
    if 'studio' not in data:
        raise ValueError('Not a studio pipeline journal')
    return data


def actor_for(data, role, actor):
    if data['studio']['participants'][role]['id'] != actor:
        raise ValueError('Actor must be the recorded ' + role + ' specialist')


def strict_submit(path, actor, summary, addressed=(), supersede_pending=False):
    data = load(path)
    if data['studio']['custody']:
        raise ValueError('Release editor custody before changing the source snapshot')
    item = loop.submit(path, actor, summary, addressed, supersede_pending)
    data = load(path)
    item = data['rounds'][-1]
    item['submitted_ns'] = time.time_ns()
    item['stages'] = {}
    item['invalidated_ns'] = {}
    loop.save(path, data)
    return item


def strict_review(path, actor, report):
    load(path)
    return loop.review(path, actor, report)


def approved(data):
    current = loop.require_current(data)
    if not current['review'] or current['review']['verdict'] != 'approve':
        raise ValueError('Current independent code approval is required')
    return current


def strict_custody(path, actor, action):
    data = load(path)
    actor_for(data, 'editor', actor)
    if action == 'acquire':
        current = approved(data)
        if data['studio']['custody']:
            raise ValueError('Editor custody is already held; concurrent owners are forbidden')
        data['studio']['custody'] = {'actor': actor, 'digest': current['snapshot']['digest']}
    elif action == 'release':
        if not data['studio']['custody']:
            raise ValueError('No editor custody to release')
        data['studio']['custody'] = None
    else:
        raise ValueError('Custody action must be acquire or release')
    loop.event(data, 'editor_custody_' + action, actor)
    loop.save(path, data)
    return data['studio']['custody']


def strict_record(path, actor, stage, result, evidence, summary, digest):
    data = load(path)
    if stage not in STAGES:
        raise ValueError('Unknown specialist stage')
    actor_for(data, stage, actor)
    current = approved(data)
    if digest != current['snapshot']['digest']:
        raise ValueError('Stage report must identify the current source digest')
    if result not in ('passed', 'failed', 'not_run'):
        raise ValueError('Invalid stage status')
    if stage == 'editor':
        lease = data['studio']['custody']
        if not lease or lease['actor'] != actor or lease['digest'] != digest:
            raise ValueError('Editor stage requires current exclusive editor custody')
    elif data['studio']['custody']:
        raise ValueError('Release editor custody before downstream stages')
    for preceding in STAGES[:STAGES.index(stage)]:
        previous = current['stages'].get(preceding)
        if not previous or previous['status'] != 'passed' or not evidence_current(previous):
            raise ValueError('Complete current ' + preceding + ' evidence first')
    artifact = Path(evidence).resolve(strict=True)
    if not artifact.is_file() or artifact == Path(path).resolve():
        raise ValueError('Evidence must be a separate regular file')
    if artifact.stat().st_mtime_ns < max(current['submitted_ns'], current['invalidated_ns'].get(stage, 0)):
        raise ValueError('Evidence predates this submission or upstream signoff; rerun the stage')
    # A repeated earlier stage invalidates downstream approvals, even with unchanged source.
    invalidated_ns = time.time_ns()
    for downstream in STAGES[STAGES.index(stage)+1:]:
        current['invalidated_ns'][downstream] = invalidated_ns
        current['stages'].pop(downstream, None)
        current['verification'].pop('studio-' + downstream, None)
    value = {'actor': actor, 'model': data['studio']['participants'][stage]['model'],
        'status': result, 'summary': loop.nonempty(summary, 'stage summary'),
        'source_digest': digest, 'evidence': str(artifact), 'sha256': loop.sha(artifact), 'utc': loop.utc()}
    current['stages'][stage] = value
    current['verification']['studio-' + stage] = value
    loop.event(data, stage + '_recorded', actor, result=value)
    loop.save(path, data)
    return value


def evidence_current(record):
    path = Path(record['evidence'])
    return path.is_file() and loop.sha(path) == record['sha256']


def strict_status(path):
    data = load(path)
    result = loop.status(path)
    result['model_attribution'] = data['studio']['participants']
    reasons = result['reasons']
    if data['studio']['custody']:
        reasons.append('Editor custody is still held')
    if data['rounds']:
        current = data['rounds'][-1]
        for stage in STAGES:
            value = current.get('stages', {}).get(stage)
            if not value or value['status'] != 'passed':
                reasons.append(stage + ': missing or not passed')
            elif not evidence_current(value):
                reasons.append(stage + ': evidence changed or missing')
    result['ready'] = result['ready'] and not reasons
    if not result['ready'] and result['state'] == 'complete':
        result['state'] = 'awaiting_specialists'
    return result



def adaptive(data):
    return data['studio'].get('profile') == 'adaptive'


def validate_plan(root, participants, stages, scopes, criteria, author=None):
    if 'coordinator' not in participants or len(participants) < 2:
        raise ValueError('Declare coordinator and at least one actual selected worker')
    for role, person in participants.items():
        loop.nonempty(role, 'role')
        loop.nonempty(person.get('id'), role + ' actual host ID')
        expected = 'gpt-6-astra' if role == 'coordinator' else 'gpt-6.1-sol'
        if person.get('model') != expected:
            raise ValueError(role + ' requires explicit model ' + expected)
    director = participants['coordinator']['id'].casefold()
    if any(p['id'].casefold() == director for r, p in participants.items() if r != 'coordinator'):
        raise ValueError('A selected worker must differ from the coordinator')
    author = author or ('implementer' if 'implementer' in participants else
                        next((r for r in participants if r not in ('coordinator', 'reviewer')), 'coordinator'))
    if author not in participants or author == 'reviewer':
        raise ValueError('Select a work owner or coordinator baseline; reviewer cannot author its own review')
    if 'reviewer' in participants and participants['reviewer']['id'].casefold() == participants[author]['id'].casefold():
        raise ValueError('Independent reviewer must differ from the work author')
    if not scopes or not criteria:
        raise ValueError('Declare task scopes and acceptance criteria')
    normalized = []
    for scope in scopes:
        target = loop.safe_path(root, scope)
        if not target.exists():
            raise ValueError('Create scoped input/output directory first: ' + scope)
        normalized.append(target.relative_to(root).as_posix())
    names = []
    editor_ids = set()
    for stage in stages:
        name = loop.nonempty(stage.get('name'), 'stage name')
        if name in names:
            raise ValueError('Stage names must be unique')
        if stage.get('owner') not in participants or stage['owner'] == 'coordinator':
            raise ValueError('Stage owner must be a selected worker')
        deps = stage.get('depends_on', [])
        if not isinstance(deps, list) or any(d not in names for d in deps):
            raise ValueError('Dependencies must name preceding selected stages')
        checks = stage.get('checks')
        if not isinstance(checks, list) or not checks or len(set(checks)) != len(checks):
            raise ValueError('Each selected stage needs distinct required check names')
        for check in checks:
            loop.nonempty(check, 'check')
        if stage.get('uses_editor', False):
            editor_ids.add(participants[stage['owner']]['id'])
        names.append(name)
    if len(editor_ids) > 1:
        raise ValueError('One actual worker must own every selected editor stage')
    return {'author': author, 'participants': participants, 'stages': stages,
            'scopes': sorted(set(normalized)),
            'criteria': [loop.nonempty(c, 'criterion') for c in criteria]}


def initialize(path, root, participants, scopes, criteria, max_repairs=3,
               profile='adaptive', stages=None, author=None):
    if profile == 'strict-five':
        return strict_initialize(path, root, participants, scopes, criteria, max_repairs)
    if profile != 'adaptive':
        raise ValueError('Unknown profile')
    path = Path(path).resolve()
    if path.exists():
        raise ValueError('Journal exists; preserve the previous run')
    root = Path(root).resolve(strict=True)
    plan = validate_plan(root, participants, stages or [], scopes, criteria, author)
    if not isinstance(max_repairs, int) or not 0 <= max_repairs <= 20:
        raise ValueError('max_repairs must be between 0 and 20')
    for scope in plan['scopes']:
        target = root / scope
        if target == path or (target.is_dir() and path.is_relative_to(target)):
            raise ValueError('Keep journal outside scoped files')
    people = {'coordinator': participants['coordinator']['id'],
              'implementer': participants[plan['author']]['id']}
    if 'reviewer' in participants:
        people['reviewer'] = participants['reviewer']['id']
    data = {'schema': 1, 'root': str(root), 'participants': people,
            'scopes': plan['scopes'], 'criteria': plan['criteria'],
            'required_checks': [], 'max_repairs': max_repairs, 'rounds': [], 'events': [],
            'studio': {'profile': 'adaptive', 'participants': participants, 'custody': None,
                       'plan': plan, 'plan_version': 1, 'plan_history': []}}
    data['studio']['plan_history'].append({'version': 1, 'utc': loop.utc(),
        'reason': 'Initial manager-selected task plan', 'plan': plan})
    loop.event(data, 'initialized', people['coordinator'])
    loop.save(path, data)
    return data


def revise_plan(path, actor, reason, participants, stages, scopes=None, criteria=None, author=None):
    data = load(path)
    if not adaptive(data):
        raise ValueError('Plan revisions require adaptive profile; historical strict plan is unchanged')
    loop.require_actor(data, actor, ['coordinator'])
    if data['studio']['custody']:
        raise ValueError('Release editor custody before revising plan')
    reason = loop.nonempty(reason, 'plan-change reason')
    plan = validate_plan(Path(data['root']), participants, stages,
                         scopes or data['scopes'], criteria or data['criteria'], author)
    if participants['coordinator']['id'] != actor:
        raise ValueError('Plan update cannot replace its coordinator')
    for scope in plan['scopes']:
        target = Path(data['root']) / scope
        if target == Path(path).resolve() or (target.is_dir() and Path(path).resolve().is_relative_to(target)):
            raise ValueError('Keep journal outside scopes')
    # Preserve the previous verdict/checks and changed acceptance in history.
    studio = data['studio']
    studio['plan_version'] += 1
    studio['plan'] = plan
    studio['participants'] = participants
    studio['plan_history'].append({'version': studio['plan_version'], 'utc': loop.utc(),
        'reason': reason, 'plan': plan})
    data['scopes'], data['criteria'] = plan['scopes'], plan['criteria']
    data['participants'] = {'coordinator': actor, 'implementer': participants[plan['author']]['id']}
    if 'reviewer' in participants:
        data['participants']['reviewer'] = participants['reviewer']['id']
    loop.event(data, 'plan_revised', actor, version=studio['plan_version'], reason=reason)
    loop.save(path, data)
    return plan


def submit(path, actor, summary, addressed=(), supersede_pending=False):
    data = load(path)
    if not adaptive(data):
        return strict_submit(path, actor, summary, addressed, supersede_pending)
    if data['studio']['custody']:
        raise ValueError('Release editor custody before freezing task snapshot')
    loop.require_actor(data, actor, ['implementer', 'coordinator'])
    summary = loop.nonempty(summary, 'snapshot summary')
    addressed = sorted({loop.nonempty(x, 'finding ID') for x in addressed})
    snap = loop.snapshot(data)
    if data['rounds']:
        previous = data['rounds'][-1]
        if len(data['rounds']) > data['max_repairs']:
            raise ValueError('Repair limit reached; report unresolved work')
        changed_plan = previous.get('plan_version') != data['studio']['plan_version']
        if previous['review'] is None:
            if not changed_plan and (not supersede_pending or previous['snapshot']['digest'] == snap['digest']):
                raise ValueError('Pending review; replace only stale snapshot or changed plan')
            expected = set()
        else:
            if supersede_pending:
                raise ValueError('Previous review completed; submit normally')
            expected = {f['id'] for f in previous['review']['findings']}
        if set(addressed) != expected:
            raise ValueError('Address every previous finding ID and no invented IDs')
    elif addressed or supersede_pending:
        raise ValueError('Initial snapshot has no findings to address')
    item = {'number': len(data['rounds']) + 1, 'snapshot': snap,
            'implementation': {'actor': actor, 'summary': summary, 'addressed': addressed},
            'review': None, 'verification': {}}
    data['rounds'].append(item)
    loop.event(data, 'task_snapshot_submitted', actor, round=item['number'],
               digest=snap['digest'], addressed=addressed)
    item.update(submitted_ns=time.time_ns(), stages={}, invalidated_ns={},
                plan_version=data['studio']['plan_version'])
    if 'reviewer' not in data['studio']['participants']:
        item['review'] = {'verdict': 'not_selected', 'findings': [],
                          'summary': 'Independent review was not selected for this task'}
    loop.save(path, data)
    return item


def current_plan_round(data):
    current = loop.require_current(data)
    if current.get('plan_version') != data['studio']['plan_version']:
        raise ValueError('Plan changed; submit a new task snapshot before signoff')
    return current


def adaptive_approved(data):
    current = current_plan_round(data)
    if 'reviewer' in data['studio']['participants']:
        if not current['review'] or current['review']['verdict'] != 'approve':
            raise ValueError('Selected independent review must approve the current snapshot')
    return current


def review(path, actor, report):
    data = load(path)
    if not adaptive(data):
        return strict_review(path, actor, report)
    if 'reviewer' not in data['studio']['participants']:
        raise ValueError('No independent reviewer selected; do not invent one')
    current_plan_round(data)
    return loop.review(path, actor, report)


def editor_owner(data):
    ids = {data['studio']['participants'][s['owner']]['id']
           for s in data['studio']['plan']['stages'] if s.get('uses_editor', False)}
    return next(iter(ids), None)


def custody(path, actor, action):
    data = load(path)
    if not adaptive(data):
        return strict_custody(path, actor, action)
    if actor != editor_owner(data):
        raise ValueError('Only selected editor owner may hold custody')
    if action == 'acquire':
        if data['studio']['custody']:
            raise ValueError('Editor custody already held')
        # Asset work can start before its final content snapshot is submitted.
        data['studio']['custody'] = {'actor': actor}
    elif action == 'release':
        if not data['studio']['custody']:
            raise ValueError('No editor custody to release')
        data['studio']['custody'] = None
    else:
        raise ValueError('Custody action must be acquire or release')
    loop.event(data, 'editor_custody_' + action, actor)
    loop.save(path, data)
    return data['studio']['custody']


def downstream_names(stages, name):
    affected = {name}
    for s in stages:
        if any(d in affected for d in s.get('depends_on', [])):
            affected.add(s['name'])
    return affected - {name}


def record(path, actor, stage, result, evidence, summary, digest, checks=None):
    data = load(path)
    if not adaptive(data):
        return strict_record(path, actor, stage, result, evidence, summary, digest)
    plan = data['studio']['plan']
    selected = next((s for s in plan['stages'] if s['name'] == stage), None)
    if not selected:
        raise ValueError('Stage was not selected for this task')
    actor_for(data, selected['owner'], actor)
    current = adaptive_approved(data)
    if digest != current['snapshot']['digest']:
        raise ValueError('Stage must identify current source/content digest')
    if result not in ('passed', 'failed', 'not_run'):
        raise ValueError('Invalid stage status')
    if not isinstance(checks, dict) or set(checks) != set(selected['checks']):
        raise ValueError('Report every selected required check, and no invented checks')
    if any(v not in ('passed', 'failed', 'not_run') for v in checks.values()):
        raise ValueError('Invalid check status')
    if result == 'passed' and any(v != 'passed' for v in checks.values()):
        raise ValueError('Passed stage requires all selected checks passed')
    lease = data['studio']['custody']
    if selected.get('uses_editor', False):
        if not lease or lease['actor'] != actor:
            raise ValueError('Editor stage requires exclusive editor custody')
    elif lease:
        raise ValueError('Release editor custody before non-editor signoff')
    for dependency in selected.get('depends_on', []):
        prev = current['stages'].get(dependency)
        if not prev or prev['status'] != 'passed' or not evidence_current(prev):
            raise ValueError('Complete current dependency evidence first: ' + dependency)
    artifact = Path(evidence).resolve(strict=True)
    if not artifact.is_file() or artifact == Path(path).resolve():
        raise ValueError('Evidence must be a separate regular file')
    if artifact.stat().st_mtime_ns < max(current['submitted_ns'], current['invalidated_ns'].get(stage, 0)):
        raise ValueError('Evidence predates snapshot or upstream signoff; rerun selected checks')
    value = {'actor': actor, 'model': data['studio']['participants'][selected['owner']]['model'],
             'status': result, 'checks': checks, 'summary': loop.nonempty(summary, 'summary'),
             'source_digest': digest, 'evidence': str(artifact), 'sha256': loop.sha(artifact), 'utc': loop.utc()}
    for name in downstream_names(plan['stages'], stage):
        current['stages'].pop(name, None)
        current['invalidated_ns'][name] = time.time_ns()
    current['stages'][stage] = value
    loop.event(data, 'stage_recorded', actor, stage=stage, result=value)
    loop.save(path, data)
    return value


def status(path):
    data = load(path)
    if not adaptive(data):
        return strict_status(path)
    result = {'ready': False, 'state': 'awaiting_snapshot', 'reasons': [],
              'round': len(data['rounds']), 'model_attribution': data['studio']['participants'],
              'profile': 'adaptive', 'plan_version': data['studio']['plan_version']}
    if not data['rounds']:
        return result
    current = data['rounds'][-1]
    result['digest'] = current['snapshot']['digest']
    if current.get('plan_version') != data['studio']['plan_version']:
        result.update(state='plan_changed', reasons=['New plan requires fresh snapshot/signoffs'])
        return result
    if loop.snapshot(data)['digest'] != result['digest']:
        result.update(state='stale', reasons=['Scoped source/content changed'])
        return result
    if 'reviewer' in data['studio']['participants']:
        if not current['review']:
            result['state'] = 'awaiting_review'
            return result
        if current['review']['verdict'] != 'approve':
            result.update(state='changes_requested', reasons=[f['id'] for f in current['review']['findings']])
            return result
    for stage in data['studio']['plan']['stages']:
        value = current['stages'].get(stage['name'])
        if not value or value['status'] != 'passed':
            result['reasons'].append(stage['name'] + ': missing or not passed')
        elif not evidence_current(value):
            result['reasons'].append(stage['name'] + ': evidence changed or missing')
    if data['studio']['custody']:
        result['reasons'].append('Editor custody still held')
    result['ready'] = not result['reasons']
    result['state'] = 'complete' if result['ready'] else 'awaiting_selected_checks'
    return result

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('init')
    init.add_argument('--participants', required=True, help='JSON map of role to {id, model}; actual host IDs')
    init.add_argument('--root', required=True)
    init.add_argument('--scope', action='append', required=True)
    init.add_argument('--criterion', action='append', required=True)
    init.add_argument('--max-repairs', type=int, default=3)
    init.add_argument('--profile', choices=['adaptive', 'strict-five'], default='adaptive')
    init.add_argument('--plan', help='JSON {stages: [...], author: optional selected role}')
    change = sub.add_parser('plan')
    change.add_argument('--participants', required=True)
    change.add_argument('--plan', required=True)
    change.add_argument('--reason', required=True)
    change.add_argument('--scope', action='append')
    change.add_argument('--criterion', action='append')
    submit_p = sub.add_parser('submit')
    submit_p.add_argument('--summary', required=True)
    submit_p.add_argument('--addressed', action='append', default=[])
    submit_p.add_argument('--supersede-pending', action='store_true')
    review_p = sub.add_parser('review')
    review_p.add_argument('--report', required=True)
    custody_p = sub.add_parser('custody')
    custody_p.add_argument('--operation', choices=['acquire', 'release'], required=True)
    record_p = sub.add_parser('record')
    record_p.add_argument('--stage', required=True)
    record_p.add_argument('--checks', help='JSON file mapping selected check names to passed/failed/not_run')
    record_p.add_argument('--status', choices=['passed', 'failed', 'not_run'], required=True)
    for name in ('evidence', 'summary', 'digest'):
        record_p.add_argument('--' + name, required=True)
    for p in (submit_p, review_p, custody_p, record_p, change):
        p.add_argument('--actor', required=True)
    sub.add_parser('status')
    sub.add_parser('gate')
    a = parser.parse_args(argv)
    try:
        if a.action == 'init':
            plan = json.loads(Path(a.plan).read_text(encoding='utf-8-sig')) if a.plan else {}
            result = initialize(a.journal, a.root, json.loads(Path(a.participants).read_text(encoding='utf-8-sig')),
                                a.scope, a.criterion, a.max_repairs, a.profile, plan.get('stages'), plan.get('author'))
        elif a.action == 'plan':
            plan = json.loads(Path(a.plan).read_text(encoding='utf-8-sig'))
            result = revise_plan(a.journal, a.actor, a.reason,
                json.loads(Path(a.participants).read_text(encoding='utf-8-sig')),
                plan['stages'], a.scope, a.criterion, plan.get('author'))
        elif a.action == 'submit':
            result = submit(a.journal, a.actor, a.summary, a.addressed, a.supersede_pending)
        elif a.action == 'review':
            result = review(a.journal, a.actor, json.loads(Path(a.report).read_text(encoding='utf-8-sig')))
        elif a.action == 'custody':
            result = custody(a.journal, a.actor, a.operation)
        elif a.action == 'record':
            result = record(a.journal, a.actor, a.stage, a.status, a.evidence, a.summary, a.digest,
                            json.loads(Path(a.checks).read_text(encoding='utf-8-sig')) if a.checks else None)
        else:
            result = status(a.journal)
        print(json.dumps(result, indent=2))
        return int(a.action == 'gate' and not result['ready'])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
