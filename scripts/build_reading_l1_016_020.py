"""Materialize the authored five gap exercises, with separate review coordinates."""
import copy,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=json.loads((ROOT/'content/readings/drafts.json').read_text())
lines=iter((ROOT/'content/authoring/reading-enrichment/l1-016-020.tsv').read_text().splitlines())
solutions=['shortest','important','careful','but','However'];out=[]
for original,answer in zip(base[15:20],solutions):
 assert original['questions'][0]['options'][ord(original['questions'][0]['correctOptionId'])-97]['text']==answer
 assert sum(p['english'].count('[1]') for p in original['paragraphs'])==1
 p=copy.deepcopy(original);p['content']['contentVersion']=2;p['previousSyntax']=p['syntax'];p['syntax']=[];p['sentences']=[]
 p['gapSolutions']={'[1]':{'questionId':'q1','answer':answer}};p['reviewParagraphs']=copy.deepcopy(p['paragraphs']);p['syntaxOffsetBasis']='reviewParagraphs'
 for source,review in zip(p['paragraphs'],p['reviewParagraphs']):
  review['english']=source['english'].replace('[1]',answer)
  sources=list(re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)',source['english']))
  matches=list(re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)',review['english']));assert len(sources)==len(matches)
  translations=[]
  for i,(m,old_m) in enumerate(zip(matches,sources)):
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
   p['syntax'].append(syntax);p['sentences'].append({'id':sid,'paragraphId':source['id'],'english':en,'translation':jp,'start':m.start(),'end':m.end(),'sourceEnglish':old_m.group(),'sourceStart':old_m.start(),'sourceEnd':old_m.end(),'syntaxId':syntax['id']});translations.append(jp)
  source['translation']=review['translation']=''.join(translations)
 p['reviewWordCount']=len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",' '.join(x['english'] for x in p['reviewParagraphs'])))
 p['review']={'fullTranslation':'ai_checked_human_pending','fullSyntax':'ai_checked_human_pending','questionUniqueness':'ai_checked_human_pending'};out.append(p)
try:next(lines);raise AssertionError('unused authored annotation')
except StopIteration:pass

extras=[
 [('ユウトが自転車から降りて歩いた理由は？',['坂がとても急だったから','駅が閉鎖されていたから','川があふれていたから','プールが休みだったから'],['so steep that ... walkが直接の根拠。','駅の閉鎖は述べていない。','川の氾濫は述べていない。','プールでは女子に会っている。'],'one hill was so steep'),('ユウトの提案は何を改善しようとしたものか。',['距離に加えて坂の情報と平らな経路も示すこと','全ての住民を同じ経路に限定すること','自転車でプールへ行くことを禁止すること','駅からプールまでの距離を短くする工事'],['mark hills and offer a flatter choiceという情報提供の改善。','only one routeの代わりに選択肢を増やす案。','移動は禁止していない。','工事ではなく地図の改善。'],'mark hills and offer a flatter choice')],
 [('月曜日の利用者について分かることは？',['既にはしごを予約していた','はしごを買い取ると約束していた','ハルに一週間の延長を頼んだ','店主の道具を全て修理していた'],['had already bookedとあり次の予約が成立済み。','購入ではなく借用の予約。','延長を望んだのはハル。','全道具の修理という記述はない。'],'Someone else had already booked it for Monday.')],
 [('印刷前に記事を調理員へ見せた目的は？',['仕事の内容を正しく理解したか確かめるため','給食の値段を上げてもらうため','サッカーの記事へ全て書き換えるため','新聞作りの中止を知らせるため'],['to make sure以下が確認の目的を述べる。','値上げの依頼はない。','実際に調理員の記事を掲載した。','新聞は完成し次号も計画している。'],'make sure that they had understood her work correctly'),('次号の取材方針として適切なのは？',['身近なものを新しい視点で見られる記事を探す','最も有名な人物だけを必ず選ぶ','記事の本人確認を禁止する','サッカー選手の記事以外は載せない'],['in a new wayと末文が取材方針の変化を示す。','有名さはもはや唯一の理由ではない。','確認は正確さのために行っている。','選手以外を初号で扱い好評だった。'],'notice something familiar in a new way')],
 [],
 [('字幕について確認した条件は？',['読む時間があり、発言内容とも一致すること','必ず一秒以内で消えること','登場人物と異なる話にすること','会場の前方からだけ読めること'],['long enough to readとmatch what ... sayingの二条件。','必要な読み時間を確保した。','発言と一致させる必要がある。','後方からも試写した。'],'long enough to read')]
]
for i,(p,questions) in enumerate(zip(out,extras)):
 for prompt,options,reasons,quote in questions:
  order=list(range(4));shift=(i+len(p['questions']))%4;order=order[shift:]+order[:shift]
  p['questions'].append({'id':f"q{len(p['questions'])+1}",'prompt':prompt,'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],'evidence':{'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}})
path=ROOT/'content/readings/enriched-level1-016-020.json'
if path.exists():assert json.loads(path.read_text())==out,'refuse changed saved revision'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Compiled',len(out),'readings and',sum(len(p['sentences']) for p in out),'sentences')
