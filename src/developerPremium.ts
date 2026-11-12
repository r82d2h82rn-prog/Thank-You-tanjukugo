import AsyncStorage from '@react-native-async-storage/async-storage';

// Local Web beta access only. Production billing must use server entitlements.
export const DEVELOPER_ACCESS_KEY = 'thank-you.developer-premium.v1';
const PASSWORD_DIGEST = '5e75501506682e0dede71e66f455bc63fce8299ac03643c9882d0323c07a1ed5';

async function digest(password: string): Promise<string> {
  if (!globalThis.crypto?.subtle) throw new Error('HTTPS対応のブラウザで利用してください。');
  const bytes = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(password));
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, '0')).join('');
}
export async function loadDeveloperAccess(): Promise<boolean> {
  return (await AsyncStorage.getItem(DEVELOPER_ACCESS_KEY)) === PASSWORD_DIGEST;
}
export async function unlockDeveloperAccess(password: string): Promise<boolean> {
  if (password.length > 256 || await digest(password) !== PASSWORD_DIGEST) return false;
  await AsyncStorage.setItem(DEVELOPER_ACCESS_KEY, PASSWORD_DIGEST);
  return true;
}
export async function revokeDeveloperAccess(): Promise<void> {
  await AsyncStorage.removeItem(DEVELOPER_ACCESS_KEY);
}
