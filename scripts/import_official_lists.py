#!/usr/bin/env python3
"""Import reviewed, locally saved NGSL Project files; never fetch remote material.

The manifest pins every byte sequence, source, encoding, and column mapping.
Alphabetical order is never silently treated as a frequency rank.
"""
import argparse, collections, csv, hashlib, io, json, pathlib, sys
from content_pipeline import ROOT, NOW, read_json, read_csv, write_json, write_csv, normalized, import_candidates

def parse_list(data, spec):
    if hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError('配布ファイルのSHA256不一致: '+spec['sourceId'])
    text=data.decode(spec['encoding'],errors='strict')
    if spec['format']=='csv':
        reader=csv.DictReader(io.StringIO(text))
        required={spec['lemmaColumn'],spec['rankColumn']}
        if not required.issubset(reader.fieldnames or []): raise ValueError('配布CSVの列が変更されています')
        rows=[{'lemma':normalized(row[spec['lemmaColumn']]),'rank':row[spec['rankColumn']].strip()} for row in reader if row.get(spec['lemmaColumn'],'').strip()]
    elif spec['format']=='alphabetized_text':
        lines=text.splitlines(); first=spec['firstLemma']
        if first not in lines: raise ValueError('アルファベット一覧の開始点がありません')
        rows=[{'lemma':normalized(line),'rank':''} for line in lines[lines.index(first):] if line.strip()]
    else: raise ValueError('未知の配布形式')
    if len(rows)!=spec['observedRows'] or len({r['lemma'] for r in rows})!=len(rows): raise ValueError('語数または重複が配布記録と不一致')
    if spec['format']=='csv' and (any(not r['rank'].isdigit() or int(r['rank'])<1 for r in rows) or len({r['rank'] for r in rows})!=len(rows)):
        raise ValueError('頻度順位の欠落または重複')
    return rows

def ingest(root=ROOT):
    manifest=read_json(root/'content/upstream/manifest.json'); sources={s['id']:s for s in read_json(root/'content/sources.json')}
    # Preflight all files and rights before changing the candidate catalog.
    prepared=[]
    for spec in manifest['files']:
        source=sources[spec['sourceId']]
        if source.get('candidateExtraction')!='granted' or not source.get('licenseEvidence') or not source.get('termsUrl') or source.get('observedVersion')!=spec['version']:
            raise ValueError('取り込み許可・版・根拠が不一致: '+spec['sourceId'])
        path=(root/spec['path']).resolve()
        if not path.is_relative_to((root/'content/upstream').resolve()): raise ValueError('配布ファイルのパス逸脱')
        prepared.append((spec,parse_list(path.read_bytes(),spec)))
    for spec,rows in prepared:
        output=root/f"content/upstream/{spec['sourceId']}-normalized.csv"
        write_csv(output,rows,['lemma','rank']); import_candidates(output,spec['sourceId'],'word',root)
    candidates=read_csv(root/'content/word_candidates.csv')
    counts=collections.Counter()
    for row in candidates:
        for source_id in json.loads(row.get('source_ranks') or '{}'): counts[source_id]+=1
    official_ids={s['sourceId'] for s in manifest['files']}
    report={'importedAt':NOW(),'sourceRows':dict(counts),'uniqueOfficialCandidates':sum(bool(official_ids.intersection(json.loads(r['source_ranks']))) for r in candidates),'totalCandidates':len(candidates),'multiSourceCandidates':sum(len(official_ids.intersection(json.loads(r['source_ranks'])))>1 for r in candidates),'notes':['候補数は収録決定数ではない。','NAWLは公式配布ページの統計リンクが辞書へ遷移するため、アルファベット配布版から見出しのみを取得。順位未取得。','BSL統計CSVは1744行。公式ページ説明の1700語との差は未解決。','文字コードを厳密に復号し、TSLのアクセント付き綴りを保持。','入試頻度・LEVEL・採用スコアを自動で捏造しない。']}
    write_json(root/'analysis/official_import.json',report); return report

if __name__=='__main__':
    print(json.dumps(ingest(),ensure_ascii=False,indent=2))
