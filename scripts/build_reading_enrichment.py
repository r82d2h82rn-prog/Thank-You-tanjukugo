import copy,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base=json.loads((root/'content/readings/drafts.json').read_text());lines=iter((root/'content/authoring/reading-enrichment/l1-first5.tsv').read_text().splitlines());out=[]
for original in base[:5]:
 p=copy.deepcopy(original);p['previousSyntax']=p['syntax'];p['syntax']=[];p['sentences']=[];p['content']['contentVersion']=2
 for para in p['paragraphs']:
  translations=[]
  for i,m in enumerate(re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)',para['english'])):
   english=m.group();jp,annotation,note=next(lines).split('\t');sid=f"{para['id']}-s{i+1:03}";spans=[];used={}
   for n,part in enumerate(annotation.split(';')):
    role,text=part.split('=',1);hits=[x.start() for x in re.finditer(r'(?<!\w)'+re.escape(text)+r'(?!\w)',english)];assert hits,(p['id'],english,text)
    idx=used.get(text,0);start=m.start()+hits[idx];used[text]=idx+1
    spans.append(dict(id=f'n{n+1}',role=role,text=text,start=start,end=start+len(text)))
   assert any(x['role']=='S' for x in spans) and any(x['role']=='V' for x in spans)
   verb=next(x for x in spans if x['role']=='V');relations=[]
   for n,span in enumerate(spans):
    if span['text']=='for old books':
     relations.append({'from':span['id'],'to':next(x['id'] for x in spans if x['text']=='a box'),'type':'modifies'});continue
    if span['role']=='M':relations.append({'from':span['id'],'to':verb['id'],'type':'modifies'})
    if span['role']=='phrase' and n>0 and not span['text'].startswith('to '):
     head=next((x for x in reversed(spans[:n]) if x['role'] in ('S','O','C')),verb);relations.append({'from':span['id'],'to':head['id'],'type':'modifies'})
    if span['role']=='clause':relations.append({'from':span['id'],'to':verb['id'],'type':'adverbial' if re.match(r'(because|before|while)\b',span['text']) else 'clause'})
   old=next((x for x in original['syntax'] if x['paragraphId']==para['id'] and x['sentence']==english),None)
   syntax=dict(id=f"{p['id']}:{sid}",passageId=p['id'],contentVersion=2,paragraphId=para['id'],sentenceId=sid,sentence=english,start=m.start(),end=m.end(),translation=jp,explanation=note+((' 既存解説：'+old['explanation']) if old else ''),spans=spans,relations=relations,skeleton=' / '.join(x['role']+': '+x['text'] for x in spans if x['role'] in ('S','V','O','C')),grammarPoints=[note],readingOrder='主節の主語と動詞を確認し、並列・句節の役割を説明に従って読み、日本語訳で意味を確認する。',reviewStatus='ai_author_checked_human_pending')
   p['syntax'].append(syntax);p['sentences'].append({'id':sid,'paragraphId':para['id'],'english':english,'translation':jp,'start':m.start(),'end':m.end(),'syntaxId':syntax['id']});translations.append(jp)
  para['translation']=''.join(translations)
 out.append(p)
try:next(lines);raise AssertionError('unused authored annotation')
except StopIteration:pass
extras=[
 [('ミナは変更後、いつ本を点検しているか。','毎週金曜日','毎週月曜日','毎日正午','月末だけ','every Friday'),('古い本用の箱を置いた場所はどこか。','本棚の横','職員室の中','店の入口','自宅の台所','beside the shelf')],
 [('会館の場所を知らせるため、地図に何を加えたか。','ニンジンとトマトの絵','全商品の価格表','祖母の電話番号','運転手の名前','pictures of carrots and tomatoes')],
 [('男性がいたのはどこか。','案内板の後ろ','遊び場の中央','家の玄関','広場の入口','behind the information board'),('ユイが翌日の午後にしたことは何か。','本を持って見つけた場所へ戻った','公園を全て静かにするよう求めた','案内板を撤去した','池を別の場所へ移した','Yui returned the next afternoon with her book.')],
 [('失敗したタロウにボランティアはどう接したか。','手順を説明してもう一度試させた','かばんを取り上げて帰らせた','全部一人で修理するよう要求した','新品を買うことだけを勧めた','let him try again')],[]]
for p,qs in zip(out,extras):
 for prompt,correct,*rest in qs:
  wrong=rest[:3];quote=rest[3];para=next(x for x in p['paragraphs'] if quote in x['english']);qid=f"q{len(p['questions'])+1}"
  p['questions'].append({'id':qid,'prompt':prompt,'options':[{'id':c,'text':t,'explanation':('本文の「'+quote+'」に対応する。') if i==0 else ('本文は「'+quote+'」と述べており、この選択肢の内容は示していない。')} for i,(c,t) in enumerate(zip('abcd',[correct]+wrong))],'correctOptionId':'a','explanation':'本文の「'+quote+'」を確認する。','evidence':{'paragraphId':para['id'],'quote':quote}})
 p['review']={'fullTranslation':'ai_checked_human_pending','fullSyntax':'ai_checked_human_pending','questionUniqueness':'ai_checked_human_pending'}
(root/'content/readings/enriched.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Enriched',len(out),'readings',sum(len(x['sentences']) for x in out),'sentences')
