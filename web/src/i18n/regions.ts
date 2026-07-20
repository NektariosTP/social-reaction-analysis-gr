export interface Region {
  en: string;
  el: string;
  center: [number, number];
}

export const REGIONS: Region[] = [
  { en: "Attica", el: "Αττική", center: [23.7, 38.0] },
  { en: "Central Macedonia", el: "Κεντρική Μακεδονία", center: [23.0, 40.6] },
  { en: "Thessaly", el: "Θεσσαλία", center: [22.4, 39.6] },
  { en: "Epirus", el: "Ήπειρος", center: [20.8, 39.6] },
  { en: "Western Greece", el: "Δυτική Ελλάδα", center: [21.7, 38.2] },
  { en: "Western Macedonia", el: "Δυτική Μακεδονία", center: [21.4, 40.3] },
  { en: "Peloponnese", el: "Πελοπόννησος", center: [22.4, 37.3] },
  { en: "Central Greece", el: "Στερεά Ελλάδα", center: [22.9, 38.7] },
  { en: "East Macedonia and Thrace", el: "Ανατολική Μακεδονία και Θράκη", center: [24.9, 41.1] },
  { en: "Crete", el: "Κρήτη", center: [24.9, 35.3] },
  { en: "North Aegean", el: "Βόρειο Αιγαίο", center: [26.1, 38.9] },
  { en: "South Aegean", el: "Νότιο Αιγαίο", center: [25.4, 36.9] },
  { en: "Ionian Islands", el: "Ιόνια Νησιά", center: [20.7, 39.0] },
];
