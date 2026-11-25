"""Compile original L3 ordering readings from explicitly authored annotations."""
import json
from build_l3_gap10 import ROOT,AUTHOR,read_authored,parse_sentence,words,write_immutable
from level3_word_policy import validate_level3_word_count
from content_pipeline import validate_reading,validate_provenance

def compile_batch(next5=False):
 suffix="-next5" if next5 else ""
 authored=read_authored(8,suffix);questions=json.loads((AUTHOR/f'l3-f08{suffix}-questions.json').read_text());assert len(authored)==len(questions) and len(authored)==5
 sources={s['id']:s for s in json.loads((ROOT/'content/sources.json').read_text())};batch=[]
 for i,(a,qs) in enumerate(zip(authored,questions),6 if next5 else 1):
  pid=f'reading-l3-f08-{i:02}';paragraphs=[];syntax=[];sentences=[]
  assert len(a['paragraphs'])==4
  for j,rows in enumerate(a['paragraphs'],1):
   paraid=f'p{ORDERS[i-1][j-1]}';offset=0;ens=[];jps=[]
   for k,(markup,jp,note) in enumerate(rows,1):
    en,spans,edges,gaps=parse_sentence(markup);assert not gaps and jp and note
    sid=f'{paraid}-s{k:03}'
    for n in spans:n['start']+=offset;n['end']+=offset
    sy={'id':f'{pid}:{sid}','sentenceId':sid,'paragraphId':paraid,'sentence':en,'translation':jp,'start':offset,'end':offset+len(en),'explanation':note,'spans':spans,'relations':edges,'skeleton':' / '.join(n['role']+': '+n['text'] for n in spans if n['role'] in ('S','V','O','C')),'grammarPoints':[note],'readingOrder':'主節のSとVを確認し、句節の階層・修飾先・否定の範囲・段落間の対比を確認して全文訳と照合する。','offsetBasis':'paragraphs','reviewStatus':'ai_author_checked_human_pending'}
    sentences.append({'id':sid,'paragraphId':paraid,'english':en,'translation':jp,'start':offset,'end':offset+len(en),'sourceStart':offset,'sourceEnd':offset+len(en),'sourceEnglish':en,'syntaxId':sy['id']});syntax.append(sy);ens.append(en);jps.append(jp);offset+=len(en)+1
   paragraphs.append({'id':paraid,'english':' '.join(ens),'translation':''.join(jps)})
  count=words(' '.join(p['english'] for p in paragraphs));validate_level3_word_count(8,i,count);assert 5<=len(qs)<=8
  built=[]
  for j,q in enumerate(qs):
   order=list(range(4));shift=(i+j*3)%4;order=order[shift:]+order[:shift]
   correct=q.get('correctIndex',0);assert len(q['options'])==4
   built.append({'id':f'q{j+1}','prompt':q['prompt'],'options':[{'id':'abcd'[k],'text':q['options'][n][0],'explanation':q['options'][n][1]} for k,n in enumerate(order)],'correctOptionId':'abcd'[order.index(correct)],'explanation':q['options'][correct][1],'evidence':{'paragraphId':next(p['id'] for p in paragraphs if q['quote'] in p['english']),'quote':q['quote']}})
  p={'id':pid,'level':3,'format':8,'title':a['title'],'paragraphs':paragraphs,'wordCount':count,'sentences':sentences,'syntax':syntax,'syntaxOffsetBasis':'paragraphs','questions':built,'recommendedSeconds':round((count/75*60+len(built)*55)/15)*15,'vocabulary':[{'english':en,'meaning':jp} for en,jp in VOCAB[i-1]],'content':{'sourceIds':['original-reading-l3-v1'],'sourceUsage':[{'sourceId':'original-reading-l3-v1','fields':['title','paragraphs','questions','syntax','vocabulary']}],'contentVersion':2,'standardVersion':2,'qualityStatus':'review_required','autoChecked':True,'humanReviewed':False,'productionApproved':False,'examFrequency':None,'selectionReason':'独自のLEVEL3段落整序読解。指示表現・課題提示・対策・検証・結論のつながりから4段落を整序。形式内番号別語数・全文和訳・明示的構文を検証。'},'difficulty':{'scores':{'vocabulary':3,'syntax':4,'logic':4,'questions':4},'method':'AI rubric, author assessed','status':'ai_assessed_human_pending','rationale':'既出情報を受ける指示表現と実験・対策の時系列を照合し、因果・対比の順序を判断する。'},'editorialReview':{'status':'author_checked','reviewer':'AI author; not independent human review','independentHumanReviewed':False},'review':{k:'ai_checked_human_pending' for k in ['fullTranslation','fullSyntax','questionUniqueness','englishNaturalness']}}
  p['paragraphOrder']=[f'p{n}' for n in ORDERS[i-1]]
  p['paragraphs'].sort(key=lambda para:para['id'])
  assert next(o['text'] for o in p['questions'][0]['options'] if o['id']==p['questions'][0]['correctOptionId'])=='→'.join(str(n) for n in ORDERS[i-1])
  errors=validate_reading(p)+validate_provenance(p['content'],sources,False);assert not errors,(pid,errors);batch.append(p)
 return batch
ORDERS=[[3,1,4,2],[2,4,1,3],[4,2,3,1],[1,3,2,4],[3,4,2,1],[2,1,3,4],[4,1,2,3],[1,4,3,2],[2,3,1,4],[3,2,4,1]]
VOCAB=[[('baseline','比較の基準'),('distribution','分布'),('representative','代表的な')],[('provenance','由来・来歴'),('attribution','出所の特定'),('reconstruction','再構成')],[('insulation','断熱'),('contingency','不測の事態'),('redundancy','代替手段の重複')],[('turnover','入れ替わり'),('stewardship','責任ある管理'),('eligibility','参加資格')],[('equivalence','同等性'),('ambiguity','曖昧さ'),('revision','修正')]]

VOCAB += [[('restoration','修復'),('irreversible','元に戻せない'),('preservation','保存')],[('corridor','生息地をつなぐ回廊'),('coverage','観測範囲'),('consistent with','〜と整合する')],[('deposit','預かり金'),('circulation','循環'),('durability','耐久性')],[('tactile','触覚の'),('spatial','空間の'),('representation','表現・再現')],[('exposure','露光'),('qualified','限定・留保付きの'),('non-detection','未検出')]]

def main(next5=False):
 suffix='_next5' if next5 else ''
 batch=compile_batch(next5);write_immutable(ROOT/f'content/readings/l3_f08{suffix}.json',batch)
 path=ROOT/'content/readings/advanced.json';old=json.loads(path.read_text());byid={p['id']:p for p in old}
 for p in batch:
  if p['id'] in byid:assert byid[p['id']]==p
  else:old.append(p)
 path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
 path=ROOT/'content/readings/difficulty.json';ratings=json.loads(path.read_text());ratings['ratings'].update({p['id']:p['difficulty'] for p in batch});path.write_text(json.dumps(ratings,ensure_ascii=False,indent=2)+'\n')
 raw=json.loads((ROOT/'content/readings/drafts.json').read_text())+old
 cp={'authoredPassages':len(raw),'totalQuestions':sum(len(p['questions']) for p in raw),'totalWords':sum(p.get('reviewWordCount',p['wordCount']) for p in raw),'complete':len(raw)==400,'levels':{str(l):{'authoredPassages':sum(p['level']==l for p in raw),'countsByFormat':[sum(p['level']==l and p['format']==f for p in raw) for f in range(1,11)],'complete':all(sum(p['level']==l and p['format']==f for p in raw)==10 for f in range(1,11))} for l in range(1,5)},'humanReviewed':False,'productionApproved':False}
 (ROOT/'analysis/reading_checkpoint.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n')
 manifest={'batch':f'l3-f08{suffix}-{len(batch)}','humanReviewed':0,'passages':[{'id':p['id'],'words':p['wordCount'],'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),'sentences':len(p['sentences'])} for p in batch]}
 (ROOT/f'analysis/reading_l3_f08{suffix}_batch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
if __name__=='__main__':
 import sys
 main('--next5' in sys.argv)
