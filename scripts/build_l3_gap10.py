"""Compile explicitly annotated original L3 sentence/phrase gaps. No automatic syntax guessing."""
import copy, json, re, xml.etree.ElementTree as ET
from pathlib import Path
from level3_word_policy import validate_level3_word_count
from content_pipeline import validate_reading, validate_provenance
ROOT=Path(__file__).resolve().parents[1]
AUTHOR=ROOT/'content/authoring/readings'
def words(text):return len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",text))
def parse_sentence(markup):
    root=ET.fromstring('<r>'+markup+'</r>');out=[];nodes=[];gaps=[];aliases={};links=[];root_verbs=[];root_modifiers=[]
    def walk(e,depth=0,parent=None):
        start=sum(map(len,out));node=None
        if e.tag in ('S','V','O','C','M','clause','phrase'):
            node={'id':f'n{len(nodes)+1}','role':e.tag,'start':start,'depth':depth}
            if e.get('k'):node['kind']=e.get('k')
            nodes.append(node)
            if parent is None and e.tag=='V':root_verbs.append(node['id'])
            if parent is None and e.tag=='M' and not e.get('to'):root_modifiers.append(node['id'])
            aliases.setdefault(e.tag.lower(),node['id'])
            if e.get('id'):aliases[e.get('id')]=node['id']
            if e.get('to'):links.append((node['id'],e.get('to')))
            elif parent and e.tag in ('phrase','M') and parent['role'] in ('S','O','C'):
                links.append((node['id'],parent['id']))
        if e.text:out.append(e.text)
        for child in e:
            walk(child,depth+int(e.tag in ('clause','phrase')),node or parent)
            if child.tail:out.append(child.tail)
        end=sum(map(len,out))
        if node:node['end']=end
        if e.tag in ('gap','g'):gaps.append((start,end))
    walk(root)
    text=''.join(out)
    for n in nodes:n['text']=text[n['start']:n['end']]
    # Authoring convention: a root M modifies the main predicate unless given an explicit target.
    if root_verbs:
        aliases['v']=root_verbs[0]
        links.extend((n,root_verbs[0]) for n in root_modifiers)
    edges=[{'from':a,'to':aliases.get(b,b),'type':'modifies'} for a,b in links]
    assert any(n['role']=='S' for n in nodes) and any(n['role']=='V' for n in nodes),(text,nodes)
    assert len(re.findall(r'[.!?](?=\s|$)',text))==1 and text[-1] in '.!?',text
    assert all(e['to'] in {n['id'] for n in nodes} for e in edges)
    return text,nodes,edges,gaps

def read_authored(form=2):
    readings=[];current=None;para=None
    for line in (AUTHOR/f'l3-f{form:02}.tsv').read_text().splitlines():
        if line.startswith('# '):
            current={'title':line.split(' ',2)[2],'paragraphs':[]};readings.append(current);para=None
        elif not line.strip():para=None
        else:
            assert current is not None
            if para is None:para=[];current['paragraphs'].append(para)
            fields=line.split('\t');assert len(fields)==3,fields
            para.append(fields)
    return readings

def compile_batch(form=2):
    assert form in (2,3),'Supported authored gap formats are 2 and 3'
    authored=read_authored(form);questions=json.loads((AUTHOR/f'l3-f{form:02}-questions.json').read_text())
    assert len(authored)==len(questions)==10
    batch=[]
    for i,(a,qs) in enumerate(zip(authored,questions),1):
        pid=f'reading-l3-f{form:02}-{i:02}';review=[];source=[];syntax=[];sentences=[];gap=None
        assert 4<=len(a['paragraphs'])<=8
        for j,rows in enumerate(a['paragraphs'],1):
            paraid=f'p{j}';english=[];translations=[];para_gap=None;offset=0
            for k,(markup,jp,note) in enumerate(rows,1):
                en,spans,edges,gaps=parse_sentence(markup);sid=f'{paraid}-s{k:03}'
                assert jp and note
                if gaps:
                    assert gap is None and len(gaps)==1
                    ga,gb=gaps[0];gap={'paragraphId':paraid,'start':offset+ga,'end':offset+gb,'answer':en[ga:gb]};para_gap=gap
                for n in spans:n['start']+=offset;n['end']+=offset
                sy={'id':f'{pid}:{sid}','sentenceId':sid,'paragraphId':paraid,'sentence':en,'translation':jp,'start':offset,'end':offset+len(en),'explanation':note,'spans':spans,'relations':edges,'skeleton':' / '.join(n['role']+': '+n['text'] for n in spans if n['role'] in ('S','V','O','C')),'grammarPoints':[note],'readingOrder':'主節のSとVを確認し、句節の階層と修飾先、対比・条件・否定の範囲をたどって全文訳と照合する。','offsetBasis':'reviewParagraphs','reviewStatus':'ai_author_checked_human_pending'}
                syntax.append(sy);sentences.append({'id':sid,'paragraphId':paraid,'english':en,'translation':jp,'start':offset,'end':offset+len(en),'syntaxId':sy['id']})
                english.append(en);translations.append(jp);offset+=len(en)+1
            full=' '.join(english);original=full if not para_gap else full[:para_gap['start']]+'[1]'+full[para_gap['end']:]
            review.append({'id':paraid,'english':full,'translation':''.join(translations)})
            source.append({'id':paraid,'english':original,'translation':''.join(translations)})
        assert gap is not None
        if form==3:
            row=next(s for s in sentences if s['paragraphId']==gap['paragraphId'] and s['start']<=gap['start']<s['end'])
            assert gap['start']==row['start'] and gap['end']==row['end']-1,'Format 3 must omit the complete assertion, retaining terminal punctuation'
            assert len(gap['answer'].split())>=8
        for s in sentences:
            delta=len(gap['answer'])-3 if s['paragraphId']==gap['paragraphId'] else 0
            def source_pos(pos):
                if not delta or pos<=gap['start']:return pos
                assert pos>=gap['end']
                return pos-delta
            s['sourceStart']=source_pos(s['start']);s['sourceEnd']=source_pos(s['end'])
            para=next(p for p in source if p['id']==s['paragraphId'])
            s['sourceEnglish']=para['english'][s['sourceStart']:s['sourceEnd']]
        count=words(' '.join(p['english'] for p in review));validate_level3_word_count(form,i,count)
        built=[]
        assert 5<=len(qs)<=8
        for j,q in enumerate(qs):
            assert len(q['options'])==4
            if j==0:assert q['options'][q.get('correctIndex',0)][0]==gap['answer']
            order=list(range(4));shift=(i+2*j)%4;order=order[shift:]+order[:shift]
            built.append({'id':f'q{j+1}','prompt':q['prompt'],'options':[{'id':'abcd'[k],'text':q['options'][n][0],'explanation':q['options'][n][1]} for k,n in enumerate(order)],'correctOptionId':'abcd'[order.index(q.get('correctIndex',0))],'explanation':q['options'][q.get('correctIndex',0)][1],'evidence':{'paragraphId':next(p['id'] for p in source if q['quote'] in p['english']),'quote':q['quote']}})
        p={'id':pid,'level':3,'format':form,'title':a['title'],'paragraphs':source,'reviewParagraphs':review,'wordCount':words(' '.join(p['english'] for p in source)),'reviewWordCount':count,'syntaxOffsetBasis':'reviewParagraphs','gapSolutions':{'[1]':{'questionId':'q1','answer':gap['answer']}},'sentences':sentences,'syntax':syntax,'questions':built,'recommendedSeconds':round((count/75*60+len(built)*55)/15)*15,'vocabulary':[{'english':gap['answer'],'meaning':qs[0]['meaning']}],'content':{'sourceIds':['original-reading-l3-v1'],'sourceUsage':[{'sourceId':'original-reading-l3-v1','fields':['title','paragraphs','questions','syntax','vocabulary']}],'contentVersion':2,'standardVersion':2,'qualityStatus':'review_required','autoChecked':True,'humanReviewed':False,'productionApproved':False,'examFrequency':None,'selectionReason':('独自の仮想事例によるLEVEL3語句空所補充。形式内の番号別完成語数・全英文の和訳と明示的構文を適用。人間の正式校閲は未実施。' if form==2 else '独自の仮想事例によるLEVEL3文・節の空所補充。前後の論理・照応・条件を統合し、完成語数・全文和訳・明示的構文を検証。独立人間校閲は未実施。')},'difficulty':{'scores':{'vocabulary':3,'syntax':4,'logic':3,'questions':3},'method':'AI rubric, author assessed','status':'ai_assessed_human_pending','rationale':'複数段落の主張・条件・反論を統合し、文脈に合う語句と推論範囲を判断する。'},'editorialReview':{'status':'author_checked','reviewer':'AI author; not independent human review','independentHumanReviewed':False},'review':{k:'ai_checked_human_pending' for k in ['fullTranslation','fullSyntax','questionUniqueness','englishNaturalness']}}
        errors=validate_reading(p)+validate_provenance(p['content'],{s['id']:s for s in json.loads((ROOT/'content/sources.json').read_text())},False);assert not errors,(pid,errors)
        batch.append(p)
    return batch

def write_immutable(path,value):
    if path.exists():assert json.loads(path.read_text())==value,('Refuse different saved batch',str(path))
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main(form=2):
    batch=compile_batch(form);write_immutable(ROOT/f'content/readings/l3_f{form:02}.json',batch)
    path=ROOT/'content/readings/advanced.json';old=json.loads(path.read_text());byid={p['id']:p for p in old}
    for p in batch:
        if p['id'] in byid:assert byid[p['id']]==p
        else:old.append(p)
    path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
    path=ROOT/'content/readings/difficulty.json';ratings=json.loads(path.read_text());ratings['ratings'].update({p['id']:p['difficulty'] for p in batch});path.write_text(json.dumps(ratings,ensure_ascii=False,indent=2)+'\n')
    raw=json.loads((ROOT/'content/readings/drafts.json').read_text())+old
    checkpoint={'authoredPassages':len(raw),'totalQuestions':sum(len(p['questions']) for p in raw),'totalWords':sum(p.get('reviewWordCount',p['wordCount']) for p in raw),'complete':len(raw)==400,'levels':{str(l):{'authoredPassages':sum(p['level']==l for p in raw),'countsByFormat':[sum(p['level']==l and p['format']==f for p in raw) for f in range(1,11)],'complete':all(sum(p['level']==l and p['format']==f for p in raw)==10 for f in range(1,11))} for l in range(1,5)},'humanReviewed':False,'productionApproved':False}
    (ROOT/'analysis/reading_checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n')
    manifest={'batch':f'l3-f{form:02}-10','humanReviewed':0,'passages':[{'id':p['id'],'words':p['wordCount'],'completedWords':p['reviewWordCount'],'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),'sentences':len(p['sentences'])} for p in batch]}
    (ROOT/f'analysis/reading_l3_f{form:02}_batch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
if __name__=='__main__':
    import sys
    main(int(sys.argv[1]) if len(sys.argv)>1 else 2)
