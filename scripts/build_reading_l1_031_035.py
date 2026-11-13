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
 'reading-l1-f04-01':['A small white bird stood','That afternoon,','For the next week,'],
 'reading-l1-f04-02':['Emma suggested','The baker tested'],
 'reading-l1-f04-03':['His aunt suggested','Tom visited the area again.'],
 'reading-l1-f04-04':["The class contacted","Students cleaned","At the first performance,"],
 'reading-l1-f04-05':['One day,','Lucy chose'],
 }.get(original['id'])
 if not starts:return copy.deepcopy(original['paragraphs']),[]
 source=original['paragraphs'][0];text=source['english'];cuts=[0]+[text.index(x) for x in starts]+[len(text)];rows=[];mapping=[]
 for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
  while b>a and text[b-1].isspace():b-=1
  ident=f'p{i+1}';rows.append({'id':ident,'english':text[a:b],'translation':''});mapping.append({'paragraphId':ident,'sourceParagraphId':source['id'],'start':a,'end':b})
 assert ' '.join(x['english'] for x in rows)==text
 return rows,mapping
base=json.loads((ROOT/'content/readings/drafts.json').read_text())
lines=iter((ROOT/'content/authoring/reading-enrichment/l1-031-035.tsv').read_text().splitlines())
solutions=['']*5;out=[]
for original,answer in zip(base[30:35],solutions):
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
 'who needed to reach other shops':'People',
 'that practiced in an empty hall':"a children's theater group",
 'they had used for years':'chairs',
 'people might need':'other things',
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
 [('美術の授業でベンが描いたものは？',['鳥と橋と作業員の明るい帽子','携帯の修理方法だけ','初めて見た別の学校','雨でなくなった橋'],['drewの後に三つの題材が並ぶ。','携帯の修理図ではない。','自分の毎日の道中を描いた。','橋がなくなったとは述べていない。'],"Ben drew the bird, the bridge, and the worker's bright hat.")],
 [('番号札があれば、客は何ができたか。',['近くの広場で待つか他店を訪ねる','順番を無視していつでも入る','パンを無料で受け取る','全ての店を閉鎖する'],['could waitとvisitが順番までの選択肢を示す。','入れる番号は掲示板で示した。','料金の変更ではない。','他店を訪ねられる仕組み。'],'Customers could wait in the nearby square or visit another shop'),('試行後に他の店にも利点があったと分かる記述は？',['初めて訪れる店を発見した客がいた','パンの材料を全て変えた','地元のテレビ番組が終了した','広場が消えた'],['customers ... discovered shopsという観察が根拠。','bread did not changeとある。','番組終了の記述はない。','広場は待機場所として利用した。'],'they had discovered shops they had never visited')],
 [],
 [('劇団へ送る椅子の選び方は？',['掃除と点検をして安全なものだけ送る','壊れた部品も全部客席に使う','古いものは必ず全て捨てる','新品を学校が買ってから送る'],['cleaned、checked、only the safe onesが手順と条件。','壊れた部品は別にリサイクルした。','丈夫な椅子は再利用した。','学校で使った椅子を送った。'],'They sent only the safe ones to the theater.')],
 [('兄のノートに含まれていたものは？',['消した単語や矢印、下絵、答えのない問い','他人に見せる完成原稿だけ','一文字もない空白だけ','劇の入場券だけ'],['containedの後の四項目が根拠。','完成した本でなくてもよいと説明した。','実際に使われ書き込みがある。','入場券は述べていない。'],'crossed-out words, arrows, rough drawings, and questions without answers'),('ルーシーは使ったノートをどう感じたか。',['棚のきれいなノートより誇らしく思った','間違いがあるので必ず捨てようと思った','兄に全ページの清書を強制した','劇に役立たなかったと判断した'],['more proud ... thanの比較が直接の根拠。','間違いは進歩の印になった。','兄への清書依頼はない。','劇が完成した。'],'She felt more proud of that used notebook')]
]
for i,(p,questions) in enumerate(zip(out,extras)):
 for prompt,options,reasons,quote in questions:
  order=list(range(4));shift=(i+len(p['questions']))%4;order=order[shift:]+order[:shift];qid=f"q{len(p['questions'])+1}"
  evidence={'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}
  p['questions'].append({'id':qid,'prompt':prompt,'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],'evidence':evidence})
  p['reviewEvidence'][qid]={'paragraphId':next(x['id'] for x in p['reviewParagraphs'] if quote in x['english']),'quote':quote}
path=ROOT/'content/readings/enriched-level1-031-035.json'
if path.exists():assert json.loads(path.read_text())==out,'refuse changed saved revision'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Compiled',len(out),'readings and',sum(len(p['sentences']) for p in out),'sentences')
