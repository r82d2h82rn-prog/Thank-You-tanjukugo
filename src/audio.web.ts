let context: AudioContext | undefined;
let lastTap = 0;
let active: OscillatorNode[] = [];
export function playSound(kind: 'tap' | 'correct' | 'wrong', enabled: boolean) {
  if (!enabled) return;
  if (kind === 'tap' && Date.now() - lastTap < 90) return;
  lastTap = Date.now();
  try {
    context ??= new AudioContext();
    void context.resume().catch(() => {});
    active.forEach(o => { try { o.stop(); } catch {} }); active = [];
    const notes = kind === 'correct' ? [660, 880] : kind === 'wrong' ? [220, 174] : [900];
    const duration = kind === 'tap' ? 0.035 : 0.13;
    notes.forEach((frequency, index) => {
      const oscillator = context!.createOscillator(); const gain = context!.createGain();
      const start = context!.currentTime + index * duration;
      oscillator.frequency.value = frequency; oscillator.type = 'sine';
      gain.gain.setValueAtTime(0, start); gain.gain.linearRampToValueAtTime(0.055, start + 0.005); gain.gain.exponentialRampToValueAtTime(0.001, start + duration);
      oscillator.connect(gain); gain.connect(context!.destination); oscillator.start(start); oscillator.stop(start + duration); active.push(oscillator);
    });
  } catch { /* Audio availability must not block study. */ }
}
export function speak(text: string, enabled: boolean) {
  if (!enabled || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel(); const speech = new SpeechSynthesisUtterance(text); speech.lang = 'en-US'; speech.rate = 0.85; window.speechSynthesis.speak(speech);
}
export function stopSpeech() { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); }
