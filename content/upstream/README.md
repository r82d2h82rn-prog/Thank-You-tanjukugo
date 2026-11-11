# Official vocabulary distributions and attribution

Retrieved 2026-11-12 (JST) from links on the New General Service List Project's official pages. The files are retained byte-for-byte; `manifest.json` records their resolved URLs, SHA256 digests, encodings, versions, and observed row counts. They are research inputs, not approved app lessons.

| Source | Authors credited on the official page | Official page | Rows read | Rank |
|---|---|---|---:|---|
| NGSL 1.2 | Browne, C., Culligan, B., and Phillips, J. | https://www.newgeneralservicelist.com/new-general-service-list | 2,809 | SFI Rank |
| NAWL 1.2 | Browne, C., Culligan, B., and Phillips, J. | https://www.newgeneralservicelist.com/new-academic-word-list | 957 | Not obtained |
| TSL 1.2 | Browne, C. and Culligan, B. | https://www.newgeneralservicelist.com/toeic-service-list | 1,250 | TSL Rank |
| BSL 1.2 | Browne, C. and Culligan, B. | https://www.newgeneralservicelist.com/business-service-list | 1,744 | BSL Rank |

These word lists are licensed by their credited authors under **Creative Commons Attribution-ShareAlike 4.0 International**: https://creativecommons.org/licenses/by-sa/4.0/ . Commercial reuse is allowed subject to the license. Preserve the attribution and license link, identify changes, license adaptations under CC BY-SA 4.0, and do not impose additional restrictions on licensed material. The licensors do not endorse this project.

`*-normalized.csv` and `../word_candidates.csv` adapt and combine these lists. Changes include header selection, case and Unicode normalization, source tracking, removal of descriptive preambles, and duplicate consolidation. These derived candidate lists and the project contributions within them are provided under CC BY-SA 4.0. This notice does not assign a blanket license to the software or declare that every independently authored lesson is an adaptation. The scope of share-alike for a commercial packaged lesson collection remains a release-review item; no approved lessons have been published.

Important differences: BSL's page describes 1,700 words but its linked statistics CSV has 1,744 nonempty unique headwords. We retain the measured count rather than deleting 44 rows. NAWL's statistics link led to a learning dictionary, so the alphabetized text distribution was used instead; alphabetical positions are not frequency ranks. TSL's file requires Windows-1252 decoding for words including résumé, café, and entrée. Decoding errors are not silently replaced.

Do not remove or truncate these files to make the candidate counts match the final lesson quotas. The final 3,900-word selection is a separate editorial task.
