const { createHash, createHmac, timingSafeEqual, randomBytes } = require('node:crypto');
const COOKIE = '__Host-ty-developer';
const TTL = 30 * 24 * 60 * 60;
const hash = value => createHash('sha256').update(value).digest();
const signature = (value, secret) => createHmac('sha256', secret).update('developer-session:' + value).digest('base64url');
function validSession(token, secret) {
  if (typeof token !== 'string' || token.length > 256) return false;
  const parts = token.split('.');
  if (parts.length !== 3 || !/^\d+$/.test(parts[0])) return false;
  const expires = Number(parts[0]);
  if (expires <= Date.now() / 1000 || expires > Date.now() / 1000 + TTL + 60) return false;
  const expected = signature(parts[0] + '.' + parts[1], secret);
  return timingSafeEqual(hash(parts[2]), hash(expected));
}
module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Vary', 'Cookie');
  const reply = (status, enabled, error) => res.status(status).json({ enabled, ...(error ? { error } : {}) });
  const secret = process.env.DEVELOPER_PREMIUM_PASSWORD;
  if (!secret || secret.length < 24) return reply(503, false, '開発者用解除は準備中です。');
  if (req.method === 'GET') {
    const token = (req.headers.cookie || '').split(';').map(x => x.trim()).find(x => x.startsWith(COOKIE + '='))?.slice(COOKIE.length + 1);
    return reply(200, validSession(token, secret));
  }
  if (!['POST', 'DELETE'].includes(req.method)) { res.setHeader('Allow', 'GET, POST, DELETE'); return reply(405, false); }
  let origin;
  try { origin = new URL(req.headers.origin); } catch { return reply(403, false); }
  if (origin.protocol !== 'https:' || origin.host !== req.headers.host) return reply(403, false);
  const cookie = (value, age) => `${COOKIE}=${value}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${age}`;
  if (req.method === 'DELETE') { res.setHeader('Set-Cookie', cookie('', 0)); return reply(200, false); }
  if (!/^application\/json\b/.test(req.headers['content-type'] || '')) return reply(415, false);
  let body = req.body;
  if (typeof body === 'string') { if (body.length > 1024) return reply(413, false); try { body = JSON.parse(body); } catch { return reply(400, false); } }
  const password = body?.password;
  if (typeof password !== 'string' || password.length > 256 || !timingSafeEqual(hash(password), hash(secret))) return reply(401, false);
  const value = `${Math.floor(Date.now() / 1000) + TTL}.${randomBytes(16).toString('base64url')}`;
  res.setHeader('Set-Cookie', cookie(`${value}.${signature(value, secret)}`, TTL));
  return reply(200, true);
};
