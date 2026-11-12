import copy,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
batch_start=int(sys.argv[1]) if len(sys.argv)>1 else 0
source='l1-first5.tsv' if batch_start==0 else 'l1-next5.tsv'
assert batch_start in (0,5),'Use an explicitly authored batch'
base=json.loads((root/'content/readings/drafts.json').read_text());lines=iter((root/'content/authoring/reading-enrichment'/source).read_text().splitlines());out=[]
for original in base[batch_start:batch_start+5]:
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
if batch_start==5:
 extras=[
  [('変更後の効果を確かめ続けるため、給食班は何をしたか。','毎月一度、食べ残しを測った','生徒ごとの成績を公表した','金曜の図書館を閉鎖した','毎週ご飯の量を倍にした','once each month')],
  [('部が空き教室の消灯を促すためにしたことは何か。','スイッチの近くに注意カードを置いた','全ての階段を閉鎖した','電気を一日中つけた','全ての教室を暗い色に塗った','reminder cards near classroom switches'),('翌年の部員のために残したものは何か。','調査に使った地図','練習中の試合の記録だけ','全員の電気代の請求書','植物の写真','its maps')],
  [('説明を書き直したとき、以前の事実情報はどう扱ったか。','下の小さな欄に残した','全て削除した','来館者には秘密にした','誤りだと断定した','They kept the old facts in a smaller box below.')],
  [('案内係で手伝うことに同意したとき、マイは一日をどう予想したか。','退屈になると思った','必ずリレーで優勝すると思った','競技が全て中止になると思った','学校へ行く必要がないと思った','she expected to have a boring day'),('案内係を経験した後も残っていた気持ちはどれか。','競走に出られたらよかったという気持ち','先生に感謝されることへの怒り','案内板を使う友人への不信','運動会をなくしたいという希望','Mai still wished she had been able to race.')],[]]
for p,qs in zip(out,extras):
 for prompt,correct,*rest in qs:
  wrong=rest[:3];quote=rest[3];para=next((x for x in p['paragraphs'] if quote in x['english']),None);assert para,(p['id'],quote);qid=f"q{len(p['questions'])+1}"
  p['questions'].append({'id':qid,'prompt':prompt,'options':[{'id':c,'text':t,'explanation':('本文の「'+quote+'」に対応する。') if i==0 else ('本文は「'+quote+'」と述べており、この選択肢の内容は示していない。')} for i,(c,t) in enumerate(zip('abcd',[correct]+wrong))],'correctOptionId':'a','explanation':'本文の「'+quote+'」を確認する。','evidence':{'paragraphId':para['id'],'quote':quote}})
 p['review']={'fullTranslation':'ai_checked_human_pending','fullSyntax':'ai_checked_human_pending','questionUniqueness':'ai_checked_human_pending'}
if batch_start==5:
 structures=json.loads((root/'content/authoring/reading-enrichment/l1-next5-structure.json').read_text())
 reasons={
 'reading-l1-f01-06':[['once each monthに対応し、変更後の効果を継続して調べた。','個人名も記録しない調査であり、成績の公表はしていない。','金曜の図書館の開館が遅いことは説明されるが、閉鎖はしていない。','両日のご飯の量は同じであり、量を倍にする変更ではない。']],
 'reading-l1-f01-07':[['教室スイッチの近くにreminder cardsを置いたと明記される。','階段は閉鎖でなく安全用の照明を求めた。','空き教室のつけっぱなしを減らす目的に反する。','教室の塗装を変えたという記述はない。'],['its mapsを翌年の部員のために保存したとある。','調査対象は校内の利用状況で、試合の記録だけを残したとはない。','電気代の個別請求書を作成・保存したとはない。','植物の写真はこの長文に登場しない。']],
 'reading-l1-f01-08':[['kept the old facts in a smaller box belowが直接の根拠。','元の情報を残したと明示され、全削除と矛盾する。','来館者に見える小さい欄であり秘密にしていない。','元の情報はcorrectと認められている。']],
 'reading-l1-f01-09':[['although she expected to have a boring dayに対応する。','足首を痛めてリレーに出られないことが導入で示される。','暑さによる予定変更は後で起きることで、全中止の予想ではない。','案内係の手伝いに同意しており、欠席する話ではない。'],['still wished she had been able to raceは参加できなかったことへの願い。','先生への怒りは述べず、先生は最後に感謝している。','友達は掲示板を確認しており、それを不信とする記述はない。','運動会をなくすのでなく、支える役割の価値を認めた。']]
 }
 for passage in out:
  for question,why in zip(passage['questions'][3:],reasons.get(passage['id'],[])):
   for option,text in zip(question['options'],why):option['explanation']=text
   question['explanation']=why[0]
  for syntax in passage['syntax']:
   spec=structures.get(syntax['id'])
   if not spec:continue
   sentence=syntax['sentence']
   for role,text,depth,kind in spec['nodes']:
    matches=[m.start() for m in re.finditer(r'(?<!\w)'+re.escape(text)+r'(?!\w)',sentence)];assert len(matches)==1,(syntax['id'],text)
    node=next((n for n in syntax['spans'] if n['text']==text and n['role']==role),None)
    if node is None:
     node={'id':f"n{len(syntax['spans'])+1}",'role':role,'text':text,'start':syntax['start']+matches[0],'end':syntax['start']+matches[0]+len(text)};syntax['spans'].append(node)
    node.update(depth=depth,kind=kind)
   for source,target,kind in spec['edges']:
    a=next(n for n in syntax['spans'] if n['text']==source);b=next(n for n in syntax['spans'] if n['text']==target)
    syntax['relations']=[r for r in syntax['relations'] if r['from']!=a['id']]
    syntax['relations'].append({'from':a['id'],'to':b['id'],'type':kind})
path=root/'content/readings/enriched.json'
previous=json.loads(path.read_text()) if path.exists() else []
byid={p['id']:p for p in previous}
for p in out:
 if p['id'] in byid:assert byid[p['id']]==p,'Refuse to overwrite an already saved revision: '+p['id']
 else:previous.append(p)
path.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
print('Enriched',len(out),'readings',sum(len(x['sentences']) for x in out),'sentences')
