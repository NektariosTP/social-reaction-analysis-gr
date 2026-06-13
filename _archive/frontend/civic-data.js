/**
 * civic-data.js — Curated static dataset of Greek civic infrastructure.
 *
 * Each record: { name, nameEl?, lat, lon, address?, url? }
 * Coordinates are approximate (±200 m).
 */

"use strict";

const CIVIC_DATA = {

    // ── Solidarity Networks ─────────────────────────────────────
    solidarity: [
        {
            name: "Network of Social Solidarity & Assistance",
            nameEl: "Δίκτυο Κοινωνικής Αλληλεγγύης & Αρωγής",
            lat: 40.6351, lon: 22.9367,
            address: "Pl. Morichovou 1, Thessaloniki 546 25",
            url: "https://dkaa.gr/",
        },
        {
            name: "Solidarity Network of Pangrati",
            nameEl: "Δίκτυο Αλληλεγγύης Παγκρατίου",
            lat: 37.9675, lon: 23.7531,
            address: "Kononos 57-61, Athina 116 33",
            url: "https://dialpa.org/",
        },
        {
            name: "Local Exchange and Solidarity Network of Magnesia",
            nameEl: "Τοπικό Δίκτυο Ανταλλαγών και Αλληλεγγύης Μαγνησίας",
            lat: 39.3638, lon: 22.9459,
            address: "Korai 90, Volos 383 33",
            url: "www.tem-magnisia.gr/el",
        },
        {
            name: "Solidarity Network of Vyronas",
            nameEl: "Δίκτυο Αλληλεγγύης Βύρωνα",
            lat: 37.9601, lon: 23.7594,
            address: "Pindou 6, Vironas 162 31",
            url: "https://www.facebook.com/groups/540571455960378/?locale=el_GR",
        },
        {
            name: "Lesvos Solidarity",
            nameEl: "Αλληλεγύη Λέσβου",
            lat: 39.1115, lon: 26.5563,
            address: "Agioritou Panselinou 1, Mitilini 811 00",
            url: "https://lesol.gr/",
        },
        {
            name: "Network for Children's Rights",
            nameEl: "Δίκτυο για τα Δικαιώµατα του Παιδιού",
            lat: 37.9914, lon: 23.7242,
            address: "Alkamenous 11 B, Athina 104 39",
            url: "https://ddp.gr/",
        },
        {
            name: "Solidarity Network of Agia Paraskevi",
            nameEl: "Δίκτυο Αλληλεγγύης Αγίας Παρασκευής",
            lat: 38.0136, lon: 23.8302,
            address: "Mesogion 452, Ag. Paraskevi 153 42",
            url: "https://santasolidarity.gr/",
        },
        {
            name: "Solidarity Network of Zografou",
            nameEl: "Δίκτυο Αλληλεγγύης Ζωγράφου",
            lat: 37.9787, lon: 23.7659,
            address: "Xirogianni 15, Zografou 157 71",
            url: "https://diktioaz.blogspot.com/",
        },
        {
            name: "ARSIS – Association for the Social Support of Youth",
            nameEl: "ΑΡΣΙΣ - Κοινωνική Οργάνωση Υποστήριξης Νέων",
            lat: 37.9953, lon: 23.7331,
            address: "Mavrommateon 43, Athina 104 34",
            url: "http://www.arsis.gr/",
        },
        {
            name: "ARSIS – Association for the Social Support of Youth",
            nameEl: "ΑΡΣΙΣ - Κοινωνική Οργάνωση Υποστήριξης Νέων",
            lat: 40.6386, lon: 22.9382,
            address: "Leontos Sofou 26, Thessaloniki 546 25",
            url: "http://www.arsis.gr/",
        },
        {
            name: "ARSIS – Association for the Social Support of Youth",
            nameEl: "ΑΡΣΙΣ - Κοινωνική Οργάνωση Υποστήριξης Νέων",
            lat: 39.6607, lon: 20.8512,
            address: "Leof. Dodonis 10, Ioannina 453 32",
            url: "http://www.arsis.gr/",
        },
        {
            name: "ARSIS – Association for the Social Support of Youth",
            nameEl: "ΑΡΣΙΣ - Κοινωνική Οργάνωση Υποστήριξης Νέων",
            lat: 40.3019, lon: 21.7931,
            address: "Agiou Christoforou 6, Kozani 501 32",
            url: "http://www.arsis.gr/",
        },
    ],

    // ── Social Clinics ──────────────────────────────────────────
    clinics: [
        {
            name: "Metropolitan Community Clinic at Helliniko (MKIKE)",
            nameEl: "Μητροπολιτικό Κοινωνικό Ιατρείο Ελληνικού",
            lat: 37.8981, lon: 23.7452,
            address: "Helliniko, South Athens",
            url: "https://mkike.gr",
        },
        {
            name: "Social Solidarity Medical Center of Penteli",
            nameEl: "Κοινωνικό Ιατρείο Αλληλεγγύης Πεντέλης",
            lat: 38.0403, lon: 23.8635,
            address: "Penteli, Attica",
        },
        {
            name: "Social Clinic of Athens (Kypseli)",
            nameEl: "Κοινωνικό Ιατρείο Αθήνας",
            lat: 37.9929, lon: 23.7401,
            address: "Kypseli, Athens",
        },
        {
            name: "Social Pharmacy Thessaloniki",
            nameEl: "Κοινωνικό Φαρμακείο Θεσσαλονίκης",
            lat: 40.6401, lon: 22.9444,
            address: "Thessaloniki",
        },
        {
            name: "Social Clinic of Patras",
            nameEl: "Κοινωνικό Ιατρείο Πάτρας",
            lat: 38.2452, lon: 21.7344,
            address: "Patras",
        },
        {
            name: "Social Clinic of Heraklion",
            nameEl: "Κοινωνικό Ιατρείο Ηρακλείου",
            lat: 35.3391, lon: 25.1438,
            address: "Heraklion, Crete",
        },
        {
            name: "Social Clinic of Ioannina",
            nameEl: "Κοινωνικό Ιατρείο Ιωαννίνων",
            lat: 39.6648, lon: 20.8540,
            address: "Ioannina",
        },
        {
            name: "Social Clinic of Volos",
            nameEl: "Κοινωνικό Ιατρείο Βόλου",
            lat: 39.3620, lon: 22.9404,
            address: "Volos",
        },
    ],

    // ── Community Kitchens ──────────────────────────────────────
    kitchens: [
        {
            name: "Apostoli Community Kitchen",
            nameEl: "Κοινωνική Κουζίνα Αποστολή",
            lat: 37.9814, lon: 23.7245,
            address: "Athens",
            url: "https://apostoli.edu.gr",
        },
        {
            name: "Boroume Food Rescue Hub",
            nameEl: "Boroume – Δράσεις Κατά της Σπατάλης Τροφίμων",
            lat: 37.9843, lon: 23.7372,
            address: "Charilaou Trikoupi 12, Athens",
            url: "https://boroume.gr",
        },
        {
            name: "Athens Municipality Community Pantry",
            nameEl: "Κοινωνικό Παντοπωλείο Δήμου Αθηναίων",
            lat: 37.9826, lon: 23.7256,
            address: "Athens",
        },
        {
            name: "Thessaloniki Municipality Community Kitchen",
            nameEl: "Κοινωνική Κουζίνα Δήμου Θεσσαλονίκης",
            lat: 40.6370, lon: 22.9452,
            address: "Thessaloniki",
        },
        {
            name: "Church of Greece Community Kitchen – Athens",
            nameEl: "Κοινωνική Κουζίνα Εκκλησίας Ελλάδος – Αθήνα",
            lat: 37.9780, lon: 23.7285,
            address: "Athens",
        },
        {
            name: "Community Kitchen Patras",
            nameEl: "Κοινωνική Κουζίνα Πάτρας",
            lat: 38.2450, lon: 21.7340,
            address: "Patras",
        },
        {
            name: "Community Kitchen Larissa",
            nameEl: "Κοινωνική Κουζίνα Λάρισας",
            lat: 39.6389, lon: 22.4175,
            address: "Larissa",
        },
    ],

    // ── Post-Disaster Help Centers ──────────────────────────────
    disaster: [
        {
            name: "Greek Red Cross – Athens HQ",
            nameEl: "Ελληνικός Ερυθρός Σταυρός – Αθήνα",
            lat: 37.9767, lon: 23.7333,
            address: "Lykourgou 1, Athens",
            url: "https://redcross.gr",
        },
        {
            name: "Greek Red Cross – Thessaloniki Branch",
            nameEl: "Ελληνικός Ερυθρός Σταυρός – Θεσσαλονίκη",
            lat: 40.6399, lon: 22.9428,
            address: "Thessaloniki",
            url: "https://redcross.gr",
        },
        {
            name: "Greek Red Cross – Patras Branch",
            nameEl: "Ελληνικός Ερυθρός Σταυρός – Πάτρα",
            lat: 38.2455, lon: 21.7350,
            address: "Patras",
            url: "https://redcross.gr",
        },
        {
            name: "Greek Red Cross – Heraklion Branch",
            nameEl: "Ελληνικός Ερυθρός Σταυρός – Ηράκλειο",
            lat: 35.3388, lon: 25.1442,
            address: "Heraklion, Crete",
            url: "https://redcross.gr",
        },
        {
            name: "Civil Protection Attica Region",
            nameEl: "Πολιτική Προστασία Περιφέρειας Αττικής",
            lat: 37.9938, lon: 23.7540,
            address: "Athens",
            url: "https://civilprotection.gr",
        },
        {
            name: "Civil Protection Central Macedonia",
            nameEl: "Πολιτική Προστασία Κεντρικής Μακεδονίας",
            lat: 40.6417, lon: 22.9438,
            address: "Thessaloniki",
            url: "https://civilprotection.gr",
        },
        {
            name: "ARSIS Emergency Shelter – Athens",
            nameEl: "Arsis – Κέντρο Έκτακτης Ανάγκης Αθήνας",
            lat: 37.9820, lon: 23.7295,
            address: "Athens",
            url: "https://arsis.gr",
        },
    ],

    // ── Volunteering Programs ───────────────────────────────────
    volunteering: [
        {
            name: "ActionAid Greece",
            nameEl: "ActionAid Ελλάδας",
            lat: 37.9851, lon: 23.7388,
            address: "Mavromichali 23, Athens",
            url: "https://actionaid.gr",
        },
        {
            name: "Metadrasi – Action for Migration and Development",
            nameEl: "Μετάδραση",
            lat: 37.9852, lon: 23.7264,
            address: "Athens",
            url: "https://metadrasi.org",
        },
        {
            name: "Arsis – Social Organization for Youth",
            nameEl: "Αρσις – Κοινωνική Οργάνωση Υποστήριξης Νέων",
            lat: 40.6359, lon: 22.9380,
            address: "Lagkada 26, Thessaloniki",
            url: "https://arsis.gr",
        },
        {
            name: "SOS Children's Villages Greece",
            nameEl: "SOS Χωριά Παιδιών Ελλάδας",
            lat: 37.9906, lon: 23.7426,
            address: "Athens",
            url: "https://sos-villages.gr",
        },
        {
            name: "Boroume",
            nameEl: "Μπορούμε",
            lat: 37.9843, lon: 23.7372,
            address: "Charilaou Trikoupi 12, Athens",
            url: "https://boroume.gr",
        },
        {
            name: "WWF Greece",
            lat: 37.9765, lon: 23.7303,
            address: "Filellinon 26, Athens",
            url: "https://wwf.gr",
        },
        {
            name: "Praksis",
            nameEl: "Πράξις",
            lat: 37.9798, lon: 23.7270,
            address: "Athens",
            url: "https://praksis.gr",
        },
        {
            name: "Médecins du Monde Greece",
            nameEl: "Γιατροί του Κόσμου Ελλάδας",
            lat: 37.9841, lon: 23.7285,
            address: "Athens",
            url: "https://mdmgreece.gr",
        },
        {
            name: "MSF Greece (Médecins Sans Frontières)",
            nameEl: "Γιατροί Χωρίς Σύνορα Ελλάδα",
            lat: 37.9812, lon: 23.7303,
            address: "Athens",
            url: "https://msf.org",
        },
    ],

    // ── Rehab Centers (Κέντρα Απεξάρτησης) ─────────────────────
    rehab: [
        {
            name: "KETHEA – Centre for the Treatment of Dependent Individuals (HQ)",
            nameEl: "ΚΕΘΕΑ – Κέντρο Θεραπείας Εξαρτημένων Ατόμων",
            lat: 37.9656, lon: 23.7444,
            address: "Sorvolou 24, Mets 116 36, Athens",
            url: "https://kethea.gr",
        },
        {
            name: "KETHEA ITHAKI – Athens",
            nameEl: "ΚΕΘΕΑ ΙΘΑΚΗ",
            lat: 37.9887, lon: 23.7337,
            address: "Athens",
            url: "https://kethea.gr",
        },
        {
            name: "KETHEA STROFI – Athens",
            nameEl: "ΚΕΘΕΑ ΣΤΡΟΦΗ",
            lat: 37.9735, lon: 23.7282,
            address: "Athens",
            url: "https://kethea.gr",
        },
        {
            name: "KETHEA NOSTOS – Thessaloniki",
            nameEl: "ΚΕΘΕΑ ΝΟΣΤΟΣ Θεσσαλονίκης",
            lat: 40.6510, lon: 22.9095,
            address: "Thessaloniki",
            url: "https://kethea.gr",
        },
        {
            name: "KETHEA EXODOS – Patras",
            nameEl: "ΚΕΘΕΑ ΕΞΟΔΟΣ Πάτρας",
            lat: 38.2461, lon: 21.7353,
            address: "Patras",
            url: "https://kethea.gr",
        },
        {
            name: "KETHEA DIAVASI – Heraklion",
            nameEl: "ΚΕΘΕΑ ΔΙΑΒΑΣΗ Ηρακλείου",
            lat: 35.3394, lon: 25.1444,
            address: "Heraklion, Crete",
            url: "https://kethea.gr",
        },
        {
            name: "KETHEA – Ioannina",
            nameEl: "ΚΕΘΕΑ Ιωαννίνων",
            lat: 39.6651, lon: 20.8535,
            address: "Ioannina",
            url: "https://kethea.gr",
        },
        {
            name: "OKANA – Organisation Against Drugs (HQ)",
            nameEl: "ΟΚΑΝΑ – Οργανισμός κατά των Ναρκωτικών",
            lat: 37.9780, lon: 23.7238,
            address: "Avramioti 2, 105 52 Athens",
            url: "https://okana.gr",
        },
        {
            name: "OKANA Addiction Treatment Unit – Thessaloniki",
            nameEl: "ΟΚΑΝΑ – Μονάδα Θεσσαλονίκης",
            lat: 40.6417, lon: 22.9436,
            address: "Thessaloniki",
            url: "https://okana.gr",
        },
        {
            name: "OKANA Addiction Treatment Unit – Patras",
            nameEl: "ΟΚΑΝΑ – Μονάδα Πάτρας",
            lat: 38.2455, lon: 21.7342,
            address: "Patras",
            url: "https://okana.gr",
        },
        {
            name: "18 ANO – Psychiatric Addiction Clinic",
            nameEl: "18 ΑΝΩ – Μονάδα Απεξάρτησης",
            lat: 37.9839, lon: 23.6878,
            address: "Psychiatric Hospital of Attica, Haidari, Athens",
            url: "https://18ano.gr",
        },
        {
            name: "Psychiatric Clinic of Thessaloniki – Addiction Unit",
            nameEl: "Ψυχιατρική Κλινική Θεσσαλονίκης – Μονάδα Εξαρτήσεων",
            lat: 40.6380, lon: 22.9310,
            address: "Thessaloniki",
        },
    ],
};
