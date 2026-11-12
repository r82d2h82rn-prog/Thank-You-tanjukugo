import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Entry, Mode, State } from '../model';
import { ExamAnswer, ExamSpec, canTakeExam, consumeDiagnostic, examChoices, examKey, examQuestions, finishExam, gradeExam } from '../exams';
const label = (mode: Mode) => mode === 'choice' ? '選択式' : '記述式';
function Action({ text, onPress, disabled = false }: { text: string; onPress: () => void; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={text} disabled={disabled} onPress={onPress} style={[styles.button, disabled && { opacity: .4 }]}><Text style={styles.buttonText}>{text}</Text></Pressable>;
}
export function ExamActions({ state, entries, spec, premium, onStart, update }: { state: State; entries: Entry[]; spec: ExamSpec; premium: boolean; onStart: (s: ExamSpec) => void; update: React.Dispatch<React.SetStateAction<State>> }) {
  const diagnostic = { ...spec, type: 'diagnostic' as const, mode: 'choice' as const };
  return <View style={styles.panel}>
    {spec.type !== 'level' && !state.exams?.[examKey(diagnostic)]?.diagnosticUsed && <>
      <Text style={styles.heading}>初回診断（1回のみ）</Text><Text style={styles.text}>8択・1問10秒。全問完了時に、正解した単語を選択式の習得済みにします。開始後の中断は受験権を消費します。</Text>
      <Action text="初回診断を受験" disabled={!canTakeExam(state, entries, diagnostic)} onPress={() => onStart(diagnostic)} />
      <Action text="初回診断をスキップ" onPress={() => update(s => consumeDiagnostic(s, diagnostic))} />
      <Text style={styles.text}>戻る場合は診断の機会を維持します。</Text>
    </>}
    <Text style={styles.heading}>{spec.kind === 'word' ? '英単語' : '英熟語'} · {spec.type === 'level' ? 'LEVEL合格試験' : 'セクション合格試験'}</Text>
    <Text style={styles.text}>{spec.type === 'level' ? '同じ形式・教材種別の全セクション合格後に受験できます。' : '受験する形式で、このセクションを全項目習得すると解放されます。'}</Text>
    {(['choice','written'] as Mode[]).map(mode => { const target = { ...spec, mode }; const record = state.exams?.[examKey(target)]; return <View key={mode}>
      <Text style={styles.text}>{label(mode)}：{record?.passed ? '✓ 合格済み' : '未合格'}{record?.best !== undefined ? ` · 最高 ${record.best}点` : ''}</Text>
      <Action text={`${spec.kind === 'word' ? '英単語' : '英熟語'} · ${label(mode)}${spec.type === 'level' ? 'LEVEL' : 'セクション'}試験を受験${mode === 'written' && !premium ? ' 🔒' : ''}`} disabled={!canTakeExam(state, entries, target) || (mode === 'written' && !premium)} onPress={() => onStart(target)} />
    </View>; })}
  </View>;
}
export function ExamScreen({ spec, entries, update, onExit, onQuestion }: { spec: ExamSpec; entries: Entry[]; update: React.Dispatch<React.SetStateAction<State>>; onExit: () => void; onQuestion: () => void }) {
  const [questions] = useState(() => examQuestions(entries, spec));
  const [started, setStarted] = useState(false); const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<ExamAnswer[]>([]); const [inputs, setInputs] = useState<string[]>([]);
  const input = inputs.map(v => v.trim()).join(' ');
  const [remaining, setRemaining] = useState(spec.mode === 'choice' ? 10 : 30);
  const [expired, setExpired] = useState(false); const [done, setDone] = useState(false);
  const deadline = useRef(0), lockedIndex = useRef(-1);
  const current = questions[index]; const seconds = spec.mode === 'choice' ? 10 : 30;
  const options = useMemo(() => current ? examChoices(current, entries) : [], [current, entries]);
  useEffect(() => {
    if (!started || done || !current) return;
    onQuestion();
    deadline.current = Date.now() + seconds * 1000;
    setRemaining(seconds); setExpired(false);
    const timer = setInterval(() => { const left = Math.max(0, Math.ceil((deadline.current - Date.now())/1000)); setRemaining(left); if (left === 0) setExpired(true); },100);
    return () => clearInterval(timer);
  }, [started, index, done, seconds, current]);
  useEffect(() => {
    if (!started || done || typeof window === 'undefined') return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', warn); return () => window.removeEventListener('beforeunload', warn);
  }, [started, done]);
  const submit = (response: string, timeout = false, unknown = false) => {
    if (!started || done || !current || lockedIndex.current === index) return;
    if (!timeout && Date.now() >= deadline.current) { setExpired(true); setRemaining(0); return; }
    lockedIndex.current = index;
    const correct = !timeout && !unknown && (spec.mode === 'choice' ? response === current.meaning : gradeExam(current, response));
    const next = [...answers, { entry: current, correct, response: timeout ? '時間切れ' : unknown ? 'わからない' : response }];
    setAnswers(next); setInputs([]);
    if (next.length === questions.length) {
      update(s => finishExam(s, spec, questions, next)); setDone(true);
    } else setIndex(i => i + 1);
  };
  const score = answers.filter(a => a.correct).length; const passScore = questions.length === 50 ? 48 : 95;
  if (!started) return <View style={styles.panel}><Text style={styles.heading}>{spec.type === 'diagnostic' ? '初回診断' : spec.type === 'level' ? 'LEVEL合格試験' : 'セクション合格試験'}を開始します</Text><Text style={styles.text}>{questions.length}問 · {label(spec.mode)} · 1問{seconds}秒 · 合格{passScore}点以上</Text><Text style={styles.text}>正誤と解説は全問終了後に表示します。途中終了では今回の習得変更は反映されません。初回診断は開始後の中断でも受験権を消費します。</Text><Action text="試験を開始する" onPress={() => { if (spec.type === 'diagnostic') update(s => consumeDiagnostic(s,spec)); setStarted(true); }} /><Action text="開始せず戻る" onPress={onExit} /></View>;
  if (done) return <View style={styles.panel}><Text style={styles.heading}>試験結果：{score} / {questions.length} · {score >= passScore ? '合格' : '不合格'}</Text><Text style={styles.text}>今回の結果を確定しました。過去の合格記録は維持されます。</Text><Action text="学習メニューに戻る" onPress={onExit} />{answers.map((a,i) => <View key={a.entry.id} style={styles.result}><Text style={styles.heading}>{i+1}. {a.correct ? '✓' : '×'} {a.entry.english}</Text><Text style={styles.text}>回答：{a.response || '未入力'} / 正解：{a.entry.meaning}</Text><Text style={styles.text}>{a.entry.example}</Text><Text style={styles.text}>{a.entry.translation}</Text><Text style={styles.text}>{a.entry.explanation}</Text></View>)}</View>;
  return <View style={styles.panel}><Text style={styles.heading}>試験 {index+1} / {questions.length} · 残り {remaining}秒</Text>
    <Text style={styles.word}>{spec.mode === 'choice' ? current.english : current.meaning}</Text>
    {expired ? <><Text style={styles.heading}>時間切れ</Text><Action text="時間切れ：次の問題へ" onPress={() => submit('',true)} /></> : spec.mode === 'choice' ? <>{options.map((option,i) => <Action key={`${index}:${i}`} text={`${i+1}. ${option}`} onPress={() => submit(option)} />)}<Action text="試験：わからない" onPress={() => submit('',false,true)} /></> : <><Text style={styles.text}>{spec.kind === 'idiom' ? `${current.english.split(' ').length}語 · 最初の頭文字：${current.english[0]}` : '英単語を入力してください'}</Text><View style={{flexDirection:'row',flexWrap:'wrap',gap:8}}>{Array.from({length: spec.kind === 'idiom' ? current.english.split(' ').length : 1},(_,i) => <TextInput key={`${index}:${i}`} accessibilityLabel={`試験の英語回答 ${i+1}`} autoCapitalize="none" autoCorrect={false} value={inputs[i] ?? ''} onChangeText={text => setInputs(values => {const copy=[...values];copy[i]=text;return copy;})} onSubmitEditing={() => submit(input)} style={[styles.input,{minWidth:100,flex:1}]} />)}</View><Action text="試験の回答を確定" onPress={() => submit(input)} /><Action text="試験：わからない" onPress={() => submit('',false,true)} /></>}
    <Text style={styles.text}>正誤・解説は全問終了後に表示します。</Text>
    <Action text="試験を中断して戻る（今回の変更は破棄）" onPress={onExit} />
  </View>;
}
const styles = StyleSheet.create({ panel:{gap:14,padding:20,backgroundColor:'#fff',borderRadius:12}, heading:{fontSize:18,lineHeight:28,color:'#122b4a',fontWeight:'700'},text:{fontSize:14,lineHeight:23,color:'#61748b'},word:{fontSize:30,color:'#122b4a',fontWeight:'700'},button:{padding:14,backgroundColor:'#122b4a',borderRadius:8,marginVertical:4},buttonText:{fontSize:14,lineHeight:22,color:'#fff'},input:{padding:14,borderWidth:1,borderColor:'#61748b',fontSize:18},result:{paddingVertical:15,borderTopWidth:1,borderTopColor:'#dfe6ee',gap:8} });
