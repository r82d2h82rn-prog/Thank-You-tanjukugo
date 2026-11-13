"""Record verified versus pending coverage without counting saved drafts as enriched."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
original=json.loads((root/'content/readings/drafts.json').read_text())[:100]
completed={}
for path in (root/'content/readings').glob('enriched*.json'):
 for passage in json.loads(path.read_text()):
  if passage['level']!=1:continue
  assert passage['id'] not in completed,passage['id']
  completed[passage['id']]=passage
pending=[i for i,p in enumerate(original,1) if p['id'] not in completed]
sentences=sum(len(p['sentences']) for p in completed.values());first=pending[0] if pending else None
status={'target':100,'sentenceComplete':len(completed),'humanReviewed':0,'allComplete':not pending,'next':first,'passages':[{'number':i,'id':p['id'],'title':p['title'],'status':'sentence_translation_and_syntax_complete_human_pending' if p['id'] in completed else 'not_enriched','alignedSentences':len(completed.get(p['id'],{}).get('sentences',[]))} for i,p in enumerate(original,1)]}
dump(root/'analysis/level1-through-100-status.json',status)
path=root/'analysis/reading_quality_progress.json';progress=json.loads(path.read_text());progress['levels']['1']['sentenceAlignedTranslationAndSyntaxEnriched']=len(completed)
progress['currentPriority']=f'LEVEL 1を100番まで補完中。累計{len(completed)}/100題{sentences}文。未補完{len(pending)}題、次は{first}番。正式人間校閲・端末実機確認は未完了。';dump(path,progress)
print(progress['currentPriority'])
