// Native audio adapter is reserved for the Android development phase.
export function playSound(_kind: 'tap' | 'correct' | 'wrong', _enabled: boolean) {}
export function speak(_text: string, _enabled: boolean) {}
export function stopSpeech() {}
