"""Four-axis label constants — single source of truth for classification + admin."""
from __future__ import annotations

AXIS_ACTION_FORMS = [
    "Διαδήλωση/Πορεία/Συγκέντρωση",
    "Απεργία/Στάση εργασίας",
    "Κατάληψη",
    "Αποκλεισμός/Μπλόκο",
    "Μποϊκοτάζ",
    "Διαδικτυακή εκστρατεία",
    "Whistleblowing",
    "Αποχή",
]

AXIS_THEMATIC_FIELDS = [
    "Εργασιακό",
    "Πολιτικό/Θεσμικό",
    "Οικονομικό",
    "Περιβαλλοντικό",
    "Δικαιώματα/Κοινωνικό",
    "Εκπαίδευση",
    "Αστυνομική Βία",
    "Άλλο",
]

AXIS_CHANNEL = ["Φυσικό (offline)", "Ψηφιακό (online)", "Υβριδικό"]

AXIS_INTENSITY = [
    "Ειρηνική",
    "Διαταρακτική",
    "Βίαιη/Συγκρουσιακή",
]
