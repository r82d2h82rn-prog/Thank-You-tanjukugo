import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import sources from '../../content/sources.json';
export function SourceCredits() {
  return <View style={{ gap: 16 }}>
    <Text style={s.heading}>教材の制作・利用条件</Text>
    <Text style={s.text}>現在利用できる150項目は初期試作品の独自検証教材です。正式教材として人による校閲・利用条件の最終確認が済んだものではありません。</Text>
    <Text style={s.text}>NGSL・NAWLなどは調査対象です。ネットワーク接続が拒否されたため、候補データの取得・最新ライセンスの確認・大学入試の頻度分析は未実施です。</Text>
    {sources.map(source => <View key={source.id} style={s.card}>
      <Text style={s.heading}>{source.name}</Text>
      {source.url && <Text selectable style={s.url}>{source.url}</Text>}
      <Text style={s.text}>{source.purpose === 'sample' ? '検証用教材：独自生成・人手レビュー待ち' : '調査候補：製品に未導入'}</Text>
      <Text style={s.small}>確認済みバージョン：{source.observedVersion ?? '未確認'} / 商用利用条件：{source.commercialUse === 'granted' ? '記録あり' : '未確認'}</Text>
      <Text style={s.small}>{source.notes}</Text>
    </View>)}
    <Text style={s.text}>効果音はアプリ内で合成したオリジナル音です。英語発音には端末のWeb Speech機能を使用しています。第三者の発音音源を同梱していません。</Text>
  </View>;
}
const s = StyleSheet.create({ card: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#dfe6ee', borderRadius: 12, padding: 18, gap: 10 }, heading: { color: '#122b4a', fontSize: 18, fontWeight: '700' }, text: { color: '#354e69', fontSize: 15, lineHeight: 26 }, small: { color: '#5a7088', fontSize: 13, lineHeight: 23 }, url: { color: '#316b9f', fontSize: 13, lineHeight: 23 } });
