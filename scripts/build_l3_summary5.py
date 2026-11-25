"""Compile original L3 summary readings from explicitly authored annotations."""
import json
from build_l3_gap10 import ROOT,AUTHOR,read_authored,parse_sentence,words,write_immutable
from level3_word_policy import validate_level3_word_count
from content_pipeline import validate_reading,validate_provenance

def compile_batch(next5=False):
 suffix="-next5" if next5 else ""
 authored=read_authored(9,suffix);questions=json.loads((AUTHOR/f'l3-f09{suffix}-questions.json').read_text());assert len(authored)==len(questions) and len(authored)==5
 sources={s['id']:s for s in json.loads((ROOT/'content/sources.json').read_text())};batch=[]
 for i,(a,qs) in enumerate(zip(authored,questions),6 if next5 else 1):
  pid=f'reading-l3-f09-{i:02}';paragraphs=[];syntax=[];sentences=[]
  assert 4<=len(a['paragraphs'])<=8
  for j,rows in enumerate(a['paragraphs'],1):
   paraid=f'p{j}';offset=0;ens=[];jps=[]
   for k,(markup,jp,note) in enumerate(rows,1):
    en,spans,edges,gaps=parse_sentence(markup);assert not gaps and jp and note
    sid=f'{paraid}-s{k:03}'
    for n in spans:n['start']+=offset;n['end']+=offset
    sy={'id':f'{pid}:{sid}','sentenceId':sid,'paragraphId':paraid,'sentence':en,'translation':jp,'start':offset,'end':offset+len(en),'explanation':note,'spans':spans,'relations':edges,'skeleton':' / '.join(n['role']+': '+n['text'] for n in spans if n['role'] in ('S','V','O','C')),'grammarPoints':[note],'readingOrder':'主節のSとVを確認し、句節の階層・修飾先・否定の範囲・段落間の対比を確認して全文訳と照合する。','offsetBasis':'paragraphs','reviewStatus':'ai_author_checked_human_pending'}
    sentences.append({'id':sid,'paragraphId':paraid,'english':en,'translation':jp,'start':offset,'end':offset+len(en),'sourceStart':offset,'sourceEnd':offset+len(en),'sourceEnglish':en,'syntaxId':sy['id']});syntax.append(sy);ens.append(en);jps.append(jp);offset+=len(en)+1
   paragraphs.append({'id':paraid,'english':' '.join(ens),'translation':''.join(jps)})
  count=words(' '.join(p['english'] for p in paragraphs));validate_level3_word_count(9,i,count);assert 5<=len(qs)<=8
  built=[]
  for j,q in enumerate(qs):
   order=list(range(4));shift=(i+j*3)%4;order=order[shift:]+order[:shift]
   correct=q.get('correctIndex',0);assert len(q['options'])==4
   built.append({'id':f'q{j+1}','prompt':q['prompt'],'options':[{'id':'abcd'[k],'text':q['options'][n][0],'explanation':q['options'][n][1]} for k,n in enumerate(order)],'correctOptionId':'abcd'[order.index(correct)],'explanation':q['options'][correct][1],'evidence':{'paragraphId':next(p['id'] for p in paragraphs if q['quote'] in p['english']),'quote':q['quote']}})
  p={'id':pid,'level':3,'format':9,'title':a['title'],'paragraphs':paragraphs,'wordCount':count,'sentences':sentences,'syntax':syntax,'syntaxOffsetBasis':'paragraphs','questions':built,'recommendedSeconds':round((count/75*60+len(built)*55)/15)*15,'vocabulary':[{'english':en,'meaning':jp} for en,jp in VOCAB[i-1]],'content':{'sourceIds':['original-reading-l3-v1'],'sourceUsage':[{'sourceId':'original-reading-l3-v1','fields':['title','paragraphs','questions','syntax','vocabulary']}],'contentVersion':2,'standardVersion':2,'qualityStatus':'review_required','autoChecked':True,'humanReviewed':False,'productionApproved':False,'examFrequency':None,'selectionReason':'独自のLEVEL3要約読解。中心主張・対比・条件・結論を統合し、具体例への偏り・過度な一般化・論旨の逆転を避けた要約を選ぶ。形式内番号別語数・全文和訳・明示的構文を検証。'},'difficulty':{'scores':{'vocabulary':3,'syntax':4,'logic':4,'questions':4},'method':'AI rubric, author assessed','status':'ai_assessed_human_pending','rationale':'複数段落の中心主張とその条件を統合し、具体例と一般的結論を区別して要約の範囲を判断する。'},'editorialReview':{'status':'author_checked','reviewer':'AI author; not independent human review','independentHumanReviewed':False},'review':{k:'ai_checked_human_pending' for k in ['fullTranslation','fullSyntax','questionUniqueness','englishNaturalness']}}
  errors=validate_reading(p)+validate_provenance(p['content'],sources,False);assert not errors,(pid,errors);batch.append(p)
 return batch
VOCAB=[[('authenticity','真正性・本物らしさ'),('variation','変化・差異'),('transmission','伝承')],[('apprentice','見習い'),('judgment','判断力'),('replicate','再現する')],[('equivalence','同等性'),('rhythm','リズム'),('interpretation','解釈')],[('connection','乗り継ぎ'),('reliability','確実性'),('indicator','指標')],[('replication','追試・反復'),('germination','発芽'),('variable','変数・条件')]]

VOCAB += [[('selectivity','情報の選択性'),('exhaustive','網羅的な'),('omission','省略・欠落')],[('repairability','修理可能性'),('disassembly','分解'),('documentation','説明・記録資料')],[('feedback','反応が次の提示に影響する循環'),('preference','好み'),('redirect','方向を変える')],[('intimacy','親密さ'),('distinctive','独自の'),('exemption','免除')],[('consistent','一貫した'),('criteria','評価基準'),('defensible','根拠を説明できる')]]

def main(next5=False):
 suffix='_next5' if next5 else ''
 batch=compile_batch(next5);write_immutable(ROOT/f'content/readings/l3_f09{suffix}.json',batch)
 path=ROOT/'content/readings/advanced.json';old=json.loads(path.read_text());byid={p['id']:p for p in old}
 for p in batch:
  if p['id'] in byid:assert byid[p['id']]==p
  else:old.append(p)
 path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
 path=ROOT/'content/readings/difficulty.json';ratings=json.loads(path.read_text());ratings['ratings'].update({p['id']:p['difficulty'] for p in batch});path.write_text(json.dumps(ratings,ensure_ascii=False,indent=2)+'\n')
 raw=json.loads((ROOT/'content/readings/drafts.json').read_text())+old
 cp={'authoredPassages':len(raw),'totalQuestions':sum(len(p['questions']) for p in raw),'totalWords':sum(p.get('reviewWordCount',p['wordCount']) for p in raw),'complete':len(raw)==400,'levels':{str(l):{'authoredPassages':sum(p['level']==l for p in raw),'countsByFormat':[sum(p['level']==l and p['format']==f for p in raw) for f in range(1,11)],'complete':all(sum(p['level']==l and p['format']==f for p in raw)==10 for f in range(1,11))} for l in range(1,5)},'humanReviewed':False,'productionApproved':False}
 (ROOT/'analysis/reading_checkpoint.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n')
 manifest={'batch':f'l3-f09{suffix}-{len(batch)}','humanReviewed':0,'passages':[{'id':p['id'],'words':p['wordCount'],'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),'sentences':len(p['sentences'])} for p in batch]}
 (ROOT/f'analysis/reading_l3_f09{suffix}_batch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
if __name__=='__main__':
 import sys
 main('--next5' in sys.argv)
