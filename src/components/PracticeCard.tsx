import React from 'react';
import { GestureResponderEvent, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Entry, Mastery, Mode } from '../model';
export interface Feedback { correct: boolean; response: string; unknown: boolean }
interface Props {
  compact?: boolean; tight?: boolean; entry: Entry; mode: Mode; feedback: Feedback | null; options: string[]; inputs: string[];
  onInput: (index: number, value: string) => void;
  onAnswer: (value: string, unknown?: boolean) => void; onAdvance: () => void;
  onSpeech: () => void; speechEnabled: boolean; onFavorite: () => void; favorite: boolean; premium: boolean; record: Mastery;
}
export function PracticeCard(p: Props) {
  const { entry, mode, feedback, compact = false, tight = false } = p;
  const Control = ({ label, action, disabled = false }: { label: string; action: () => void; disabled?: boolean }) => <Pressable accessibilityRole="button" accessibilityLabel={label} disabled={disabled} onPress={(event: GestureResponderEvent) => { event.stopPropagation(); action(); }} style={[s.control, compact && s.compactControl, disabled && { opacity: 0.4 }]}><Text style={[s.text, compact && s.compactText]}>{label}</Text></Pressable>;
  return <Pressable testID="practice-card" accessibilityRole="button" accessibilityLabel={feedback ? '解説カード' : '問題カード'} onPress={event => { event.stopPropagation(); if (feedback) p.onAdvance(); }} style={[s.card, compact && s.compactCard, tight && s.tightCard, feedback && (feedback.correct ? s.correct : s.wrong)]}>
    {feedback ? <View testID="explanation-content" style={[s.section, compact && s.compactSection, tight && s.tightSection]} accessibilityLiveRegion="polite">
      <Text style={s.heading}>{feedback.unknown ? '？ わからない' : feedback.correct ? '✓ 正解！' : '× 不正解'}</Text>
      <Text style={s.text}>あなたの回答：{feedback.response || '（空欄）'}</Text>
      <Text style={s.answer}>正解：{entry.meaning}</Text>
      <Text style={[s.word, compact && s.compactWord]}>{entry.english}</Text>
      <Text style={[s.muted, compact && s.compactMuted]}>{entry.pos}　/{entry.pronunciation.replace(/^\/|\/$/g, '')}/</Text>
      <View style={s.controls}><Control label="発音を聴く" action={p.onSpeech} disabled={!p.speechEnabled} /><Control label={p.favorite ? '★ お気に入り解除' : '☆ お気に入り登録'} action={p.onFavorite} disabled={!p.premium} /></View>
      <Text style={s.example}>{entry.example}</Text><Text style={s.text}>{entry.translation}</Text><Text style={[s.muted, compact && s.compactMuted]}>{entry.explanation}</Text>
      <Text style={s.text}>{mode === 'choice' ? '選択式' : '記述式'}：連続正解 {p.record.streak}回 · {p.record.mastered ? '✓ 習得済み' : '未習得'}</Text>
      <Text style={s.hint}>画面をタップして次へ</Text>
    </View> : <View testID="question-content" style={[s.section, compact && s.compactSection, tight && s.tightSection]}>
      <Text style={[s.muted, compact && s.compactMuted]}>{mode === 'choice' ? '日本語の意味を選びましょう' : '対応する英語を入力しましょう'}</Text>
      <Text style={[s.word, compact && s.compactWord]}>{mode === 'choice' ? entry.english : entry.meaning}</Text>
      {mode === 'choice' ? <>
        <Text style={[s.muted, compact && s.compactMuted]}>/{entry.pronunciation.replace(/^\/|\/$/g, '')}/ · {p.record.mastered ? '習得済み' : '未習得'}</Text>
        <View style={s.controls}><Control label="発音を聴く" action={p.onSpeech} disabled={!p.speechEnabled} /><Control label={p.favorite ? '★ お気に入り解除' : '☆ お気に入り登録'} action={p.onFavorite} disabled={!p.premium} /></View>
        {p.options.map((option, i) => <Pressable key={option} accessibilityRole="button" accessibilityLabel={option} onPress={event => { event.stopPropagation(); p.onAnswer(option); }} style={[s.option, compact && s.compactOption, tight && s.tightOption]}><Text style={s.letter}>{String.fromCharCode(65 + i)}</Text><Text style={[s.text, compact && s.compactText, { flex: 1 }]}>{option}</Text></Pressable>)}
      </> : <>
        <Text style={[s.muted, compact && s.compactMuted]}>{entry.kind === 'idiom' ? `${entry.english.split(' ').length}語 · 最初の頭文字：${entry.english[0]}` : '英単語を入力してください'}</Text>
        <View style={s.controls}>{Array.from({ length: entry.kind === 'idiom' ? entry.english.split(' ').length : 1 }, (_, i) => <TextInput key={i} accessibilityLabel={`英語の入力 ${i + 1}`} value={p.inputs[i] ?? ''} onChangeText={text => p.onInput(i, text)} autoCapitalize="none" autoCorrect={false} style={s.input} onSubmitEditing={() => p.onAnswer(p.inputs.map(v => v.trim()).join(' '))} />)}</View>
        <Control label="回答する" action={() => p.onAnswer(p.inputs.map(v => v.trim()).join(' '))} disabled={!p.inputs.some(v => v?.trim())} />
      </>}
      <Control label="わからない" action={() => p.onAnswer('', true)} />
    </View>}
  </Pressable>;
}
const s = StyleSheet.create({
  compactCard: { padding: 16, minHeight: 0 }, tightCard: { padding: 12 }, compactSection: { gap: 10 }, tightSection: { gap: 7 },
  compactControl: { paddingVertical: 7, paddingHorizontal: 12, minHeight: 40 }, compactText: { fontSize: 14, lineHeight: 22 }, compactMuted: { fontSize: 12, lineHeight: 20 }, compactWord: { fontSize: 30, lineHeight: 38, marginVertical: 2 },
  compactOption: { paddingVertical: 10, paddingHorizontal: 14, minHeight: 46, gap: 12 }, tightOption: { paddingVertical: 8, minHeight: 44 },
  card: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#d9e3ef', borderRadius: 16, padding: 24, minHeight: 380 }, section: { gap: 16 }, controls: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, control: { borderWidth: 1, borderColor: '#bacbdd', borderRadius: 8, paddingVertical: 12, paddingHorizontal: 16, minHeight: 46, backgroundColor: '#fff', alignItems: 'center' },
  heading: { fontSize: 24, fontWeight: '700', color: '#122b4a' }, word: { fontSize: 34, fontWeight: '800', color: '#122b4a', marginVertical: 8 }, answer: { fontSize: 20, fontWeight: '700', color: '#122b4a' }, text: { fontSize: 16, lineHeight: 26, color: '#122b4a' }, muted: { fontSize: 14, lineHeight: 24, color: '#52677e' }, hint: { fontSize: 13, color: '#52677e', textAlign: 'center', padding: 16 }, example: { fontSize: 20, lineHeight: 31, color: '#122b4a' }, option: { flexDirection: 'row', gap: 16, borderWidth: 1, borderColor: '#d3deea', borderRadius: 10, padding: 16, alignItems: 'center', minHeight: 56 }, letter: { fontSize: 14, color: '#617d9b', fontWeight: '700' }, input: { minWidth: 100, flex: 1, fontSize: 18, padding: 14, borderWidth: 1, borderColor: '#9aafc6', borderRadius: 8, color: '#122b4a', backgroundColor: '#fff' }, correct: { backgroundColor: '#edf7f3', borderColor: '#9fcbbb' }, wrong: { backgroundColor: '#fff2ed', borderColor: '#e2b4a3' }
});
