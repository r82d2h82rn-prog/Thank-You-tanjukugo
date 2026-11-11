/** A synchronous gate prevents duplicate answer writes and answer-tap bubbling. */
export type PracticePhase = 'QUESTION' | 'ANSWER_PROCESSING' | 'EXPLANATION' | 'NEXT_QUESTION' | 'FINISHED';
export class PracticeGate {
  phase: PracticePhase = 'QUESTION';
  private explanationReadyAt = Infinity;
  constructor(readonly minimumExplanationMs = 350) {}
  questionReady() { this.phase = 'QUESTION'; this.explanationReadyAt = Infinity; }
  answer() { if (this.phase !== 'QUESTION') return false; this.phase = 'ANSWER_PROCESSING'; return true; }
  explain(now = Date.now()) { if (this.phase !== 'ANSWER_PROCESSING') return; this.phase = 'EXPLANATION'; this.explanationReadyAt = now + this.minimumExplanationMs; }
  advance(now = Date.now()) {
    if (this.phase !== 'EXPLANATION' || now < this.explanationReadyAt) return false;
    this.phase = 'NEXT_QUESTION'; return true;
  }
  finish() { this.phase = 'FINISHED'; }
}
