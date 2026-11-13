# LEVEL 1 through passage 100

Requested target: all 100 saved LEVEL 1 passages. This is a progress checkpoint, not a completion certificate.

- Previously enriched: 1–15.
- First saved batch: 16–20 (`reading-l1-f02-06`–`reading-l1-f02-10`), 71 aligned sentences.
- Second batch: 21–25, 71 sentences including the five inserted answers.
- Third batch: 26–30, 66 sentences; source-preserving paragraph presentation for 29–30.
- Fourth batch: 31–35, 63 sentences; restored 4/3/3/4/3 display paragraphs and 4/5/3/4/5 questions.
- Remaining: 36–100 (65 passages).
- Source passage IDs, English paragraphs and original q1–q3 retained byte-for-byte in the immutable source.
- Version 2 overlays: full sentence translations, authored spans and grammatical explanations; 5/4/5/3/4 questions respectively.
- Answer-filled review text is separate from the original gap exercise; offsets use review text and retain source coordinates.
- Source syntax preserved as `previousSyntax`. Newly authored modifier links are not blindly attached to the first verb in compound sentences.
- Semantic review: AI author check only. Independent human review: pending. Browser/device operation: not verified in this environment.

Next batch: 36–40 (title/theme format). Sentence gaps retain reversible source coordinates (including the marker itself for an inserted answer), rather than zipping arrays of different lengths. 29–30 now have three logical display paragraphs, explicit original coordinates, and displayed evidence remapping. Raw paragraph/question objects remain preserved.

Existing completed LEVEL 2–4 revisions are included unchanged. Original source backup remains untouched.

Validation at the 30-passage checkpoint: 43 TypeScript tests and 16 Python tests passed; TypeScript typecheck passed. Web export and remote save verification recorded separately. No new device/browser claim is made.

35-passage checkpoint: 44 TypeScript tests passed; typecheck and Web export passed. Python suite: 16 tests passed at previous checkpoint (no Python behavior changed). Current batch sentence coverage is 63/63; LEVEL 1 as a whole is not complete. Word distributions use the completed review text, with source word counts preserved separately.
