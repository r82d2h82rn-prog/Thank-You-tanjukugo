"""Resolve only level 3/4 placements; level 1/2 source records are used unchanged."""
from content_pipeline import read_json

def authored_catalog(root):
    original=read_json(root/'content/words/drafts.json')
    overlay=root/'content/words/selection.json'
    if not overlay.exists():return original
    additions=read_json(root/'content/words/reselected_additions.json')
    selection=read_json(overlay)
    for name in selection.get('additionalBatchFiles',[]):
        if not name.startswith('content/words/advanced_') or not name.endswith('.json'):raise ValueError('Invalid batch path')
        additions+=read_json(root/name)
    all_entries=original+additions
    by_id={e['id']:e for e in all_entries}
    if len(by_id)!=len(all_entries):raise ValueError('Duplicate source ID')
    placements=selection['placements'];ids=[p['id'] for p in placements]
    if len(set(ids))!=len(ids) or any(p['level'] not in (3,4) for p in placements):raise ValueError('Invalid upper-level placement')
    lower=[e for e in original if e['level']<3]
    reserve=[e['id'] for e in original if e['level']>=3 and e['id'] not in ids]
    accounted={e['id'] for e in lower}|set(ids)|set(reserve)
    if accounted!=set(by_id) or len(reserve)!=selection['expectedReservedWords']:raise ValueError('Unaccounted source ID')
    return lower+[{**by_id[p['id']],**p} for p in placements]
