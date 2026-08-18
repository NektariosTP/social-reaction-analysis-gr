/**
 * Canonical DB strings for the four-axis classification model (see CLAUDE.md).
 * Keyed by the exact value the API returns, so a raw `action_forms[0]` etc.
 * can be looked up directly without a separate translation-key mapping.
 */

export type Lang = "el" | "en";

interface TaxonomyEntry {
  en: string;
}

interface IntensityEntry extends TaxonomyEntry {
  /** Ordinal level 1-3, used to render the ●●○ dot indicator. */
  level: 1 | 2 | 3;
}

export const ACTION_FORM: Record<string, TaxonomyEntry> = {
  "Διαδήλωση/Πορεία/Συγκέντρωση": { en: "Demonstration / March / Rally" },
  "Απεργία/Στάση εργασίας": { en: "Strike / Work stoppage" },
  "Κατάληψη": { en: "Occupation" },
  "Αποκλεισμός/Μπλόκο": { en: "Blockade" },
  "Μποϊκοτάζ": { en: "Boycott" },
  "Διαδικτυακή εκστρατεία": { en: "Online campaign" },
  Whistleblowing: { en: "Whistleblowing" },
  "Αποχή": { en: "Abstention" },
};

export const THEMATIC_FIELD: Record<string, TaxonomyEntry> = {
  "Εργασιακό": { en: "Labour" },
  "Πολιτικό/Θεσμικό": { en: "Political / Institutional" },
  "Οικονομικό": { en: "Economic" },
  "Περιβαλλοντικό": { en: "Environmental" },
  "Δικαιώματα/Κοινωνικό": { en: "Rights / Social" },
  "Εκπαίδευση": { en: "Education" },
  "Αστυνομική Βία": { en: "Police violence" },
  "Άλλο": { en: "Other" },
};

export const CHANNEL: Record<string, TaxonomyEntry> = {
  "Φυσικό (offline)": { en: "Physical (offline)" },
  "Ψηφιακό (online)": { en: "Digital (online)" },
  "Υβριδικό": { en: "Hybrid" },
};

export const CHANNEL_BORDER_STYLE: Record<string, "solid" | "dashed" | "dotted"> = {
  "Φυσικό (offline)": "solid",
  "Υβριδικό": "dashed",
  "Ψηφιακό (online)": "dotted",
};

export const INTENSITY: Record<string, IntensityEntry> = {
  "Ειρηνική": { en: "Peaceful", level: 1 },
  "Διαταρακτική (μη βίαιη, παρεμποδιστική)": { en: "Disruptive (non-violent, obstructive)", level: 2 },
  "Βίαιη/Συγκρουσιακή": { en: "Violent / Confrontational", level: 3 },
};

const ALL_AXES = [ACTION_FORM, THEMATIC_FIELD, CHANNEL, INTENSITY];

/** Resolve a raw DB taxonomy value to a display label for the given language. */
export function axisLabel(value: string | null | undefined, lang: Lang): string {
  if (!value) return "";
  if (lang === "el") return value;
  for (const axis of ALL_AXES) {
    const entry = axis[value];
    if (entry) return entry.en;
  }
  return value;
}

export function intensityLevel(value: string | null | undefined): 1 | 2 | 3 | null {
  if (!value) return null;
  return INTENSITY[value]?.level ?? null;
}
