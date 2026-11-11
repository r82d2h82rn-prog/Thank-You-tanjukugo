#!/usr/bin/env python3
"""Analyze only permission-verified local exam texts. Never fetch/download exam bodies."""
import collections, csv, hashlib, json, pathlib, re
from content_pipeline import ROOT, NOW, normalized, read_json, read_csv, write_csv, write_json
TOKEN = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
def tokens(text, forms):
    return [{'form':m.group().casefold(),'lemma':forms.get(m.group().casefold(),m.group().casefold()),'start':m.start(),'end':m.end()} for m in TOKEN.finditer(text)]
def phrase_hits(words, phrase, max_gap=3):
    """Bounded-gap candidates are review suggestions, never automatic confirmed frequency."""
    parts=normalized(phrase).split(); hits=[]
    if not parts: return hits
    for start in range(len(words)):
        if words[start]['lemma']!=parts[0]: continue
        positions=[start]
        for part in parts[1:]:
            found=next((i for i in range(positions[-1]+1,min(len(words),positions[-1]+max_gap+2)) if words[i]['lemma']==part),None)
            if found is None: break
            positions.append(found)
        if len(positions)==len(parts): hits.append((positions[0],positions[-1]))
    return hits
def analyze(root=ROOT):
    sources=read_csv(root/'analysis/exam_sources.csv')
    forms=read_json(root/'analysis/lemma_forms.json')
    candidates=read_csv(root/'content/word_candidates.csv')
    idioms=read_csv(root/'content/idiom_candidates.csv')
    candidate_set={normalized(row['lemma']) for row in candidates}
    stats=collections.defaultdict(lambda:{'count':0,'forms':collections.Counter(),'exams':set(),'years':set(),'universities':set(),'by_university':collections.Counter(),'by_faculty':collections.Counter(),'by_year':collections.Counter()})
    exams=[]; skipped=[]; phrase_matches=[]; total=0; uni_sizes=collections.Counter(); seen_ids=set(); seen_bodies=set()
    for source in sources:
        identity=source.get('id')
        if not identity or identity in seen_ids: raise ValueError('試験IDが重複または欠落しています')
        seen_ids.add(identity)
        if source.get('analysis_permission')!='granted' or not source.get('license_evidence') or not source.get('terms_url'):
            skipped.append({'id':identity,'reason':'analysis permission/evidence unverified'}); continue
        if not source.get('university') or not source.get('faculty') or not source.get('method') or not source.get('subject') or not source.get('year','').isdigit() or not source.get('url'):
            raise ValueError('大学・学部・方式・科目・年度・URLが必要です')
        path=(root/source['local_path']).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file(): raise ValueError('分析用ファイルがリポジトリ内にありません')
        body=path.read_bytes(); digest=hashlib.sha256(body).hexdigest()
        if digest!=source.get('sha256'): raise ValueError('コーパスのSHA256が一致しません')
        if digest in seen_bodies: raise ValueError('同じ資料の二重集計を拒否しました')
        seen_bodies.add(digest)
        words=tokens(body.decode('utf-8'),forms); total+=len(words); uni_sizes[source['university']]+=len(words)
        exams.append({'id':identity,'university':source['university'],'faculty':source['faculty'],'year':int(source['year']),'wordCount':len(words),'sha256':digest,'missingData':source.get('missing_data') or None})
        for word in words:
            if word['lemma'] not in candidate_set: continue
            s=stats[word['lemma']]; s['count']+=1; s['forms'][word['form']]+=1; s['exams'].add(identity); s['years'].add(int(source['year'])); s['universities'].add(source['university']); s['by_university'][source['university']]+=1; s['by_faculty'][source['university']+'/'+source['faculty']]+=1; s['by_year'][source['year']]+=1
        for row in idioms:
            phrase=row['lemma']
            for first,last in phrase_hits(words,phrase):
                phrase_matches.append({'exam_id':identity,'phrase':phrase,'start':words[first]['start'],'end':words[last]['end'],'status':'review_required','note':'活用・最大3語の挿入を許す候補検出。本文は出力しない。句境界・語義を要確認。'})
    ranks=[]
    for lemma,s in stats.items():
        # Equal weight per university, including zero occurrences at other analyzed universities.
        balanced=sum(s['by_university'][uni]/size*10000 for uni,size in uni_sizes.items() if size)/max(len(uni_sizes),1)
        ranks.append({'lemma':lemma,'count':s['count'],'per_10000':s['count']/total*10000 if total else None,'exam_count':len(s['exams']),'year_count':len(s['years']),'university_count':len(s['universities']),'corpus_words':total,'corpus_exams':len(exams),'university_balanced_per_10000':balanced,'forms':json.dumps(s['forms'],ensure_ascii=False,sort_keys=True),'by_university':json.dumps(s['by_university'],ensure_ascii=False,sort_keys=True),'by_faculty':json.dumps(s['by_faculty'],ensure_ascii=False,sort_keys=True),'by_year':json.dumps(s['by_year'],ensure_ascii=False,sort_keys=True),'adoption_score':None,'proposed_level':None,'score_status':'未検証：一般頻度・LEVEL適合を未評価'})
    ranks.sort(key=lambda row:(-row['university_balanced_per_10000'],row['lemma']))
    fields=['lemma','count','per_10000','exam_count','year_count','university_count','corpus_words','corpus_exams','university_balanced_per_10000','forms','by_university','by_faculty','by_year','adoption_score','proposed_level','score_status']
    write_csv(root/'analysis/word_frequency.csv',ranks,fields)
    write_csv(root/'analysis/idiom_matches_review.csv',phrase_matches,['exam_id','phrase','start','end','status','note'])
    # Counts of candidates are not confirmed counts. Never fill these with estimates.
    write_csv(root/'analysis/idiom_frequency.csv',[{'phrase':row['lemma'],'candidate_matches':sum(h['phrase']==row['lemma'] for h in phrase_matches),'confirmed_count':None,'status':'not_analyzed' if not exams else 'review_required'} for row in idioms],['phrase','candidate_matches','confirmed_count','status'])
    summary={'analyzedAt':NOW(),'status':'analyzed' if exams else 'no_authorized_corpus','examCount':len(exams),'corpusWords':total,'universityCount':len(uni_sizes),'measuredWordTypes':len(ranks),'confirmedIdiomCount':None,'universities':dict(uni_sizes),'exams':exams,'skipped':skipped,'limitations':['原形変換は明示したforms辞書のみ。派生語は自動統合しない。','熟語検出は候補。構文・語義の人手確認が必要。','採用スコアは一般頻度・LEVEL適合が揃うまで未算出。','未取得の大学・年度を0頻度の母集団へ追加しない。']}
    write_json(root/'analysis/corpus_summary.json',summary)
    return summary
if __name__=='__main__': print(json.dumps(analyze(),ensure_ascii=False,indent=2))
