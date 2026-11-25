"""Compile original L3 sentence insertion readings from explicitly authored annotations."""
import copy,json,re
from build_l3_gap10 import ROOT,AUTHOR,read_authored,parse_sentence,words,write_immutable
from level3_word_policy import validate_level3_word_count
from content_pipeline import validate_reading,validate_provenance

def apply_insertion(p,config):
 positions=config['positions'];target=config['target'];rows=p['sentences'];byid={row['id']:row for row in rows}
 assert len(positions)==len(set(positions))==4 and target in positions
 assert all(pos in byid for pos in positions)
 assert [row['id'] for row in rows if row['id'] in positions]==positions,'Positions must follow source order'
 markers={pos:f'[{"ABCD"[i]}]' for i,pos in enumerate(positions)};answer=markers[target];inserted=byid[target]
 correct=next(o['text'] for o in p['questions'][0]['options'] if o['id']==p['questions'][0]['correctOptionId'])
 assert correct==answer,'First question must agree with insertion target'
 assert sorted(o['text'] for o in p['questions'][0]['options'])==['[A]','[B]','[C]','[D]']
 p['reviewParagraphs']=copy.deepcopy(p['paragraphs']);p['reviewWordCount']=p['wordCount'];p['syntaxOffsetBasis']='reviewParagraphs'
 p['insert']={'sentence':inserted['english'],'translation':inserted['translation']}
 p['insertionSolution']={'questionId':'q1','marker':answer,'sentence':inserted['english'],'paragraphId':inserted['paragraphId']}
 for sy in p['syntax']:sy['offsetBasis']='reviewParagraphs'
 for para in p['paragraphs']:
  parts=[];offset=0
  for row in [r for r in rows if r['paragraphId']==para['id']]:
   marker=markers.get(row['id'],'');is_insert=row['id']==target
   piece=marker if is_insert else marker+row['english']
   start=offset if is_insert else offset+len(marker);end=offset+len(piece)
   row.update(sourceStart=start,sourceEnd=end,sourceEnglish=marker if is_insert else row['english'],sourceKind='insertion' if is_insert else 'text')
   parts.append(piece);offset+=len(piece)+1
  para['english']=' '.join(parts)
  for row in [r for r in rows if r['paragraphId']==para['id']]:assert para['english'][row['sourceStart']:row['sourceEnd']]==row['sourceEnglish']
  completed=re.sub(r'\[[A-D]\]',lambda m:p['insert']['sentence'] if m.group()==answer else '',para['english'])
  assert completed==next(x['english'] for x in p['reviewParagraphs'] if x['id']==para['id'])
 p['wordCount']=words(' '.join(x['english'] for x in p['paragraphs']))

def compile_batch(next5=False):
 suffix="-next5" if next5 else ""
 authored=read_authored(7,suffix);questions=json.loads((AUTHOR/f'l3-f07{suffix}-questions.json').read_text());assert len(authored)==len(questions) and len(authored)==5
 configurations=json.loads((AUTHOR/f'l3-f07{suffix}-insertions.json').read_text());assert len(configurations)==len(authored)
 sources={s['id']:s for s in json.loads((ROOT/'content/sources.json').read_text())};batch=[]
 for i,(a,qs,config) in enumerate(zip(authored,questions,configurations),6 if next5 else 1):
  pid=f'reading-l3-f07-{i:02}';paragraphs=[];syntax=[];sentences=[]
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
  count=words(' '.join(p['english'] for p in paragraphs));validate_level3_word_count(7,i,count);assert 5<=len(qs)<=8
  built=[]
  for j,q in enumerate(qs):
   order=list(range(4));shift=(i+j*3)%4;order=order[shift:]+order[:shift]
   correct=q.get('correctIndex',0);assert len(q['options'])==4
   built.append({'id':f'q{j+1}','prompt':q['prompt'],'options':[{'id':'abcd'[k],'text':q['options'][n][0],'explanation':q['options'][n][1]} for k,n in enumerate(order)],'correctOptionId':'abcd'[order.index(correct)],'explanation':q['options'][correct][1],'evidence':{'paragraphId':next(p['id'] for p in paragraphs if q['quote'] in p['english']),'quote':q['quote']}})
  p={'id':pid,'level':3,'format':7,'title':a['title'],'paragraphs':paragraphs,'wordCount':count,'sentences':sentences,'syntax':syntax,'syntaxOffsetBasis':'paragraphs','questions':built,'recommendedSeconds':round((count/75*60+len(built)*55)/15)*15,'vocabulary':[{'english':en,'meaning':jp} for en,jp in VOCAB[i-1]],'content':{'sourceIds':['original-reading-l3-v1'],'sourceUsage':[{'sourceId':'original-reading-l3-v1','fields':['title','paragraphs','questions','syntax','vocabulary']}],'contentVersion':2,'standardVersion':2,'qualityStatus':'review_required','autoChecked':True,'humanReviewed':False,'productionApproved':False,'examFrequency':None,'selectionReason':'独自のLEVEL3文挿入読解。前方照応、対比、後続の指示表現から挿入位置を判断。問題本文と完成本文を分離し、挿入文を含む全文和訳・構文と番号別完成語数を検証。'},'difficulty':{'scores':{'vocabulary':3,'syntax':4,'logic':4,'questions':4},'method':'AI rubric, author assessed','status':'ai_assessed_human_pending','rationale':'前後両方向の結束性と段落の展開を統合し、指示対象と説明・帰結の順序から挿入位置を判断する。'},'editorialReview':{'status':'author_checked','reviewer':'AI author; not independent human review','independentHumanReviewed':False},'review':{k:'ai_checked_human_pending' for k in ['fullTranslation','fullSyntax','questionUniqueness','englishNaturalness']}}
  apply_insertion(p,config)
  errors=validate_reading(p)+validate_provenance(p['content'],sources,False);assert not errors,(pid,errors);batch.append(p)
 return batch
VOCAB=[[('possession','所有・所持'),('attributed','筆者・出所が特定された'),('justify','正当化する')],[('displacement','移動・置き換え'),('predictable','予測可能な'),('tradeoff','一方の利益に伴う他方の不利益')],[('occurrence','発生・使用の一例'),('established','定着した'),('inclusion','掲載・収録')],[('endorse','賛同する'),('uniform','一様な'),('overlap','重なり')],[('maintenance','維持管理・手入れ'),('foreseeable','予見可能な'),('continuity','継続性')]]

def main(next5=False):
 suffix='_next5' if next5 else ''
 batch=compile_batch(next5);write_immutable(ROOT/f'content/readings/l3_f07{suffix}.json',batch)
 path=ROOT/'content/readings/advanced.json';old=json.loads(path.read_text());byid={p['id']:p for p in old}
 for p in batch:
  if p['id'] in byid:assert byid[p['id']]==p
  else:old.append(p)
 path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
 path=ROOT/'content/readings/difficulty.json';ratings=json.loads(path.read_text());ratings['ratings'].update({p['id']:p['difficulty'] for p in batch});path.write_text(json.dumps(ratings,ensure_ascii=False,indent=2)+'\n')
 raw=json.loads((ROOT/'content/readings/drafts.json').read_text())+old
 cp={'authoredPassages':len(raw),'totalQuestions':sum(len(p['questions']) for p in raw),'totalWords':sum(p.get('reviewWordCount',p['wordCount']) for p in raw),'complete':len(raw)==400,'levels':{str(l):{'authoredPassages':sum(p['level']==l for p in raw),'countsByFormat':[sum(p['level']==l and p['format']==f for p in raw) for f in range(1,11)],'complete':all(sum(p['level']==l and p['format']==f for p in raw)==10 for f in range(1,11))} for l in range(1,5)},'humanReviewed':False,'productionApproved':False}
 (ROOT/'analysis/reading_checkpoint.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n')
 manifest={'batch':f'l3-f07{suffix}-{len(batch)}','humanReviewed':0,'passages':[{'id':p['id'],'words':p['wordCount'],'completedWords':p['reviewWordCount'],'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),'sentences':len(p['sentences'])} for p in batch]}
 (ROOT/f'analysis/reading_l3_f07{suffix}_batch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
if __name__=='__main__':
 import sys
 main('--next5' in sys.argv)
