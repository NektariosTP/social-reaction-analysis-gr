/** Shapes for wireframe blocks with no backing API field yet — components
 * render these when passed, and a ComingSoonBlock placeholder when not. */

export interface PoliticianQuoteData {
  handle: string;
  platform: string;
  timestampIso: string;
  quote: string;
}

export interface TrendingHashtag {
  tag: string;
  mentions: number;
}

export interface PetitionData {
  signatures: number;
  target: number;
}
