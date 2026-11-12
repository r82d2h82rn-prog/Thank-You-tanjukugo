#!/usr/bin/env python3
"""Verify append-only authoring against the committed handover snapshot."""
import argparse
import collections
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = 'eaf6e063c7fb48040036a733cd4f484ada4815ce'
CATALOG = 'content/words/drafts.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def verify(root=ROOT):
    def original(path):
        return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=root)
    before = json.loads(original(CATALOG))
    current = json.loads((root / CATALOG).read_text())
    by_id = {entry['id']: entry for entry in current}
    assert len(by_id) == len(current), 'Duplicate draft ID'
    assert len({e['english'].strip().casefold() for e in current}) == len(current), 'Duplicate headword'
    for entry in before:
        assert by_id.get(entry['id']) == entry, f"Existing content changed: {entry['id']}"
    protected = ['src/data/entries.json', 'content/provenance.json',
                 'content/words/approved.json', 'content/idioms/approved.json',
                 'content/readings/approved.json']
    for path in protected:
        assert (root / path).read_bytes() == original(path), f'Protected file changed: {path}'
    old_ids = {e['id'] for e in before}
    added = [e for e in current if e['id'] not in old_ids]
    return dict(baselineCommit=BASE, baselineDrafts=len(before),
                preservedDrafts=len(before), addedDrafts=len(added), totalDrafts=len(current),
                levels=[sum(e['level'] == n for e in current) for n in range(1, 5)],
                baselineItemsSha256=digest(before), currentItemsSha256=digest(current),
                protectedFilesUnchanged=protected, existingItemsUnchanged=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path)
    args = parser.parse_args()
    report = verify()
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    print(text)
