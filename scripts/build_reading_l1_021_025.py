"""Materialize the authored five gap exercises, with separate review coordinates."""
import copy,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=json.loads((ROOT/'content/readings/drafts.json').read_text())
lines=iter((ROOT/'content/authoring/reading-enrichment/l1-021-025.tsv').read_text().splitlines())
solutions=[next(o['text'] for o in p['questions'][0]['options'] if o['id']==p['questions'][0]['correctOptionId']) for p in base[20:25]];out=[]
for original,answer in zip(base[20:25],solutions):
 assert original['questions'][0]['options'][ord(original['questions'][0]['correctOptionId'])-97]['text']==answer
 assert sum(p['english'].count('[1]') for p in original['paragraphs'])==1
 p=copy.deepcopy(original);p['content']['contentVersion']=2;p['previousSyntax']=p['syntax'];p['syntax']=[];p['sentences']=[]
 p['gapSolutions']={'[1]':{'questionId':'q1','answer':answer}};p['reviewParagraphs']=copy.deepcopy(p['paragraphs']);p['syntaxOffsetBasis']='reviewParagraphs'
 for source,review in zip(p['paragraphs'],p['reviewParagraphs']):
  review['english']=source['english'].replace('[1]',answer)
  matches=list(re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)',review['english']))
  gap=source['english'].find('[1]')
  def source_position(position,end=False):
   if gap<0 or position<=gap:return position
   if position>=gap+len(answer):return position-len(answer)+3
   return gap+3 if end else gap

  translations=[]
  for i,m in enumerate(matches):
   old_start=source_position(m.start());old_end=source_position(m.end(),True);old_text=source['english'][old_start:old_end]
   en=m.group();jp,annotation,note=next(lines).split('\t');sid=f"{source['id']}-s{i+1:03}";spans=[];used={}
   for n,part in enumerate(annotation.split(';')):
    role,text=part.split('=',1);hits=[x.start() for x in re.finditer(r'(?<!\w)'+re.escape(text)+r'(?!\w)',en)];assert hits,(p['id'],sid,text)
    k=used.get((role,text),0);start=m.start()+hits[k];used[(role,text)]=k+1
    spans.append({'id':f'n{n+1}','role':role,'text':text,'start':start,'end':start+len(text)})
   assert any(s['role']=='S' for s in spans) and any(s['role']=='V' for s in spans)
   verbs=[x for x in spans if x['role']=='V'];relations=[]
   # Only unambiguous single-predicate modifiers are linked automatically.
   # Multiple-predicate and relative-clause links are authored explicitly below.
   if len(verbs)==1:
    relations=[{'from':x['id'],'to':verbs[0]['id'],'type':'modifies'} for x in spans if x['role']=='M']
   explanation=note
   syntax={'id':f"{p['id']}:{sid}",'passageId':p['id'],'contentVersion':2,'paragraphId':source['id'],'sentenceId':sid,'sentence':en,'start':m.start(),'end':m.end(),'translation':jp,'explanation':explanation,'spans':spans,'relations':relations,'skeleton':' / '.join(s['role']+': '+s['text'] for s in spans if s['role'] in ('S','V','O','C')),'grammarPoints':[note],'readingOrder':'主節の主語と動詞を確認し、解説に沿って句節・否定・比較の範囲を読み、日本語訳で意味を確かめる。','reviewStatus':'ai_author_checked_human_pending','offsetBasis':'reviewParagraphs'}
   p['syntax'].append(syntax);p['sentences'].append({'id':sid,'paragraphId':source['id'],'english':en,'translation':jp,'start':m.start(),'end':m.end(),'sourceEnglish':old_text,'sourceStart':old_start,'sourceEnd':old_end,'syntaxId':syntax['id']});translations.append(jp)
  source['translation']=review['translation']=''.join(translations)
 p['reviewWordCount']=len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",' '.join(x['english'] for x in p['reviewParagraphs'])))
 p['review']={'fullTranslation':'ai_checked_human_pending','fullSyntax':'ai_checked_human_pending','questionUniqueness':'ai_checked_human_pending'};out.append(p)
try:next(lines);raise AssertionError('unused authored annotation')
except StopIteration:pass


# Exact, authored relative-clause anchors; never infer antecedents from proximity.
anchors={
 'that everyone had approved':'pictures',
 'that everyone could feel comfortable with':'a way',
 'where the children stopped':'every place',
 'who have not helped create them':'people',
 'she would probably not use':'many things',
 'that had been hidden at the bottom':'the rain jacket',
 'that might be useful somewhere':'every object',
}
for p in out:
 for syntax in p['syntax']:
  for clause,head in anchors.items():
   node=next((x for x in syntax['spans'] if x['role']=='clause' and x['text']==clause),None)
   if not node:continue
   at=syntax['sentence'].index(head)+syntax['start'];ident=f"n{len(syntax['spans'])+1}"
   syntax['spans'].append({'id':ident,'role':'phrase','text':head,'start':at,'end':at+len(head),'kind':'先行詞'})
   syntax['relations'].append({'from':node['id'],'to':ident,'type':'modifies'})
extras=[
 [('リナが最初に確認を無駄だと思った理由は？',['写真が楽しそうに見えたため','友人全員が既に公表に反対していたため','川の写真を一枚も持っていなかったため','サイトが写真を載せられなかったため'],['because the picture looked cheerfulという本人の当初の理由。','反対を聞く前の判断。','代わりに川の写真を選べている。','掲載機能の問題ではない。'],'because the picture looked cheerful'),('完成したページについて正しいのは？',['全員が了承した写真でも生き生きと見えた','友人の名前を全員公開した','写真が一枚もなかった','確認をせず最初の写真だけを載せた'],['approvedとstill looked livelyが根拠。','名前の公開を避けた。','了承済みの写真を掲載した。','最初に確認する方針を守った。'],'It still looked lively.')],
 [('最初の実験で水の減り方の原因を特定できなかった理由は？',['ふたと置き場所を同時に変えたため','水位を全く見なかったため','両方の器を同じ位置に置いたため','二回目の結果だけを発表したため'],['changed both the covers and the locationsが条件の混在を示す。','数日後に水位を比較している。','それは再実験時の改善。','発表には両方の試みを入れた。'],'changed both the covers and the locations')],
 [('後の新聞記事が伝えた式は、何が加わった後に行われたか。',['観客席と更衣室','学校のプールと食堂','町の全ての家','図書館の蔵書'],['new seats and changing roomsの二設備。','本文にない施設。','住宅の整備ではない。','本の追加ではない。'],'new seats and changing rooms had been added'),('コウタが要約を二人に確認してもらったことから読み取れる姿勢は？',['記録と証言を照合して説明を確かめようとした','新聞があれば証言は全て不要と判断した','片方の記憶を理由なく削ろうとした','式の日付を自分で変更しようとした'],['新聞の日付で違いを説明し、二人にも確認する流れ。','両方の取材を残した。','削除せず二段階の記憶として説明した。','歴史上の日付を変更する話ではない。'],'asked the neighbors to check his summary')],
 [('新しい説明ページが示したのは？',['開始時の配置と一回の手番','全ての動物の実際の飼い方','学校祭の入場料金だけ','制作した生徒の成績'],['starting positionとone complete turnが直接の根拠。','木製の動物を動かすゲームで、飼育の説明ではない。','料金ではなく手順の例。','成績は述べていない。'],'the starting position and one complete turn')],[]
]
for i,(p,questions) in enumerate(zip(out,extras)):
 for prompt,options,reasons,quote in questions:
  order=list(range(4));shift=(i+len(p['questions']))%4;order=order[shift:]+order[:shift]
  p['questions'].append({'id':f"q{len(p['questions'])+1}",'prompt':prompt,'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],'evidence':{'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}})
path=ROOT/'content/readings/enriched-level1-021-025.json'
if path.exists():assert json.loads(path.read_text())==out,'refuse changed saved revision'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Compiled',len(out),'readings and',sum(len(p['sentences']) for p in out),'sentences')
