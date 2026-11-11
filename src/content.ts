import { Entry } from './model';
export type QualityStatus = 'draft' | 'auto_checked' | 'review_required' | 'approved' | 'rejected';
export interface ContentMetadata { sourceIds: string[]; contentVersion: number; qualityStatus: QualityStatus; autoChecked: boolean; humanReviewed: boolean; examFrequency: number | null; selectionReason: string; productionApproved: boolean }
export interface SourcePermissions { id: string; commercialUse: string; redistribution: string; licenseEvidence: string | null }
export type ApprovedEntry = Entry & { content: ContentMetadata };
/** Samples remain available until a reviewed entry with the SAME stable ID replaces them. */
export function mergeCatalog(samples: Entry[], approved: ApprovedEntry[], sources: SourcePermissions[]): Entry[] {
  const catalog = new Map(samples.map(e => [e.id, e]));
  for (const entry of approved) {
    if (!entry.content?.productionApproved || entry.content.qualityStatus !== 'approved' || !entry.content.humanReviewed) throw new Error(`正式教材の承認が必要: ${entry.id}`);
    if (!entry.content.sourceIds.length || entry.content.sourceIds.some(id => {
      const source = sources.find(s => s.id === id);
      return source?.commercialUse !== 'granted' || source?.redistribution !== 'granted' || !source?.licenseEvidence;
    })) throw new Error(`出典の利用条件が未確認: ${entry.id}`);
    const old = catalog.get(entry.id);
    if (old && (old.english !== entry.english || old.kind !== entry.kind)) throw new Error(`既存IDの再利用は禁止: ${entry.id}`);
    catalog.set(entry.id, entry);
  }
  return [...catalog.values()].sort((a, b) => a.level - b.level || a.section - b.section || a.number - b.number);
}
