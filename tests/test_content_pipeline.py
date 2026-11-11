import contextlib, csv, hashlib, io, json, pathlib, sys, tempfile, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from content_pipeline import audit, import_candidates, validate_reading, validate_provenance, validate_entry, write_json, write_csv, read_csv
from analyze_corpus import analyze, phrase_hits, tokens
from import_official_lists import parse_list, ingest
class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root=pathlib.Path(self.tmp.name)
        for d in ['content','analysis','src/data','content/words','content/idioms','content/readings']: (self.root/d).mkdir(parents=True,exist_ok=True)
        self.source={'id':'fixture','candidateExtraction':'granted','licenseEvidence':'Synthetic fixture owned by test suite','termsUrl':'https://example.invalid/fixture-terms','observedVersion':'test','commercialUse':'granted','redistribution':'granted'}
        write_json(self.root/'content/sources.json',[self.source]); write_json(self.root/'content/provenance.json',{}); write_json(self.root/'src/data/entries.json',[])
        write_json(self.root/'analysis/lemma_forms.json',{'developed':'develop','developing':'develop','gave':'give'})
        for k in ['words','idioms','readings']: write_json(self.root/f'content/{k}/approved.json',[])
        write_csv(self.root/'content/word_candidates.csv',[{'lemma':'develop'},{'lemma':'development'}],['lemma'])
        write_csv(self.root/'content/idiom_candidates.csv',[{'lemma':'give up'}],['lemma'])
        self.fields=['id','university','faculty','method','year','subject','url','terms_url','analysis_permission','redistribution_permission','license_evidence','local_path','sha256','missing_data']
    def exam(self,body='Develop developed developing development. She gave it up.',**override):
        (self.root/'analysis/input.txt').write_text(body)
        row=dict(id='synthetic-1',university='Synthetic University',faculty='Test faculty',method='fixture',year='2025',subject='English',url='https://example.invalid/fixture',terms_url='https://example.invalid/terms',analysis_permission='granted',redistribution_permission='denied',license_evidence='Synthetic original test text',local_path='analysis/input.txt',sha256=hashlib.sha256(body.encode()).hexdigest(),missing_data='')
        row.update(override); write_csv(self.root/'analysis/exam_sources.csv',[row],self.fields); return row
    def test_formal_approval_requires_both_editorial_review_and_license_evidence(self):
        metadata=dict(sourceIds=['fixture'],contentVersion=1,qualityStatus='approved',humanReviewed=True,productionApproved=True,autoChecked=True,selectionReason='Synthetic fixture')
        self.assertEqual(validate_provenance(metadata,{'fixture':self.source}),[])
        self.assertIn('editorial approval missing',validate_provenance({**metadata,'humanReviewed':False},{'fixture':self.source}))
        self.assertIn('rights unverified: fixture',validate_provenance(metadata,{'fixture':{**self.source,'redistribution':'unknown'}}))
    def test_existing_data_and_new_drafts_have_unique_identity_and_complete_structure(self):
        project=pathlib.Path(__file__).resolve().parents[1]
        samples=json.loads((project/'src/data/entries.json').read_text()); drafts=json.loads((project/'content/words/drafts.json').read_text())
        self.assertEqual(len(drafts),300); self.assertEqual(len({e['id'] for e in samples+drafts}),450)
        self.assertEqual(len({e['english'] for e in samples+drafts if e['kind']=='word'}),400)
        for level in [2,3,4]:
            section=[e for e in drafts if e['level']==level]
            self.assertEqual([e['number'] for e in section],list(range(1,101)))
            order={'動詞':0,'名詞':1,'形容詞':2,'副詞':3}
            self.assertEqual([order[e['pos']] for e in section], sorted(order[e['pos']] for e in section))
        sources={s['id']:s for s in json.loads((project/'content/sources.json').read_text())}; seen=set()
        for entry in drafts:
            self.assertEqual(validate_entry(entry,sources,seen,require_approval=False),[])
            self.assertFalse(entry['content']['humanReviewed']); self.assertFalse(entry['content']['productionApproved']); self.assertIsNone(entry['content']['examFrequency'])
    def test_unknown_permission_rejects_candidate_import(self):
        self.source['candidateExtraction']='unknown'; write_json(self.root/'content/sources.json',[self.source]); (self.root/'input.csv').write_text('lemma,rank\ndevelop,1\n')
        with self.assertRaises(ValueError): import_candidates(self.root/'input.csv','fixture','word',self.root)
    def test_candidate_normalization_merge_preserves_multiple_source_ranks(self):
        (self.root/'content/word_candidates.csv').unlink()
        (self.root/'input.csv').write_text('lemma,rank\nDevelop,1\n develop ,1\n')
        self.assertEqual(import_candidates(self.root/'input.csv','fixture','word',self.root),1)
        second={**self.source,'id':'fixture2'}; write_json(self.root/'content/sources.json',[self.source,second])
        import_candidates(self.root/'input.csv','fixture2','word',self.root)
        row=read_csv(self.root/'content/word_candidates.csv')[0]
        self.assertEqual(set(json.loads(row['source_ranks'])),{'fixture','fixture2'})
        self.assertEqual(row['exam_frequency'],'')
    def test_accented_english_is_not_corrupted_or_merged_with_unaccented_forms(self):
        (self.root/'content/word_candidates.csv').unlink()
        (self.root/'input.csv').write_text('lemma,rank\nrésumé,1\nre\u0301sume\u0301,1\nresume,2\n',encoding='utf-8')
        self.assertEqual(import_candidates(self.root/'input.csv','fixture','word',self.root),2)
        self.assertEqual({r['lemma'] for r in read_csv(self.root/'content/word_candidates.csv')},{'résumé','resume'})
    def test_upstream_hash_encoding_and_alphabetical_order_are_explicit(self):
        data='Word,Rank\nrésumé,26\ncafé,55\n'.encode('cp1252')
        spec={'sourceId':'fixture','sha256':hashlib.sha256(data).hexdigest(),'format':'csv','encoding':'cp1252','lemmaColumn':'Word','rankColumn':'Rank','observedRows':2}
        self.assertEqual(parse_list(data,spec),[{'lemma':'résumé','rank':'26'},{'lemma':'café','rank':'55'}])
        with self.assertRaises(ValueError): parse_list(data+b'changed',spec)
        data=b'A description\nReferences\nAuthor.\n\nabsorb\naccelerate\n'
        spec.update(sha256=hashlib.sha256(data).hexdigest(),format='alphabetized_text',encoding='utf-8',firstLemma='absorb')
        self.assertEqual(parse_list(data,spec),[{'lemma':'absorb','rank':''},{'lemma':'accelerate','rank':''}])
    def test_official_import_is_idempotent_and_never_auto_assigns_exam_frequency(self):
        project=pathlib.Path(__file__).resolve().parents[1]
        import shutil
        for folder in ['upstream']:
            shutil.copytree(project/'content'/folder,self.root/'content'/folder)
        shutil.copy(project/'content/sources.json',self.root/'content/sources.json')
        shutil.copy(project/'content/word_candidates.csv',self.root/'content/word_candidates.csv')
        first=ingest(self.root); before=(self.root/'content/word_candidates.csv').read_bytes(); second=ingest(self.root)
        self.assertEqual(before,(self.root/'content/word_candidates.csv').read_bytes())
        self.assertEqual(first['uniqueOfficialCandidates'],5619)
        rows={r['lemma']:r for r in read_csv(self.root/'content/word_candidates.csv')}
        self.assertEqual(json.loads(rows['absorb']['source_ranks'])['nawl']['rank'],None)
        self.assertEqual(rows['be']['status'],'不採用')
        self.assertTrue(all(r['exam_frequency']=='' for r in rows.values()))
    def test_no_permission_means_no_analysis_not_invented_frequency(self):
        self.exam(analysis_permission='unknown')
        result=analyze(self.root); self.assertEqual(result['examCount'],0); self.assertIsNone(result['confirmedIdiomCount'])
        self.assertEqual(read_csv(self.root/'analysis/word_frequency.csv'),[])
    def test_measured_lemma_counts_do_not_merge_derivations_and_no_text_is_exported(self):
        self.exam(); result=analyze(self.root); self.assertEqual(result['examCount'],1); self.assertEqual(result['corpusWords'],8)
        rows={r['lemma']:r for r in read_csv(self.root/'analysis/word_frequency.csv')}
        self.assertEqual(rows['develop']['count'],'3'); self.assertEqual(rows['development']['count'],'1'); self.assertAlmostEqual(float(rows['develop']['per_10000']),3750)
        hits=read_csv(self.root/'analysis/idiom_matches_review.csv'); self.assertEqual(len(hits),1); self.assertEqual(hits[0]['status'],'review_required')
        self.assertEqual(rows['develop']['adoption_score'],'')
        self.assertNotIn('She gave it up', (self.root/'analysis/idiom_matches_review.csv').read_text())
    def test_checksum_path_escape_and_duplicate_corpus_are_rejected(self):
        self.exam(sha256='bad')
        with self.assertRaises(ValueError): analyze(self.root)
        row=self.exam(); write_csv(self.root/'analysis/exam_sources.csv',[row,{**row,'id':'synthetic-2'}],self.fields)
        with self.assertRaises(ValueError): analyze(self.root)
        self.exam(local_path='../escape.txt')
        with self.assertRaises(ValueError): analyze(self.root)
    def test_discontinuous_phrases_are_only_review_candidates(self):
        words=tokens('They gave the idea up.',{'gave':'give'})
        self.assertEqual(phrase_hits(words,'give up'),[(1,4)])
        self.assertEqual(phrase_hits(words,'give up',max_gap=0),[])
    def test_release_gate_fails_for_empty_material_and_never_calls_it_complete(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(audit(self.root)); self.assertFalse(audit(self.root,release=True))
        report=json.loads((self.root/'analysis/release_audit.json').read_text()); self.assertFalse(report['releaseReady']); self.assertEqual(report['remaining']['word'],[800,900,1200,1000])
    def test_reading_validation_checks_evidence_answers_and_exact_syntax_offsets(self):
        options=[{'id':str(i),'text':str(i),'explanation':'synthetic explanation'} for i in range(4)]
        passage={'id':'synthetic-reading','level':1,'format':1,'title':'Fixture','recommendedSeconds':60,'content':{},'paragraphs':[{'id':'p','english':'Birds fly.','translation':'鳥は飛ぶ。'}],'questions':[{'id':str(i),'prompt':'Synthetic?','options':options,'correctOptionId':'0','explanation':'Fixture','evidence':{'paragraphId':'p','quote':'Birds'}} for i in range(3)],'syntax':[{'paragraphId':'p','explanation':'Fixture','spans':[{'id':'s','start':0,'end':5,'text':'Birds','role':'S'},{'id':'v','start':6,'end':9,'text':'fly','role':'V'}],'relations':[{'from':'s','to':'v'}]}]}
        self.assertEqual(validate_reading(passage),[])
        passage['syntax'][0]['spans'][0]['end']=4; self.assertIn('syntax offsets invalid',validate_reading(passage))
        passage['questions'][0]['correctOptionId']='not-real'; self.assertIn('reading options/answer/explanations invalid',validate_reading(passage))
if __name__=='__main__': unittest.main()
