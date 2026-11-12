import React from 'react';
import { Linking, StyleSheet, Text, View } from 'react-native';
import sources from '../../content/sources.json';
import imported from '../../analysis/official_import.json';
import audit from '../../analysis/content_audit.json';
const draftWordCount = audit.draftCounts.word.reduce((total, count) => total + count, 0);
const link = (url: string) => <Text accessibilityRole="link" selectable style={s.url} onPress={() => { void Linking.openURL(url).catch(() => {}); }}>{url}</Text>;
export function SourceCredits() {
  return <View style={{ gap: 16 }}>
    <Text style={s.heading}>教材の制作・利用条件</Text>
    <Text style={s.text}>検証用150項目に加え、ホームから制作済み単語{draftWordCount.toLocaleString()}語を試用できます。追加単語は校閲前の草稿です。正式教材としての承認状態は変更していません。</Text>
    <Text style={s.text}>NGSL・NAWL・TSL・BSLの公式配布版から、重複をまとめて{imported.uniqueOfficialCandidates.toLocaleString()}語の候補を取得しました。候補の取得数は正式な収録数ではありません。独自の単語草稿{draftWordCount}語は校閲待ちです。大学入試の英文頻度は未検証です。</Text>
    <Text style={s.text}>公式語彙リストと、それを小文字化・重複統合した候補一覧はCC BY-SA 4.0の条件に従います。各教材の日本語訳・例文・解説は独自に制作しています。出典元との公式な提携・推薦を示すものではありません。</Text>
    {link('https://creativecommons.org/licenses/by-sa/4.0/')}
    {sources.map(source => <View key={source.id} style={s.card}>
      <Text style={s.heading}>{source.name}</Text>
      {source.url && link(source.url)}
      <Text style={s.text}>{source.purpose === 'pronunciation' ? '発音記号の参照データ・自動変換後の校閲待ち' : source.purpose === 'sample' ? '検証用教材：独自生成・人手レビュー待ち' : source.accessStatus === 'retrieved_license_verified' ? '候補データ取得済み・正式教材の採否は未確定' : source.purpose === 'draft' ? '独自教材の草稿・人手レビュー待ち' : '参考資料・本文は製品に未導入'}</Text>
      <Text style={s.small}>確認済みバージョン：{source.observedVersion ?? '未確認'} / 商用利用条件：{source.commercialUse === 'granted' ? '記録あり' : '未確認'}</Text>
      {source.license && <Text style={s.small}>ライセンス：{source.license}</Text>}
      {source.attribution && <Text selectable style={s.small}>{source.attribution}</Text>}
      {source.shareAlike && <Text style={s.small}>継承条件：{source.shareAlike}。著作者表示・変更の明示・同一ライセンスでの提供が必要です。</Text>}
      <Text style={s.small}>{source.notes}</Text>
    </View>)}
    <Text style={s.text}>効果音はアプリ内で合成したオリジナル音です。英語発音には端末のWeb Speech機能を使用しています。第三者の発音音源を同梱していません。</Text>
  </View>;
}
const s = StyleSheet.create({ card: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dfe6ee', borderRadius: 12, padding: 18, gap: 10 }, heading: { color: '#122b4a', fontSize: 18, fontWeight: '700' }, text: { color: '#354e69', fontSize: 15, lineHeight: 26 }, small: { color: '#5a7088', fontSize: 13, lineHeight: 23 }, url: { color: '#316b9f', fontSize: 13, lineHeight: 23 } });
