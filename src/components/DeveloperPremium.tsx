import React, { useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { revokeDeveloperAccess, unlockDeveloperAccess } from '../developerPremium';

export function DeveloperPremium({ enabled, onChange }: { enabled: boolean; onChange: (value: boolean) => void }) {
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const act = async () => {
    if (pending.current) return;
    pending.current = true; setBusy(true); setMessage('');
    try {
      if (enabled) {
        await revokeDeveloperAccess(); onChange(false); setMessage('開発者用Premium解除を取り消しました。学習記録は保持されます。');
      } else if (await unlockDeveloperAccess(password)) {
        setPassword(''); onChange(true); setMessage('Premium機能を解除しました。');
      } else { setPassword(''); setMessage('パスワードが違います。'); }
    } catch { setMessage('認証サーバーに接続できませんでした。しばらくしてから再試行してください。'); }
    finally { pending.current = false; setBusy(false); }
  };
  return <View style={s.card}>
    <Text style={s.heading}>開発者用Premium解除</Text>
    <Text style={s.text}>{enabled ? '開発者用Premium：有効' : '開発者パスワードを入力するとPremium機能を利用できます。'}</Text>
    <Text style={s.note}>記述式練習・試験、お気に入り、長文の全問題が対象です。解除状態はこのブラウザで30日間維持されます。</Text>
    {!enabled && <TextInput accessibilityLabel="開発者パスワード" placeholder="開発者パスワード" secureTextEntry autoCapitalize="none" autoCorrect={false} value={password} onChangeText={setPassword} maxLength={256} editable={!busy} onSubmitEditing={() => { if (password) void act(); }} style={s.input} />}
    <Pressable accessibilityRole="button" accessibilityState={{ disabled: busy || (!enabled && !password) }} disabled={busy || (!enabled && !password)} onPress={() => void act()} style={[s.button, (busy || (!enabled && !password)) && { opacity: 0.5 }]}><Text style={s.buttonText}>{busy ? '処理中…' : enabled ? '開発者用Premium解除を取り消す' : 'Premium機能を解除する'}</Text></Pressable>
    {!!message && <Text accessibilityLiveRegion="polite" style={s.text}>{message}</Text>}
  </View>;
}
const s = StyleSheet.create({card:{backgroundColor:'#fff',borderRadius:18,padding:22,gap:14,marginVertical:12},heading:{fontSize:20,fontWeight:'700',color:'#122b4a'},text:{fontSize:15,color:'#233d57',lineHeight:24},note:{fontSize:13,color:'#5b6d80',lineHeight:21},input:{borderWidth:1,borderColor:'#a7b8c9',borderRadius:10,padding:14,fontSize:16,color:'#122b4a'},button:{backgroundColor:'#122b4a',padding:15,borderRadius:10,alignItems:'center'},buttonText:{color:'#fff',fontSize:15,fontWeight:'700'}});
