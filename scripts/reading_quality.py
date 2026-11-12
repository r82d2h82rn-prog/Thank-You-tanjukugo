#!/usr/bin/env python3
"""Non-destructive, provisional difficulty estimates and preservation checks."""
import hashlib,json,re,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BACKUP=ROOT/'content/backups/readings-20261113'
def fingerprint(p):return hashlib.sha256(json.dumps(p,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def protect(data):
 manifest=json.loads((BACKUP/'manifest.json').read_text());byid={p['id']:p for p in data}
 assert len(byid)==len(data),'duplicate IDs'
 for pid,digest in manifest['records'].items():assert pid in byid and fingerprint(byid[pid])==digest,'Protected reading changed: '+pid
 assert sum(p['level'] in (1,2) for p in data)==200
 return len(manifest['records'])
def estimate(p):
 text=' '.join(x['english'] for x in p['paragraphs']);words=re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",text.lower())
 sentences=[s.split() for s in re.split(r'(?<=[.!?])\s+',text) if s.strip()]
 # These transparent signals are screening aids, not a CEFR test or semantic review.
 long=sum(len(w)>=10 for w in words);maxlen=max(map(len,sentences));avg=statistics.mean(map(len,sentences))
 subordinate=len(re.findall(r'\b(although|whereas|unless|whether|whose|whom|which|despite|rather than)\b',text.lower()))
 contrast=len(re.findall(r'\b(however|instead|although|yet|rather|unless|therefore|because|while|but)\b',text.lower()))
 vocab=1+(long>=3)+(long>=8)+(long>=15)+(long>=24)
 syntax=1+(maxlen>=22)+(maxlen>=32)+(maxlen>=43)+(maxlen>=56 and subordinate>=3)
 logic=1+(contrast>=2)+(contrast>=5)+(contrast>=9)+(contrast>=13)
 question=2 if p['format'] in (1,2,5,10) else 3
 return {'scores':{'vocabulary':int(vocab),'syntax':int(syntax),'logic':int(logic),'questions':question},'method':'transparent-screening-v1','status':'provisional_not_editorially_confirmed','evidence':{'wordsAtLeast10Letters':long,'longestSentenceWords':maxlen,'meanSentenceWords':round(avg,1),'subordinationSignals':subordinate,'contrastAndCausalSignals':contrast,'format':p['format']},'limitation':'語彙の頻度・従属節の深さ・全選択肢の意味的一意性を自動確定しない。本文の難易度適合・修正の要否は編集確認待ち。'}
def main():
 data=json.loads((ROOT/'content/readings/drafts.json').read_text());advanced=ROOT/'content/readings/advanced.json';data+=(json.loads(advanced.read_text()) if advanced.exists() else []);protect(data)
 ratings={p['id']:p.get('difficulty',estimate(p)) for p in data}
 out=ROOT/'content/readings/difficulty.json';out.write_text(json.dumps({'scale':{'1':'高校入試の基本','2':'高校初級〜中級','3':'大学受験標準','4':'難関大学','5':'最難関大学'},'dimensions':['vocabulary','syntax','logic','questions'],'ratings':ratings},ensure_ascii=False,indent=2)+'\n')
 summary={str(l):{'authored':sum(p['level']==l for p in data),'structurallyVerified':sum(p['level']==l for p in data),'difficultyRated':sum(p['level']==l for p in data),'aiEditoriallyChecked':sum(p['level']==l and p.get('editorialReview',{}).get('status')=='author_checked' for p in data),'independentlyHumanReviewed':0,'target':100,'formats':[sum(p['level']==l and p['format']==f for p in data) for f in range(1,11)]} for l in range(1,5)}
 (ROOT/'analysis/reading_quality_progress.json').write_text(json.dumps({'levels':summary,'protectedExistingRecords':200,'complete':all(v['authored']==100 for v in summary.values()),'note':'構造検証と意味・難易度の編集確認は別工程。既存200題の評価は自動一次評価、確定品質確認は未完了。'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
