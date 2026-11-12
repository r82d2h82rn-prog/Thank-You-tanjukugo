#!/usr/bin/env python3
"""Content tooling. No remote corpus/body downloads; permission checks precede ingestion."""
import argparse, collections, csv, datetime, hashlib, json, pathlib, re, sys, unicodedata, urllib.request, urllib.error
ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = {'word': [800,900,1200,1000], 'idiom': [300,500,700,500], 'reading':[100]*4}
NOW = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
def read_json(path): return json.loads(path.read_text())
def write_json(path, data): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as file: return list(csv.DictReader(file))
def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
def normalized(text): return re.sub(r'\s+',' ',unicodedata.normalize('NFC',text).strip().casefold().replace('’',"'"))
def probe_sources(root=ROOT):
    """Only inspect one landing page per host. Never automatically fetch linked material."""
    sources=read_json(root/'content/sources.json'); observations={}
    from urllib.parse import urlparse
    for source in sources:
        if not source['url']: continue
        host=urlparse(source['url']).hostname
        if host not in observations:
            try:
                req=urllib.request.Request(source['url'],headers={'User-Agent':'ThankYouContentResearch/0.1'})
                with urllib.request.urlopen(req,timeout=15) as response:
                    # Do not save third-party text before reuse rights are established.
                    observations[host]={'status':'accessible_terms_unverified','httpStatus':response.status,'checkedAt':NOW()}
            except (urllib.error.URLError,TimeoutError) as error:
                observations[host]={'status':'access_failed','error':str(error),'checkedAt':NOW()}
        source['accessStatus']=observations[host]['status']; source['checkedAt']=observations[host]['checkedAt']
    write_json(root/'analysis/source_access.json',observations); write_json(root/'content/sources.json',sources)
    print(json.dumps(observations,ensure_ascii=False,indent=2))
def import_candidates(path, source_id, kind, root=ROOT):
    sources={s['id']:s for s in read_json(root/'content/sources.json')}; source=sources[source_id]
    if source['candidateExtraction']!='granted' or not source.get('licenseEvidence') or not source.get('termsUrl') or not source.get('observedVersion'):
        raise ValueError('候補抽出の利用条件・根拠・バージョンを確認してから取り込んでください')
    output=root/f'content/{kind}_candidates.csv'
    rows=read_csv(output) if output.exists() else []
    merged={normalized(row['lemma']):row for row in rows}
    for item in read_csv(path):
        lemma=normalized(item.get('lemma') or item.get('word') or '')
        if not lemma or not re.fullmatch(r"[a-zà-öø-ÿ]+(?:[-' ][a-zà-öø-ÿ]+)*",lemma): raise ValueError('見出し語が不正です')
        rank=item.get('rank','')
        if rank and (not rank.isdigit() or int(rank)<1): raise ValueError('順位が不正です')
        row=merged.setdefault(lemma,{'lemma':lemma,'source_ranks':'{}','status':'要確認','proposed_level':'','level_basis':'','exam_frequency':'','adoption_reason':'','provenance_source_ids':'[]'})
        origins=json.loads(row.get('provenance_source_ids') or '[]'); row['provenance_source_ids']=json.dumps(sorted(set(origins+[source_id])));
        ranks=json.loads(row['source_ranks']); incoming={'rank':int(rank) if rank else None,'version':source['observedVersion']}
        if source_id in ranks and ranks[source_id]!=incoming: raise ValueError('同一ソース内の順位・バージョンが競合しています')
        ranks[source_id]={'rank':int(rank) if rank else None,'version':source['observedVersion']}; row['source_ranks']=json.dumps(ranks,ensure_ascii=False,sort_keys=True)
    write_csv(output, sorted(merged.values(),key=lambda r:r['lemma']), ['lemma','source_ranks','status','proposed_level','level_basis','exam_frequency','adoption_reason','provenance_source_ids'])
    return len(merged)
def validate_entry(e, sources, seen, require_approval=True):
    errors=[]
    required=['id','english','kind','level','section','number','meaning','pos','pronunciation','example','translation','explanation','acceptedAnswers','content']
    if any(key not in e for key in required): return ['missing required fields']
    if e['id'] in seen: errors.append('duplicate id')
    seen.add(e['id'])
    if e['kind'] not in ('word','idiom'): return errors+['invalid kind']
    if type(e['level']) is not int or e['level'] not in range(1,5): return errors+['invalid level']
    size=100 if e['kind']=='word' else 50
    if type(e['section']) is not int or e['section']<1 or type(e['number']) is not int or not 1<=e['number']<=size: errors.append('invalid section/number')
    elif e['level'] in range(1,5) and e['section']>TARGETS[e['kind']][e['level']-1]//size: errors.append('section outside target')
    if any(not isinstance(e[k],str) or not e[k].strip() for k in ['id','english','meaning','pos','pronunciation','example','translation','explanation']): errors.append('empty required text')
    if not isinstance(e['acceptedAnswers'],list) or not all(isinstance(a,str) and a.strip() for a in e['acceptedAnswers']): errors.append('invalid alternate answers')
    elif e['kind']=='idiom' and any(len(a.split())!=len(e['english'].split()) for a in e['acceptedAnswers']): errors.append('alternate answer word count differs')
    errors.extend(validate_provenance(e.get('content',{}),sources,require_approval))
    return errors
def validate_provenance(metadata,sources,require_approval=True):
    errors=[]
    if require_approval and (metadata.get('qualityStatus')!='approved' or metadata.get('humanReviewed') is not True or metadata.get('productionApproved') is not True or metadata.get('autoChecked') is not True): errors.append('editorial approval missing')
    if type(metadata.get('contentVersion')) is not int or metadata.get('contentVersion',0)<1 or not metadata.get('selectionReason'): errors.append('content version/reason missing')
    if not metadata.get('sourceIds'): errors.append('provenance missing')
    for source_id in metadata.get('sourceIds',[]):
        source=sources.get(source_id,{})
        if source_id not in sources: errors.append(f'unknown source: {source_id}')
        if require_approval and (source.get('commercialUse')!='granted' or source.get('redistribution')!='granted' or not source.get('licenseEvidence')): errors.append(f'rights unverified: {source_id}')
    if metadata.get('qualityStatus') not in ['draft','auto_checked','review_required','approved','rejected']: errors.append('unknown quality status')
    return errors
def validate_reading(p):
    errors=[]
    required=['id','level','format','title','paragraphs','questions','syntax','recommendedSeconds','content']
    if any(k not in p for k in required): return ['reading missing required fields']
    if p['level'] not in range(1,5) or p['format'] not in range(1,11) or p['recommendedSeconds']<=0: errors.append('invalid reading metadata')
    if not 3<=len(p['questions'])<=10: errors.append('reading question count')
    paragraphs={x['id']:x for x in p['paragraphs']}
    if len(paragraphs)!=len(p['paragraphs']) or any(not x.get('english') or not x.get('translation') for x in p['paragraphs']): errors.append('paragraphs/translations invalid')
    qids=set()
    for q in p['questions']:
        options=q.get('options',[]); option_ids=[o.get('id') for o in options]
        if q.get('id') in qids or not q.get('id'): errors.append('question IDs invalid')
        qids.add(q.get('id'))
        if len(options)!=4 or len(set(option_ids))!=4 or len({normalized(o.get('text','')) for o in options})!=4 or any(not o.get('text') or not o.get('explanation') for o in options) or q.get('correctOptionId') not in option_ids: errors.append('reading options/answer/explanations invalid')
        evidence=q.get('evidence',{})
        para=paragraphs.get(evidence.get('paragraphId'),{})
        if not q.get('prompt') or not q.get('explanation') or not evidence.get('quote') or evidence['quote'] not in para.get('english',''): errors.append('answer evidence invalid')
    if not p['syntax']: errors.append('syntax missing')
    for syntax in p['syntax']:
        para=paragraphs.get(syntax.get('paragraphId'),{}); text=para.get('english',''); spans=syntax.get('spans',[])
        ids={span.get('id') for span in spans}
        if not syntax.get('explanation') or not spans or len(ids)!=len(spans): errors.append('syntax explanation/spans invalid')
        for span in spans:
            start,end=span.get('start',-1),span.get('end',-1)
            if not isinstance(start,int) or not isinstance(end,int) or not 0<=start<end<=len(text) or text[start:end]!=span.get('text') or span.get('role') not in ['S','V','O','C','M','clause','phrase']: errors.append('syntax offsets invalid')
        for edge in syntax.get('relations',[]):
            if edge.get('from') not in ids or edge.get('to') not in ids: errors.append('syntax relation invalid')
    return errors
def audit(root=ROOT, release=False):
    sources={s['id']:s for s in read_json(root/'content/sources.json')}
    groups={'word':read_json(root/'content/words/approved.json'),'idiom':read_json(root/'content/idioms/approved.json'),'reading':read_json(root/'content/readings/approved.json')}
    issues=[]; seen=set(); labels=set(); section_numbers=collections.defaultdict(list)
    for kind,entries in groups.items():
        for e in entries:
            errors=validate_reading(e) if kind=='reading' else validate_entry(e,sources,seen)
            if kind=='reading':
                if e.get('id') in seen: errors.append('duplicate id')
                seen.add(e.get('id'))
                errors.extend(validate_provenance(e.get('content',{}),sources))
                label=('reading',normalized(' '.join(p.get('english','') for p in e.get('paragraphs',[]))))
                if label in labels: errors.append('duplicate reading text')
                labels.add(label)
            else:
                label=(kind,normalized(e.get('english','')))
                if label in labels: errors.append('duplicate normalized lemma; sense split requires separate editorial review')
                labels.add(label); section_numbers[(kind,e.get('level'),e.get('section'))].append(e.get('number'))
            issues.extend({'id':e.get('id'),'error':error} for error in errors)
    for scope,numbers in section_numbers.items():
        if sorted(numbers)!=list(range(1,len(numbers)+1)): issues.append({'id':str(scope),'error':'number gaps/duplicates'})
        if len(numbers)!=(100 if scope[0]=='word' else 50): issues.append({'id':str(scope),'error':'section incomplete'})
    counts={kind:[sum(e.get('level')==l for e in entries) for l in range(1,5)] for kind,entries in groups.items()}
    gaps={kind:[max(0,target-count) for target,count in zip(TARGETS[kind],counts[kind])] for kind in TARGETS}
    if release:
        for kind in TARGETS:
            if counts[kind]!=TARGETS[kind]: issues.append({'id':kind,'error':f'release count mismatch: {counts[kind]} expected {TARGETS[kind]}'})
        for level in range(1,5):
            for form in range(1,11):
                if sum(p.get('level')==level and p.get('format')==form for p in groups['reading'])!=10: issues.append({'id':f'reading-{level}-{form}','error':'reading format quota mismatch'})
    draft_counts={}; draft_review=0
    draft_seen=set(seen)
    for kind,folder in [('word','words'),('idiom','idioms')]:
        path=root/f'content/{folder}/drafts.json'
        drafts=read_json(path) if path.exists() else []
        if kind=='word' and (root/'content/words/selection.json').exists():
            from word_catalog import authored_catalog
            drafts=authored_catalog(root)
        draft_counts[kind]=[sum(e.get('level')==l for e in drafts) for l in range(1,5)]
        for entry in drafts:
            issues.extend({'id':entry.get('id'),'error':error} for error in validate_entry(entry,sources,draft_seen,require_approval=False))
            draft_review+=not entry.get('content',{}).get('humanReviewed',False)
    reading_path=root/'content/readings/drafts.json'
    reading_drafts=read_json(reading_path) if reading_path.exists() else []
    advanced_path=root/'content/readings/advanced.json'
    if advanced_path.exists(): reading_drafts+=read_json(advanced_path)
    enriched_path=root/'content/readings/enriched.json'
    if enriched_path.exists():
        replacements={p['id']:p for p in read_json(enriched_path)}
        for original in reading_drafts:
            replacement=replacements.get(original['id'])
            if replacement and replacement['questions'][:len(original['questions'])]!=original['questions']: issues.append({'id':original['id'],'error':'original question identity changed'})
        reading_drafts=[replacements.get(p['id'],p) for p in reading_drafts]
    draft_counts['reading']=[sum(p.get('level')==l for p in reading_drafts) for l in range(1,5)]
    for entry in reading_drafts:
        errors=validate_reading(entry)+validate_provenance(entry.get('content',{}),sources,False)
        if entry.get('id') in draft_seen:errors.append('duplicate draft reading id')
        draft_seen.add(entry.get('id'))
        label=('reading',normalized(' '.join(p.get('english','') for p in entry.get('paragraphs',[]))))
        if label in labels:errors.append('duplicate reading text')
        labels.add(label)
        issues.extend({'id':entry.get('id'),'error':error} for error in errors)
        draft_review+=not entry.get('content',{}).get('humanReviewed',False)
    samples=read_json(root/'src/data/entries.json'); metadata=read_json(root/'content/provenance.json')
    for e in samples:
        if e['id'] not in metadata: issues.append({'id':e['id'],'error':'sample provenance missing'})
        elif e['id'] not in seen:
            issues.extend({'id':e['id'],'error':error} for error in validate_entry({**e,'content':metadata[e['id']]},sources,draft_seen,require_approval=False))
    sample_counts=dict(collections.Counter(e['kind'] for e in samples))
    report={'checkedAt':NOW(),'mode':'release' if release else 'development','approvedCounts':counts,'requiredCounts':TARGETS,'remaining':gaps,'draftCounts':draft_counts,'sampleCounts':sample_counts,'structurallyCheckedCounts':{kind:sum(counts[kind])+sum(draft_counts.get(kind,[]))+sample_counts.get(kind,0) for kind in TARGETS},'humanReviewPending':draft_review+sum(not m.get('humanReviewed') for m in metadata.values()),'issues':issues,'releaseReady':not issues and counts==TARGETS}
    write_json(root/('analysis/release_audit.json' if release else 'analysis/content_audit.json'),report)
    print(json.dumps(report,ensure_ascii=False,indent=2)); return not issues

def main():
    parser=argparse.ArgumentParser(); subs=parser.add_subparsers(dest='command',required=True)
    subs.add_parser('probe'); audit_parser=subs.add_parser('audit'); audit_parser.add_argument('--release',action='store_true')
    importer=subs.add_parser('import-candidates'); importer.add_argument('path',type=pathlib.Path); importer.add_argument('--source',required=True); importer.add_argument('--kind',choices=['word','idiom'],required=True)
    args=parser.parse_args()
    if args.command=='probe': probe_sources()
    elif args.command=='audit': sys.exit(0 if audit(release=args.release) else 1)
    else: print(import_candidates(args.path,args.source,args.kind))
if __name__=='__main__': main()
