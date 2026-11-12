import React from 'react';
import { Linking, StyleSheet, Text, View } from 'react-native';
import sources from '../../content/sources.json';
import audit from '../../analysis/content_audit.json';
const draftWordCount = audit.draftCounts.word.reduce((total, count) => total + count, 0);
const idiomCount = audit.structurallyCheckedCounts.idiom;
const draftReadingCount = audit.draftCounts.reading.reduce((total, count) => total + count, 0);
const link = (url: string) => <Text accessibilityRole="link" selectable style={s.url} onPress={() => { void Linking.openURL(url).catch(() => {}); }}>{url}</Text>;
export function SourceCredits() {
  return <View style={{ gap: 16 }}>
    <Text style={s.heading}>教材と利用条件</Text>
    <Text style={s.text}>英単語{draftWordCount.toLocaleString()}語・英熟語{idiomCount.toLocaleString()}個・長文{draftReadingCount}題を収録しています。日本語訳・例文・解説は本プロジェクトで独自に執筆しています。</Text>
    <Text style={s.text}>公式語彙リストと、それを小文字化・重複統合した候補一覧はCC BY-SA 4.0の条件に従います。各教材の日本語訳・例文・解説は独自に制作しています。出典元との公式な提携・推薦を示すものではありません。</Text>
    {link('https://creativecommons.org/licenses/by-sa/4.0/')}
    {sources.filter(source => source.license && !source.id.startsWith('original-')).map(source => <View key={source.id} style={s.card}>
      <Text style={s.heading}>{source.name}</Text>
      {source.url && link(source.url)}
      <Text style={s.text}>{source.purpose === 'pronunciation' ? '英語の発音記号の参照データとして使用しています。' : '語彙リスト・参考資料。日本語訳・例文・解説の転載はしていません。'}</Text>
      <Text style={s.small}>バージョン：{source.observedVersion ?? '記載なし'}</Text>
      {source.license && <Text style={s.small}>ライセンス：{source.license}</Text>}
      {source.attribution && <Text selectable style={s.small}>{source.attribution}</Text>}
      {source.shareAlike && <Text style={s.small}>継承条件：{source.shareAlike}。著作者表示・変更の明示・同一ライセンスでの提供が必要です。</Text>}
      {source.purpose === 'pronunciation' && source.notes.includes('Copyright') ? <Text selectable style={s.small}>{source.notes.slice(source.notes.indexOf('Copyright'))}</Text> : <Text style={s.small}>語彙リストの候補データでは、小文字化・Unicode正規化・重複統合を行っています。</Text>}
    </View>)}
    <Text style={s.text}>効果音はアプリ内で合成したオリジナル音です。英語発音には端末のWeb Speech機能を使用しています。第三者の発音音源を同梱していません。</Text>
  </View>;
}
const s = StyleSheet.create({ card: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dfe6ee', borderRadius: 12, padding: 18, gap: 10 }, heading: { color: '#122b4a', fontSize: 18, fontWeight: '700' }, text: { color: '#354e69', fontSize: 15, lineHeight: 26 }, small: { color: '#5a7088', fontSize: 13, lineHeight: 23 }, url: { color: '#316b9f', fontSize: 13, lineHeight: 23 } });
