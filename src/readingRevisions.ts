import lower from '../content/readings/enriched.json';
import level3 from '../content/readings/enriched-level3.json';
import level4 from '../content/readings/enriched-level4.json';
import level2Next from '../content/readings/enriched-level2-next5.json';
import level3Next from '../content/readings/enriched-level3-next5.json';
import level4Next from '../content/readings/enriched-level4-next5.json';
// Each immutable overlay retains the source passage and question identities.
export const readingRevisions=[...lower,...level3,...level4,...level2Next,...level3Next,...level4Next];
