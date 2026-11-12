#!/usr/bin/env python3
"""Read-only legacy archive + independently authored batches -> ID-based placement overlay."""
import csv, hashlib, json, pathlib, sys, collections
from content_pipeline import ROOT, NOW, read_json, write_json, validate_entry, normalized
FIELDS = ['english','pos','pronunciation','meaning','example','translation','explanation']
POS = {'動詞':0,'名詞':1,'形容詞':2,'副詞':3,'その他':4}

def read_new(root=ROOT):
    original=read_json(root/'content/words/drafts.json')
    samples=read_json(root/'src/data/entries.json')
    words={normalized(e['english']) for e in original+samples if e['kind']=='word'}
    sources={s['id']:s for s in read_json(root/'content/sources.json')}
    seen={e['id'] for e in original+samples}; result=[]
    for file in sorted((root/'content/authoring/reselection').glob('batch_*.tsv')):
        with file.open() as stream: rows=list(csv.DictReader(stream,delimiter='\t'))
        if len(rows)!=100: raise ValueError(f'{file.name}: 100語で保存してください')
        for row in rows:
            lemma=normalized(row['english'])
            if lemma in words:raise ValueError('既存語または新規バッチの重複: '+lemma)
            words.add(lemma)
            e={k:row[k] for k in FIELDS}
            e.update(id='word-c-'+hashlib.sha256(lemma.encode()).hexdigest()[:12],kind='word',level=3,section=1,number=1,acceptedAnswers=[],content=dict(sourceIds=['original-draft-v4'],contentVersion=1,qualityStatus='review_required',autoChecked=True,humanReviewed=False,productionApproved=False,examFrequency=None,selectionReason='ユーザー改訂基準：2級中級〜準1級中級を目安とする大学受験重要語として独自選定。個別英検級・入試頻度は未検証。',sourceUsage=[dict(sourceId='original-draft-v4',fields=FIELDS+['proposedLevel'])]))
            errors=validate_entry(e,sources,seen,require_approval=False)
            if errors:raise ValueError((lemma,errors))
            result.append(e)
    return result

def arrange(entries, level):
    # Each section receives a mixed set; each section then follows the specified POS order.
    sections=[[] for _ in range(len(entries)//100)]
    for pos in POS:
        group=[e for e in entries if e['pos']==pos]
        for e in group:
            available=[i for i,s in enumerate(sections) if len(s)<100]
            i=min(available,key=lambda i:(len(sections[i]),i));sections[i].append(e)
    if any(len(s)!=100 for s in sections):raise ValueError('セクション未完成')
    return [dict(id=e['id'],level=level,section=i+1,number=j+1) for i,s in enumerate(sections) for j,e in enumerate(sorted(s,key=lambda e:POS[e['pos']]))]

def build(root=ROOT):
    original=read_json(root/'content/words/drafts.json');policy=read_json(root/'content/authoring/reselection/policy.json');new=read_new(root)
    if len(new)!=500:raise ValueError(f'再選定の補完は500語必要: 現在{len(new)}')
    promote=set(policy['promoteTo4'].split());keep4=set(policy['retainIn4'].split());reserve=set(policy['reserveBelow3'].split())
    assert len(promote)==80 and len(keep4)==20 and len(reserve)==100
    assert not promote&reserve
    by_word={e['english']:e for e in original}
    assert all(by_word[w]['level']==3 for w in promote|reserve)
    assert all(by_word[w]['level']==4 for w in keep4)
    groups={l:[] for l in range(1,5)};decisions=[]
    for e in original:
        old=e['level'];word=e['english']
        level=None if word in reserve else 4 if word in promote else 3 if old==4 and word not in keep4 else old
        if level:groups[level].append(e)
        reason=policy['reserveReason'] if level is None else '準1級中上級以上の専門語・難しい一般語としてLEVEL4へ' if old==3 and level==4 else '受験重要語としてLEVEL3の範囲へ' if old==4 and level==3 else '現LEVELの対象範囲に残す編集判断'
        decisions.append(dict(id=e['id'],english=word,previousLevel=old,selectedLevel=level,reason=reason))
    groups[3]+=new
    assert [len(groups[l]) for l in range(1,5)]==[800,900,1200,100]
    placements=[]
    for l in range(1,5):
        placements += [dict(id=e['id'],level=e['level'],section=e['section'],number=e['number']) for e in groups[l]] if l<3 else arrange(groups[l],l)
    active=original+new;by_id={e['id']:e for e in active}
    assert len(by_id)==len(active)
    materialized=[{**by_id[p['id']],**p} for p in placements]
    assert len({e['english'] for e in materialized})==len(materialized)
    examples=[e['example'].casefold() for e in original+new];assert len(examples)==len(set(examples))
    sources={s['id']:s for s in read_json(root/'content/sources.json')};seen=set()
    for e in materialized:
        errors=validate_entry(e,sources,seen,require_approval=False)
        if errors:raise ValueError((e['english'],errors))
    write_json(root/'content/words/reselected_additions.json',new)
    write_json(root/'content/words/selection.json',dict(version=2,updatedAt=NOW(),policy='content/authoring/reselection/policy.json',placements=placements,reserveIds=[e['id'] for e in original if e['english'] in reserve]))
    write_json(root/'analysis/selection_decisions.json',decisions+[dict(id=e['id'],english=e['english'],previousLevel=None,selectedLevel=3,reason='大学受験で重要な不足語の独自補完') for e in new])
    summary=dict(updatedAt=NOW(),selectedWordCounts=[len(groups[l]) for l in range(1,5)],authoredUniqueWords=len(active),activeWords=len(placements),reservedWords=len(reserve),newWords=len(new),level3MovedTo4=len(promote),level4MovedTo3=80,level3Complete=True,editorialStatus='AI再選定・人手校閲待ち',productionApproved=False,legacyArchiveSha256=hashlib.sha256((root/'content/words/drafts.json').read_bytes()).hexdigest())
    write_json(root/'analysis/reselection_summary.json',summary)
    return summary

if __name__=='__main__':
    print(json.dumps(build() if '--build' in sys.argv else {'validatedNewWords':len(read_new())},ensure_ascii=False,indent=2))
