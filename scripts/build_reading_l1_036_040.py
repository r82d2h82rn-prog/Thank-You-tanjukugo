"""Materialize the authored five gap exercises, with separate review coordinates."""
import copy,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Range:
 def __init__(self,row):self.row=row
 def start(self):return self.row['start']
 def end(self):return self.row['end']
 def group(self):return self.row['english']
def ranges(text):
 result=subprocess.run(['node','--import','tsx','scripts/sentence_ranges_json.ts'],input=json.dumps([{'paragraphId':'p','text':text}]),text=True,capture_output=True,cwd=ROOT,check=True)
 return [Range(row) for row in json.loads(result.stdout)[0]]
# Only paragraph boundaries change. The underlying source remains immutable.
def exercise_paragraphs(original):
 starts={
 'reading-l1-f04-06':['Sam realized','The second walk'],
 'reading-l1-f04-07':['A volunteer named Amy','For the next music evening,','Amy explained'],
 'reading-l1-f04-08':['The cheaper lamp','In the end,'],
 'reading-l1-f04-09':['The discussion became','The following month,'],
 'reading-l1-f04-10':['For the second meeting,','During the meeting,','The meeting ended'],
 }.get(original['id'])
 if not starts:return copy.deepcopy(original['paragraphs']),[]
 source=original['paragraphs'][0];text=source['english'];cuts=[0]+[text.index(x) for x in starts]+[len(text)];rows=[];mapping=[]
 for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
  while b>a and text[b-1].isspace():b-=1
  ident=f'p{i+1}';rows.append({'id':ident,'english':text[a:b],'translation':''});mapping.append({'paragraphId':ident,'sourceParagraphId':source['id'],'start':a,'end':b})
 assert ' '.join(x['english'] for x in rows)==text
 return rows,mapping
base=json.loads((ROOT/'content/readings/drafts.json').read_text())
lines=iter((ROOT/'content/authoring/reading-enrichment/l1-036-040.tsv').read_text().splitlines())
solutions=['']*5;out=[]
for original,answer in zip(base[35:40],solutions):
 p=copy.deepcopy(original);p['content']['contentVersion']=2;p['previousSyntax']=p['syntax'];p['syntax']=[];p['sentences']=[]
 exercise,mapping=exercise_paragraphs(original);p['exerciseParagraphs']=exercise;p['paragraphMappings']=mapping;p['reviewParagraphs']=copy.deepcopy(exercise);p['syntaxOffsetBasis']='reviewParagraphs'
 for source,review in zip(p['exerciseParagraphs'],p['reviewParagraphs']):
  review['english']=source['english'].replace('[1]',answer)
  matches=ranges(review['english'])
  mapping_row=next((x for x in mapping if x['paragraphId']==source['id']),{'sourceParagraphId':source['id'],'start':0})
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
   p['syntax'].append(syntax);p['sentences'].append({'id':sid,'paragraphId':source['id'],'english':en,'translation':jp,'start':m.start(),'end':m.end(),'sourceEnglish':old_text,'sourceStart':old_start+mapping_row['start'],'sourceEnd':old_end+mapping_row['start'],'sourceParagraphId':mapping_row['sourceParagraphId'],'syntaxId':syntax['id']});translations.append(jp)
  source['translation']=review['translation']=''.join(translations)
 for raw in p['paragraphs']:
  selected=[x for x in p['reviewParagraphs'] if next((m['sourceParagraphId'] for m in mapping if m['paragraphId']==x['id']),x['id'])==raw['id']]
  raw['translation']=''.join(x['translation'] for x in selected)
 p['reviewEvidence']={q['id']:{'paragraphId':next(x['id'] for x in p['reviewParagraphs'] if q['evidence']['quote'] in x['english']),'quote':q['evidence']['quote']} for q in p['questions']}
 p['reviewWordCount']=len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",' '.join(x['english'] for x in p['reviewParagraphs'])))
 p['review']={'fullTranslation':'ai_checked_human_pending','fullSyntax':'ai_checked_human_pending','questionUniqueness':'ai_checked_human_pending'};out.append(p)
try:next(lines);raise AssertionError('unused authored annotation')
except StopIteration:pass





anchors={
 'who had missed the first invitation':'several',
 'that looked almost the same':'two lamps',
 'that the shop did not sell':'battery',
 'that mattered to her':'the costs and features',
 'where each member showed one picture':'a meeting',
 'that was too dark':'a photograph',
 'that had not turned out well':'pictures',
 'he had learned from his friends':'ideas',
 'who had read carefully':'several students',
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
 [('二回目の散歩について正しいのは？',['時間は長くかかったが全員一緒に着いた','サムだけで歩く企画に変えた','写真撮影を全員禁止した','最も速い人だけ参加させた'],['took longerとeveryone ... togetherが根拠。','団体として歩く計画を改善した。','禁止したという記述はない。','参加者を速さで排除していない。'],'The second walk took longer, but everyone reached the end together')],
 [],
 [('購入前にミアが調べたことは？',['部品交換と返品可能な期間','学校の全生徒の成績','父親が初めて買った本','店の開店前の天気'],['whether a broken part ... とhow long ... returnsが根拠。','成績は本文にない。','本は購入対象ではない。','天気は選択理由ではない。'],'whether a broken part could be replaced and how long the shop would accept returns'),('二つ目を選んだ具体的な利用予定は？',['毎晩自分の机で使う','島への配達に使う','森の中に一年置く','同じ日に使い捨てる'],['use it at her desk every eveningが直接の根拠。','配達用ではない。','屋外放置の計画はない。','継続利用する計画。'],'use it at her desk every evening')],
 [('最後にアレックスはどうしたか。',['友人の助言を使い木々をより鮮明に撮った','暗い写真を理由に退部した','全ての仲間の写真を隠した','カメラの設定変更を禁止した'],['returned ... took a clearer photographという結末。','退部せず撮り直した。','他の部員も作品を共有した。','設定の変更は助言の一つ。'],'Alex returned to the trees and took a clearer photograph')],
 [('第一回で、よく読んだ生徒も発言が少なかった背景は？',['会話が速く本全体を一度に扱った','全員が本を読むことを禁止された','短い小説を一切選ばなかった','他校との通信を永久にやめた'],['whole book at onceとconversation moved quicklyが状況を示す。','had read carefullyとある。','同じ短い小説を選んでいる。','次回もオンラインで話し合った。'],'The conversation moved quickly'),('会の終わりに問いが増えたことは、本文でどう扱われるか。',['次も読みたいと思える丁寧な対話の一部','全員が活動をやめる理由','先生が読書を禁止した理由','最速回答者だけを決める試験の成功'],['more questionsがあってもeveryone wanted to read the next book。','継続への意欲がある。','先生は変化を喜んだ。','rather than a testとあり試験とは異なる。'],'everyone wanted to read the next book')]
]
for i,(p,questions) in enumerate(zip(out,extras)):
 for prompt,options,reasons,quote in questions:
  order=list(range(4));shift=(i+len(p['questions']))%4;order=order[shift:]+order[:shift];qid=f"q{len(p['questions'])+1}"
  evidence={'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}
  p['questions'].append({'id':qid,'prompt':prompt,'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],'evidence':evidence})
  p['reviewEvidence'][qid]={'paragraphId':next(x['id'] for x in p['reviewParagraphs'] if quote in x['english']),'quote':quote}
path=ROOT/'content/readings/enriched-level1-036-040.json'
if path.exists():assert json.loads(path.read_text())==out,'refuse changed saved revision'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Compiled',len(out),'readings and',sum(len(p['sentences']) for p in out),'sentences')
