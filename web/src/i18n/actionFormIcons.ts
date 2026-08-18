/**
 * One icon glyph per Action Form value (Axis 1), keyed by the exact DB
 * string from ACTION_FORM in taxonomy.ts. Used on map markers, the map
 * legend, and the onboarding overlay's axis chips.
 */
export const ACTION_FORM_ICONS: Record<string, string> = {
  "Διαδήλωση/Πορεία/Συγκέντρωση": "📣",
  "Απεργία/Στάση εργασίας": "✊",
  "Κατάληψη": "🏛",
  "Αποκλεισμός/Μπλόκο": "🚧",
  "Μποϊκοτάζ": "🚫",
  "Διαδικτυακή εκστρατεία": "💻",
  Whistleblowing: "🕵",
  "Αποχή": "✋",
};

export const ACTION_FORM_ICON_FALLBACK = "❔";

/** Icon for an event's primary Action Form — the first entry of its action_forms array. */
export function actionFormIcon(actionForms: string[] | null | undefined): string {
  const primary = actionForms?.[0];
  return (primary && ACTION_FORM_ICONS[primary]) || ACTION_FORM_ICON_FALLBACK;
}
