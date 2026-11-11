import { test } from 'node:test';
import assert from 'node:assert/strict';
import { PracticeGate } from '../src/practice';
test('practice state machine rejects duplicate answers and bubbled/early advance', () => {
  const gate = new PracticeGate(350);
  assert.equal(gate.answer(), true); assert.equal(gate.answer(), false);
  assert.equal(gate.advance(0), false);
  gate.explain(1000); assert.equal(gate.phase, 'EXPLANATION');
  assert.equal(gate.advance(1000), false); assert.equal(gate.advance(1349), false);
  assert.equal(gate.advance(1350), true); assert.equal(gate.advance(1800), false);
  gate.questionReady(); assert.equal(gate.answer(), true);
  gate.explain(2000); gate.advance(2350); gate.finish(); assert.equal(gate.phase, 'FINISHED'); assert.equal(gate.answer(), false);
});
