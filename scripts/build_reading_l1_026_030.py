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
 'reading-l1-f03-09':['The club leader, Lisa,','At the next meeting,'],
 'reading-l1-f03-10':['Mr. Lee changed the next discussion.','More hands went up than before.'],
 }.get(original['id'])
 if not starts:return copy.deepcopy(original['paragraphs']),[]
 source=original['paragraphs'][0];text=source['english'];cuts=[0]+[text.index(x) for x in starts]+[len(text)];rows=[];mapping=[]
 for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
  while b>a and text[b-1].isspace():b-=1
  ident=f'p{i+1}';rows.append({'id':ident,'english':text[a:b],'translation':''});mapping.append({'paragraphId':ident,'sourceParagraphId':source['id'],'start':a,'end':b})
 assert ' '.join(x['english'] for x in rows)==text
 return rows,mapping
base=json.loads((ROOT/'content/readings/drafts.json').read_text())
lines=iter((ROOT/'content/authoring/reading-enrichment/l1-026-030.tsv').read_text().splitlines())
solutions=[next(o['text'] for o in p['questions'][0]['options'] if o['id']==p['questions'][0]['correctOptionId']) for p in base[25:30]];out=[]
for original,answer in zip(base[25:30],solutions):
 assert original['questions'][0]['options'][ord(original['questions'][0]['correctOptionId'])-97]['text']==answer
 assert sum(p['english'].count('[1]') for p in original['paragraphs'])==1
 p=copy.deepcopy(original);p['content']['contentVersion']=2;p['previousSyntax']=p['syntax'];p['syntax']=[];p['sentences']=[]
 p['gapSolutions']={'[1]':{'questionId':'q1','answer':answer}};exercise,mapping=exercise_paragraphs(original);p['exerciseParagraphs']=exercise;p['paragraphMappings']=mapping;p['reviewParagraphs']=copy.deepcopy(exercise);p['syntaxOffsetBasis']='reviewParagraphs'
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
 'that needed attention':'the places',
 'that the club had not expected':'questions',
 'that new members did not know':'words',
 'they had never tried':'dishes',
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
 [('サキが難所で気づいた具体的な動作は？',['次の音の前に一本の指を動かすこと','毎回全ての指を止め続けること','楽譜を上下逆さまに読むこと','途中を全て弾かないこと'],['one finger had to move before the next note beganが根拠。','必要なのは適切な指の先行移動。','楽譜の向きを変えたとはない。','練習した小節を残りにつなげた。'],'one finger had to move before the next note began')],
 [('曇天でも子供たちが練習できたことは？',['地図で北を見つけること','雲を望遠鏡で消すこと','本物の星を昼間に全部観測すること','次回の天候を必ず晴れに変えること'],['finding north on a mapとある。','雲を操作する活動ではない。','星の実観測はできないままだった。','将来の晴天に備えたのであり天候は変えない。'],'finding north on a map'),('保護者の質問に関して正しいのは？',['部員が予想していなかった質問も出た','全て事前に決められた質問だった','質問は全て禁止された','保護者は最後まで誰も来なかった'],['had not expectedが予想外の質問を示す。','予想していないものがあった。','実際に質問が出ている。','Parents asked questionsとある。'],'Parents asked questions that the club had not expected.')],
 [],
 [('メニューの葉の記号は何を表したか。',['肉なしの料理','特に辛い料理','最も値段が高い料理','売り切れた料理'],['A leaf showed meals without meatが根拠。','辛さを示すのは唐辛子の記号。','値段の記号とは述べない。','売り切れ表示ではない。'],'A leaf showed meals without meat'),('印刷前に店主へ絵の確認を頼んだ理由として適切なのは？',['絵が料理を正しく表すか確かめるため','料理名を全て消すため','部員の国籍を変えるため','質問を今後全て禁止するため'],['check each drawingと料理を示す記号の用途から判断する。','names or descriptionsは残した。','国籍変更の話ではない。','新しい部員は料理を質問できた。'],'check each drawing before printing the new menu')],
 [('静かな生徒が指摘した負担は？',['体操服と通常の制服の購入費','望遠鏡の借用料','昼食メニューの印刷枚数','全員の電車の運行時刻'],['buying sports clothes and regular uniforms could cost families a lotが根拠。','望遠鏡はこの長文にない。','メニューはこの長文にない。','交通の話ではない。'],'buying sports clothes and regular uniforms could cost families a lot')]
]
for i,(p,questions) in enumerate(zip(out,extras)):
 for prompt,options,reasons,quote in questions:
  order=list(range(4));shift=(i+len(p['questions']))%4;order=order[shift:]+order[:shift]
  qid=f"q{len(p['questions'])+1}";evidence={'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}
  p['questions'].append({'id':qid,'prompt':prompt,'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],'evidence':evidence})
  p['reviewEvidence'][qid]={'paragraphId':next(x['id'] for x in p['reviewParagraphs'] if quote in x['english']),'quote':quote}
path=ROOT/'content/readings/enriched-level1-026-030.json'
if path.exists():assert json.loads(path.read_text())==out,'refuse changed saved revision'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Compiled',len(out),'readings and',sum(len(p['sentences']) for p in out),'sentences')
