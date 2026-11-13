# LEVEL 1 through passage 100

Requested target: all 100 saved LEVEL 1 passages. This is a progress checkpoint, not a completion certificate.

- Previously enriched: 1–15.
- First saved batch: 16–20 (`reading-l1-f02-06`–`reading-l1-f02-10`), 71 aligned sentences.
- Second batch: 21–25, 71 sentences including the five inserted answers.
- Third batch: 26–30, 66 sentences; source-preserving paragraph presentation for 29–30.
- Fourth batch: 31–35, 63 sentences; restored 4/3/3/4/3 display paragraphs and 4/5/3/4/5 questions.
- Fifth batch: 36–40, 58 sentences; restored 3/4/3/3/4 display paragraphs and 4/3/5/4/5 questions.
- Remaining: 41–100 (60 passages).
- Source passage IDs, English paragraphs and original q1–q3 retained byte-for-byte in the immutable source.
- Version 2 overlays: full sentence translations, authored spans and grammatical explanations; 5/4/5/3/4 questions respectively.
- Answer-filled review text is separate from the original gap exercise; offsets use review text and retain source coordinates.
- Source syntax preserved as `previousSyntax`. Newly authored modifier links are not blindly attached to the first verb in compound sentences.
- Semantic review: AI author check only. Independent human review: pending. Browser/device operation: not verified in this environment.

Next batch: 41–45 (reference/pronoun format). Sentence gaps retain reversible source coordinates (including the marker itself for an inserted answer), rather than zipping arrays of different lengths. 29–30 now have three logical display paragraphs, explicit original coordinates, and displayed evidence remapping. Raw paragraph/question objects remain preserved.

Existing completed LEVEL 2–4 revisions are included unchanged. Original source backup remains untouched.

Validation at the 30-passage checkpoint: 43 TypeScript tests and 16 Python tests passed; TypeScript typecheck passed. Web export and remote save verification recorded separately. No new device/browser claim is made.

35-passage checkpoint: 44 TypeScript tests passed; typecheck and Web export passed. Python suite: 16 tests passed at previous checkpoint (no Python behavior changed). Current batch sentence coverage is 63/63; LEVEL 1 as a whole is not complete. Word distributions use the completed review text, with source word counts preserved separately.

Corrections before production: the participles in “Her favorite showed three friends laughing beside a river” and “Another showed workers filling part of it with earth” now link to their object referents. Previous drafts backed by immutable GitHub commits 22e11a7ae9b5295358c2b806e57d10fc96c53eb7 (21–25) and 22f392b3240c5e3f08cf98e0136f97e046853cb6 (31–35); text/questions/offsets unchanged.

40-passage checkpoint: 46 TypeScript tests passed. All 100 IDs are listed in analysis/level1-through-100-status.json; 1–40 complete at sentence level, 41–100 not enriched. This does not certify formal human review or screen operation.
