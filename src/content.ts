import { Entry } from './model';
export type QualityStatus = 'draft' | 'auto_checked' | 'review_required' | 'approved' | 'rejected';
export interface ContentMetadata { sourceIds: string[]; contentVersion: number; qualityStatus: QualityStatus; autoChecked: boolean; humanReviewed: boolean; examFrequency: number | null; selectionReason: string; productionApproved: boolean }
export interface SourcePermissions { id: string; commercialUse: string; redistribution: string; licenseEvidence: string | null }
export type ApprovedEntry = Entry & { content: ContentMetadata };
const scopeKey = (entry: Entry) => `${entry.kind}:${entry.level}:${entry.section}`;
/** Complete approved sections replace samples; their historical IDs remain in storage. */
export function mergeCatalog(samples: Entry[], approved: ApprovedEntry[], sources: SourcePermissions[]): Entry[] {
  const previous = new Map(samples.map(e => [e.id, e]));
  const approvedIds = new Set<string>();
  const sections = new Map<string, ApprovedEntry[]>();
  for (const entry of approved) {
    if (!entry.content?.productionApproved || entry.content.qualityStatus !== 'approved' || !entry.content.humanReviewed || !entry.content.autoChecked) throw new Error(`正式教材の承認が必要: ${entry.id}`);
    if (!entry.content.sourceIds.length || entry.content.sourceIds.some(id => {
      const source = sources.find(s => s.id === id);
      return source?.commercialUse !== 'granted' || source?.redistribution !== 'granted' || !source?.licenseEvidence;
    })) throw new Error(`出典の利用条件が未確認: ${entry.id}`);
    if (approvedIds.has(entry.id)) throw new Error(`正式教材IDの重複: ${entry.id}`);
    approvedIds.add(entry.id);
    // Check original identity even when the old section will leave the active catalog.
    const old = previous.get(entry.id);
    if (old && (old.english !== entry.english || old.kind !== entry.kind)) throw new Error(`既存IDの再利用は禁止: ${entry.id}`);
    const key = scopeKey(entry);
    sections.set(key, [...(sections.get(key) ?? []), entry]);
  }
  const replaced = new Set<string>();
  for (const [key, section] of sections) {
    const size = section[0].kind === 'word' ? 100 : 50;
    const numbers = new Set(section.map(e => e.number));
    if (numbers.size !== section.length || section.some(e => !Number.isInteger(e.number) || e.number < 1 || e.number > size)) throw new Error(`SECTION番号の不備: ${key}`);
    if (section.length === size) replaced.add(key);
    else if (section.some(e => {
      const old = previous.get(e.id);
      return !old || scopeKey(old) !== key || old.number !== e.number;
    })) throw new Error(`SECTION全体の承認が必要: ${key}`);
  }
  const catalog = new Map(samples.filter(e => !replaced.has(scopeKey(e))).map(e => [e.id, e]));
  for (const entry of approved) catalog.set(entry.id, entry);
  const result = [...catalog.values()];
  const labels = new Set<string>();
  for (const entry of result) {
    const label = `${entry.kind}:${entry.english.trim().toLowerCase()}`;
    if (labels.has(label)) throw new Error(`教材見出しの重複: ${entry.english}`);
    labels.add(label);
  }
  return result.sort((a, b) => a.level - b.level || a.section - b.section || a.number - b.number);
}
