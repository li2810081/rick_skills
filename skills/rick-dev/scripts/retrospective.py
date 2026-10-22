"""Publish reviewed, sanitized rick-dev feedback; offline preview is default."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

DEFAULT_REPO = 'li2810081/rick_skills'


def gh(*args, payload=None):
    command = ['gh', 'api', *args]
    if payload is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True, encoding='utf-8', timeout=90)
    if result.returncode:
        raise RuntimeError('GitHub request failed; no verified receipt. Check network/auth and remote before retrying.')
    return json.loads(result.stdout)


def pages(endpoint):
    result = gh('--paginate', '--slurp', endpoint)
    if not isinstance(result, list) or not all(isinstance(page, list) for page in result):
        raise ValueError('Unexpected pagination response')
    return [item for page in result for item in page]


def validate(report):
    if not isinstance(report, dict):
        raise ValueError('Report must be an object')
    for key in ('key', 'title', 'body'):
        if not isinstance(report.get(key), str) or not report[key].strip():
            raise ValueError('Missing text field: ' + key)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,79}', report['key']):
        raise ValueError('key must be a stable lowercase failure-pattern slug (3-80 characters)')
    if len(report['title']) > 180 or len(report['body']) > 30000:
        raise ValueError('Report too long; use a sanitized summary, not raw transcripts')
    # ponytail: basic leak tripwire only; semantic privacy review remains mandatory.
    if re.search(r'gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY-----', report['title'] + '\n' + report['body']):
        raise ValueError('Possible credential; remove it before continuing')
    return report


def prepare(report):
    report = validate(report)
    pattern = '<!-- rick-dev-pattern:' + report['key'] + ' -->'
    digest = hashlib.sha256(json.dumps(report, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    event = '<!-- rick-dev-report:' + digest + ' -->'
    body = pattern + '\n' + event + '\n\n' + report['body']
    return pattern, event, '[rick-dev] ' + report['title'], body


def candidates(repo):
    return [i for i in pages('repos/' + repo + '/issues?state=all&per_page=100')
            if 'pull_request' not in i and ('[rick-dev]' in i.get('title', '')
                                          or '<!-- rick-dev-pattern:' in (i.get('body') or ''))]


def publish(repo, report, issue=None):
    pattern, event, title, body = prepare(report)
    # Full pagination avoids treating a truncated issue list as proof of no duplicate.
    all_issues = pages('repos/' + repo + '/issues?state=all&per_page=100')
    same = []
    for item in all_issues:
        if 'pull_request' in item:
            continue
        matched = pattern in (item.get('body') or '')
        if not matched and item.get('comments', 0):
            comments = pages('repos/' + repo + '/issues/' + str(item['number']) + '/comments?per_page=100')
            matched = any(pattern in c.get('body', '') for c in comments)
        if matched:
            same.append(item)
    if issue is not None:
        target = gh('repos/' + repo + '/issues/' + str(issue))
        if 'pull_request' in target or '[rick-dev]' not in target.get('title', ''):
            raise ValueError('Selected target is not a rick-dev feedback issue')
    else:
        if len(same) > 1:
            raise ValueError('Multiple matching issues; review threads and pass --issue explicitly')
        target = same[0] if same else None
    if target:
        endpoint = 'repos/' + repo + '/issues/' + str(target['number'])
        comments = pages(endpoint + '/comments?per_page=100')
        previous = [c for c in comments if event in c.get('body', '')]
        if event in (target.get('body') or '') or previous:
            return dict(action='already_present', issue=target['html_url'],
                        evidence=previous[0]['html_url'] if previous else target['html_url'])
        comment = gh(endpoint + '/comments', payload={'body': body})
        saved = gh('repos/' + repo + '/issues/comments/' + str(comment['id']))
        if saved.get('body') != body:
            raise RuntimeError('Comment write not confirmed; inspect remote before retrying')
        return dict(action='commented', issue=target['html_url'], evidence=saved['html_url'], state=target['state'])
    created = gh('repos/' + repo + '/issues', payload={'title': title, 'body': body,
                                                     'labels': [], 'assignees': []})
    saved = gh('repos/' + repo + '/issues/' + str(created['number']))
    if saved.get('body') != body or saved.get('title') != title:
        raise RuntimeError('Issue write not confirmed; inspect remote before retrying')
    return dict(action='created', issue=saved['html_url'], evidence=saved['html_url'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', nargs='?', type=Path)
    parser.add_argument('--repo', default=DEFAULT_REPO)
    parser.add_argument('--candidates', action='store_true', help='Read-only issue titles for agent triage')
    parser.add_argument('--issue', type=int, help='Existing semantic match, selected after reading thread')
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--reviewed', action='store_true', help='Caller confirms authorization and sanitized content')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        parser.error('repo must be OWNER/REPO')
    if args.issue is not None and args.issue < 1:
        parser.error('issue must be positive')
    if args.publish and args.candidates:
        parser.error('candidates is read-only; do not combine with publish')
    if args.candidates:
        rows = candidates(args.repo)
        print(json.dumps([dict(number=i['number'], title=i['title'], state=i['state'], url=i['html_url']) for i in rows], ensure_ascii=False))
        return 0
    if args.report is None:
        parser.error('report JSON required')
    report = validate(json.loads(args.report.read_text(encoding='utf-8-sig')))
    if not args.publish:
        _, _, title, body = prepare(report)
        print(json.dumps(dict(action='preview', repo=args.repo, title=title, body=body), ensure_ascii=False))
        return 0
    if not args.reviewed:
        parser.error('publish requires --reviewed after authorization and privacy review')
    print(json.dumps(publish(args.repo, report, args.issue), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
