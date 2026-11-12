// Passwords and verifiers are kept only in the server's private environment.
// The browser retains a signed session in a Secure, HttpOnly cookie.
async function request(method: 'GET' | 'POST' | 'DELETE', password?: string): Promise<boolean> {
  const response = await fetch('/api/developer-premium', {
    method, credentials: 'same-origin', cache: 'no-store',
    ...(method === 'POST' ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }) } : {}),
  });
  if (response.status === 401) return false;
  if (!response.ok) throw new Error('開発者認証に接続できません。');
  const result = await response.json();
  return result.enabled === true;
}
export function loadDeveloperAccess(): Promise<boolean> { return request('GET'); }
export function unlockDeveloperAccess(password: string): Promise<boolean> { return request('POST', password); }
export async function revokeDeveloperAccess(): Promise<void> { await request('DELETE'); }
