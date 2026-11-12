"""Materialize the authored five gap exercises, with separate review coordinates."""
import copy,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=json.loads((ROOT/'content/readings/drafts.json').read_text())
lines=iter((ROOT/'content/authoring/reading-enrichment/l1-gap5.tsv').read_text().splitlines())
solutions=['because','gradually','invisible','clearly','different'];out=[]
for original,answer in zip(base[10:15],solutions):
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
    k=used.get(text,0);start=m.start()+hits[k];used[text]=k+1
    spans.append({'id':f'n{n+1}','role':role,'text':text,'start':start,'end':start+len(text)})
   assert any(s['role']=='S' for s in spans) and any(s['role']=='V' for s in spans)
   verb=next(s for s in spans if s['role']=='V');relations=[]
   for n,node in enumerate(spans):
    if node['role']=='M':relations.append({'from':node['id'],'to':verb['id'],'type':'modifies'})
    elif node['role']=='clause':relations.append({'from':node['id'],'to':verb['id'],'type':'clause'})
   notes=[s['explanation'] for s in original['syntax'] if s['paragraphId']==source['id'] and s['sentence'] in old_m.group()]
   explanation=note+(' 既存の部分解説：'+' '.join(notes) if notes else '')
   syntax={'id':f"{p['id']}:{sid}",'passageId':p['id'],'contentVersion':2,'paragraphId':source['id'],'sentenceId':sid,'sentence':en,'start':m.start(),'end':m.end(),'translation':jp,'explanation':explanation,'spans':spans,'relations':relations,'skeleton':' / '.join(s['role']+': '+s['text'] for s in spans if s['role'] in ('S','V','O','C')),'grammarPoints':[note],'readingOrder':'主節の主語と動詞を確認し、解説に沿って句節・否定・比較の範囲を読み、日本語訳で意味を確かめる。','reviewStatus':'ai_author_checked_human_pending','offsetBasis':'reviewParagraphs'}
   p['syntax'].append(syntax);p['sentences'].append({'id':sid,'paragraphId':source['id'],'english':en,'translation':jp,'start':m.start(),'end':m.end(),'sourceEnglish':old_m.group(),'sourceStart':old_m.start(),'sourceEnd':old_m.end(),'syntaxId':syntax['id']});translations.append(jp)
  source['translation']=review['translation']=''.join(translations)
 p['reviewWordCount']=len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",' '.join(x['english'] for x in p['reviewParagraphs'])))
 p['review']={'fullTranslation':'ai_checked_human_pending','fullSyntax':'ai_checked_human_pending','questionUniqueness':'ai_checked_human_pending'};out.append(p)
try:next(lines);raise AssertionError('unused authored annotation')
except StopIteration:pass
extras=[
 [('案内板はどのくらいの頻度で確認されたか。',['一時間ごと','一日に一度','祭りの前日だけ','質問があった時だけ'],['every hourが確認頻度を示す。','一日一回でなく毎時である。','祭り中にも定期的に点検した。','質問に応じた点検だけではない。'],'every hour'),('案内したのはどこからどこへの経路か。',['駅からコンサート会場','学校から図書館','会場から全員の自宅','駅から博物館'],['第一段落で駅とconcert fieldが両端として示される。','学校と図書館の経路ではない。','自宅への送迎は述べない。','博物館はこの長文に出てこない。'],'from the station to the concert field')],
 [('叔父が単純な二倍計算に注意を促した理由はどれか。',['鍋による水の減り方や野菜の大きさに違いがあるため','四人家族ではスープを作れないため','図書館の本は調理に使ってはいけないため','材料を量る方法が存在しないため'],['水の減る速度と野菜の大きさという具体的な条件の違いが示される。','実際に四人分の夕食を作った。','本の利用禁止ではなく調整方法の話である。','Hana measuredとあり計量はしている。'],'at a different speed')],
 [('飼い主はエミのどの行動に感謝したか。',['犬を連れて立ち去らず近くにいたこと','犬を新しい名前で呼んだこと','首輪を処分したこと','犬を教室へ連れて行ったこと'],['staying nearbyとwalking awayの対比が根拠。','名付けたという記述はない。','首輪は連絡先の確認に利用した。','翌日の教室で体験を話したのであって、犬を連れて行ったとはない。'],'staying nearby rather than walking away with the dog'),('クラスでの発表の後、先生は何をしたか。',['地域の役立つ連絡先を黒板に書いた','動物担当窓口を閉鎖した','生徒の質問を全て禁止した','犬を自分の家に連れて帰った'],['末文のwrote useful local contact informationに対応する。','窓口の閉鎖は述べない。','同級生は質問している。','先生が犬を引き取ったとはない。'],'useful local contact information on the board')],[],
 [('最初に橋の形を特に丁寧に描いたのは誰か。',['ジュン','ミキ','レオ','先生'],['Jun painted the shapeが直接の根拠。','ミキは日差しを色で表現した。','レオは橋を歩く家族を描いた。','先生の絵の描写はない。'],'Jun painted the shape of the bridge carefully.')]]
for i,(p,questions) in enumerate(zip(out,extras)):
 for prompt,options,reasons,quote in questions:
  order=list(range(4));shift=(i+len(p['questions']))%4;order=order[shift:]+order[:shift]
  p['questions'].append({'id':f"q{len(p['questions'])+1}",'prompt':prompt,'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],'evidence':{'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}})
path=ROOT/'content/readings/enriched.json';previous=json.loads(path.read_text());before=copy.deepcopy(previous)
byid={p['id']:p for p in previous}
for p in out:
 if p['id'] in byid:assert byid[p['id']]==p,'refuse changed saved revision'
 else:previous.append(p)
assert previous[:len(before)]==before
path.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
print('Added',len(out),'readings;',sum(len(p['sentences']) for p in out),'aligned sentences; retained',len(before),'previous revisions')
