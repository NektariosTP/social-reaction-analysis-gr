/**
 * app.js — Social Reaction Analysis GR · Frontend v2
 *
 * Complete dashboard with Leaflet map, category legend, civic response
 * layer, breaking news ticker, draggable panels, and multi-view dashboard.
 */

"use strict";

// ═══════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════
const CONFIG = {
    API_BASE: localStorage.getItem("sra_api") || "http://localhost:8000",
    GITHUB_REPO: "nektariostp/social-reaction-analysis-gr",
    GREECE_CENTER: [38.5, 23.8],
    GREECE_ZOOM: 6,
};

// ═══════════════════════════════════════════════════════════════
// Category definitions
// ═══════════════════════════════════════════════════════════════
const CATEGORY_COLORS = {
    "Mass Mobilization & Street Actions": "#e74c3c",
    "Labor & Economic Reaction":          "#f39c12",
    "Institutional & Political Behavior": "#3498db",
    "Digital Reaction":                   "#9b59b6",
    "Conflict Reaction":                  "#c0392b",
    "Unknown":                            "#95a5a6",
    "None of the above":                  "#7f8c8d",
    "None":                               "#7f8c8d",
};

const CATEGORY_INFO = {
    "Mass Mobilization & Street Actions": {
        icon: "✊",
        description: "Protests, demonstrations, rallies, sit-ins, marches, and other forms of collective public action in physical spaces. This category captures the visible, on-the-ground expressions of social discontent or solidarity.",
    },
    "Labor & Economic Reaction": {
        icon: "⚒️",
        description: "Strikes, work stoppages, economic boycotts, wage disputes, labor union actions, and other economic-driven collective responses. Tracks reactions rooted in employment, wages, and economic conditions.",
    },
    "Institutional & Political Behavior": {
        icon: "🏛️",
        description: "Legislative actions, political party responses, government policy changes, judicial decisions, and formal institutional reactions. Captures how the political system responds to or drives social dynamics.",
    },
    "Digital Reaction": {
        icon: "💻",
        description: "Online campaigns, hashtag movements, social media mobilization, digital petitions, and cyber activism. Tracks the digital dimension of social reactions that unfold primarily online.",
    },
    "Conflict Reaction": {
        icon: "⚔️",
        description: "Violent clashes, riots, armed confrontations, property destruction, and other conflict-driven social reactions. Captures escalated responses that involve physical force or aggression.",
    },
};

function categoryColor(cat) {
    return CATEGORY_COLORS[cat] ?? "#95a5a6";
}

// ═══════════════════════════════════════════════════════════════
// Greece country information
// ═══════════════════════════════════════════════════════════════
const GREECE = {
    flag: "🇬🇷",
    name: "Greece",
    nameEl: "Ελλάδα",
    officialName: "Hellenic Republic",
    description: "Greece (Ελλάδα), officially the Hellenic Republic, is a country in Southeast Europe situated on the southern tip of the Balkans. Located at the crossroads of Europe, Asia, and Africa, it has one of the longest histories in the world, with its cultural heritage and influence having been pivotal in shaping Western civilization.",
    info: [
        { key: "Government",      val: "Unitary parliamentary republic" },
        { key: "Capital",         val: "Athens (Αθήνα)" },
        { key: "Language",        val: "Greek (Ελληνικά)" },
        { key: "Population",     val: "10.4 million (2024)" },
        { key: "Area",           val: "131,957 km²" },
        { key: "GDP",            val: "$239.3 billion (2024)" },
        { key: "Currency",       val: "Euro (€)" },
        { key: "President",      val: "Konstantinos Tasoulas" },
        { key: "Prime Minister", val: "Kyriakos Mitsotakis" },
    ],
};

// ═══════════════════════════════════════════════════════════════
// Greece geographic regions (13 peripheries)
// ═══════════════════════════════════════════════════════════════
const GREECE_REGIONS = [
    { name: "Attica",                       nameEl: "Αττική",                          center: [37.97, 23.72] },
    { name: "Central Greece",               nameEl: "Στερεά Ελλάδα",                   center: [38.65, 22.70] },
    { name: "Central Macedonia",            nameEl: "Κεντρική Μακεδονία",              center: [40.60, 23.00] },
    { name: "Crete",                        nameEl: "Κρήτη",                           center: [35.24, 24.90] },
    { name: "East. Macedonia & Thrace",     nameEl: "Αν. Μακεδονία & Θράκη",           center: [41.13, 25.40] },
    { name: "Epirus",                       nameEl: "Ήπειρος",                         center: [39.65, 20.85] },
    { name: "Ionian Islands",               nameEl: "Ιόνια Νησιά",                     center: [38.70, 20.50] },
    { name: "North Aegean",                 nameEl: "Βόρειο Αιγαίο",                   center: [39.10, 26.00] },
    { name: "Peloponnese",                  nameEl: "Πελοπόννησος",                    center: [37.50, 22.30] },
    { name: "South Aegean",                 nameEl: "Νότιο Αιγαίο",                    center: [36.90, 25.50] },
    { name: "Thessaly",                     nameEl: "Θεσσαλία",                        center: [39.60, 22.40] },
    { name: "Western Greece",               nameEl: "Δυτική Ελλάδα",                   center: [38.25, 21.45] },
    { name: "Western Macedonia",            nameEl: "Δυτική Μακεδονία",                center: [40.30, 21.80] },
];

// ═══════════════════════════════════════════════════════════════
// Basemap tile layers (free providers, no API key required)
// ═══════════════════════════════════════════════════════════════
const BASEMAPS = {
    dark: {
        url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr: '© <a href="https://www.openstreetmap.org/copyright">OSM</a> © <a href="https://carto.com/">CARTO</a>',
    },
    streets: {
        url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
    satellite: {
        url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr: '© <a href="https://www.esri.com/">Esri</a>',
    },
    topo: {
        url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr: '© <a href="https://opentopomap.org">OpenTopoMap</a>',
    },
};

// ═══════════════════════════════════════════════════════════════
// Application State
// ═══════════════════════════════════════════════════════════════
const state = {
    map: null,
    currentBasemap: "dark",
    tileLayer: null,
    markers: [],           // { marker, category, eventData }
    events: [],            // full event list from API
    stats: null,           // stats response
    activeCategories: new Set(Object.keys(CATEGORY_COLORS)),
    currentView: "country",
    selectedCategory: null,
    selectedEvent: null,
    regionsLayer: null,
    regionsVisible: true,
};

// ═══════════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════════
async function init() {
    initMap();
    initBasemapSwitcher();
    initCivicLayer();
    initDashboardNav();
    initSettings();
    initFullscreen();
    initSortable();
    fetchGithubStars();

    try {
        const [statsRes, eventsRes] = await Promise.all([
            fetch(`${CONFIG.API_BASE}/stats`).then(r => r.json()),
            fetch(`${CONFIG.API_BASE}/events`).then(r => r.json()),
        ]);
        state.stats = statsRes;
        state.events = eventsRes;

        renderMapMarkers();
        renderMapLegend();
        renderBreakingNews();
        renderDashboard();
        updateMapTimestamp();
    } catch (err) {
        console.error(err);
        showError("Could not connect to the API. Start the server with: uvicorn backend.api.main:app --reload --port 8000");
        renderMapLegend();
        renderDashboard();
    }
}

// ═══════════════════════════════════════════════════════════════
// Map
// ═══════════════════════════════════════════════════════════════
function initMap() {
    state.map = L.map("map", {
        zoomControl: true,
        attributionControl: true,
    }).setView(CONFIG.GREECE_CENTER, CONFIG.GREECE_ZOOM);

    setBasemap(state.currentBasemap);
    loadRegionLabels();
}

function setBasemap(name) {
    const def = BASEMAPS[name];
    if (!def) return;
    if (state.tileLayer) state.map.removeLayer(state.tileLayer);
    state.tileLayer = L.tileLayer(def.url, {
        attribution: def.attr,
        maxZoom: 18,
    }).addTo(state.map);
    state.currentBasemap = name;
}

async function loadRegionLabels() {
    if (state.regionsLayer) {
        state.map.removeLayer(state.regionsLayer);
        state.regionsLayer = null;
    }
    if (!state.regionsVisible) return;

    const group = L.layerGroup();

    // Map our region names → GeoJSON feature names where they differ
    const NAME_MAP = {
        "East. Macedonia & Thrace": "East Macedonia and Thrace",
        "Western Macedonia": "West Macedonia",
    };

    try {
        const res = await fetch("greece-regions.geojson");
        const geojson = await res.json();

        // Build lookup: GeoJSON name → feature
        const featureByName = {};
        for (const feat of geojson.features) {
            featureByName[feat.properties.name] = feat;
        }

        for (const region of GREECE_REGIONS) {
            const geoName = NAME_MAP[region.name] || region.name;
            const feature = featureByName[geoName];

            if (feature) {
                L.geoJSON(feature, {
                    style: {
                        color: "rgba(88, 166, 255, 0.35)",
                        fillColor: "rgba(88, 166, 255, 0.04)",
                        fillOpacity: 1,
                        weight: 1.2,
                        interactive: false,
                    },
                }).addTo(group);
            }
        }
    } catch (err) {
        console.warn("Could not load region boundaries:", err);
    }

    state.regionsLayer = group;
    group.addTo(state.map);
}

function updateMapTimestamp() {
    const el = document.getElementById("map-last-update");
    const now = new Date();
    el.textContent = `Last update: ${now.toLocaleDateString("en-GB")} ${now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}`;
}

// ═══════════════════════════════════════════════════════════════
// Map Markers
// ═══════════════════════════════════════════════════════════════
function syntheticCoords(clusterId) {
    const angle = (clusterId * 137.508) % 360;
    const radius = 0.6 + (clusterId % 6) * 0.35;
    const rad = angle * (Math.PI / 180);
    return [
        CONFIG.GREECE_CENTER[0] + radius * Math.cos(rad),
        CONFIG.GREECE_CENTER[1] + radius * Math.sin(rad),
    ];
}

function renderMapMarkers() {
    // Clear existing
    state.markers.forEach(({ marker }) => marker.remove());
    state.markers = [];

    for (const event of state.events) {
        const color = categoryColor(event.reaction_category);
        const hasGeo = event.lat != null && event.lon != null;
        const [lat, lon] = hasGeo
            ? [event.lat, event.lon]
            : syntheticCoords(event.cluster_id);

        const marker = L.circleMarker([lat, lon], {
            radius: 6 + Math.min(event.article_count, 8),
            fillColor: color,
            color: "#fff",
            weight: 1.5,
            opacity: hasGeo ? 1.0 : 0.45,
            fillOpacity: hasGeo ? 0.8 : 0.3,
        });

        const dateHtml = event.event_date
            ? `<p class="popup-meta">📅 ${event.event_date}</p>` : "";
        const locHtml = event.location_name
            ? `<p class="popup-meta">📍 ${event.location_name}</p>` : "";

        marker.bindPopup(
            `<div class="event-popup">
                <span class="popup-badge" style="background:${color}">${event.reaction_category}</span>
                <p class="popup-summary">${event.summary_en || "No summary available."}</p>
                ${dateHtml}${locHtml}
                <p class="popup-meta">📰 ${event.article_count} article${event.article_count !== 1 ? "s" : ""}</p>
                <p class="popup-meta">📡 ${event.sources.join(", ")}</p>
                <span class="popup-link" data-event-id="${event.event_id}">View in dashboard →</span>
            </div>`,
            { maxWidth: 340 }
        );

        marker.on("popupopen", () => {
            const link = document.querySelector(`.popup-link[data-event-id="${event.event_id}"]`);
            if (link) {
                link.addEventListener("click", () => {
                    state.selectedEvent = event;
                    setDashboardView("events");
                    renderDashboard();
                });
            }
        });

        if (state.activeCategories.has(event.reaction_category)) {
            marker.addTo(state.map);
        }

        state.markers.push({ marker, category: event.reaction_category, eventData: event });
    }
}

// ═══════════════════════════════════════════════════════════════
// Map Legend (bottom center)
// ═══════════════════════════════════════════════════════════════
function renderMapLegend() {
    const container = document.getElementById("map-legend");
    container.innerHTML = "";

    const catsToShow = Object.entries(CATEGORY_COLORS)
        .filter(([cat]) => {
            if (!state.stats) return CATEGORY_INFO[cat] != null;
            return (state.stats.categories[cat] ?? 0) > 0 || CATEGORY_INFO[cat] != null;
        });

    for (const [cat, color] of catsToShow) {
        if (cat === "Unknown" || cat === "None of the above" || cat === "None") continue;
        const chip = document.createElement("span");
        chip.className = "legend-chip" + (state.activeCategories.has(cat) ? "" : " inactive");
        chip.innerHTML = `<span class="legend-dot" style="background:${color}"></span>${shortCategoryName(cat)}`;
        chip.addEventListener("click", () => {
            toggleCategory(cat);
            chip.classList.toggle("inactive", !state.activeCategories.has(cat));
            // Also navigate to category view
            state.selectedCategory = cat;
            setDashboardView("categories");
            renderDashboard();
        });
        container.appendChild(chip);
    }
}

function shortCategoryName(cat) {
    const map = {
        "Mass Mobilization & Street Actions": "Mass Mobilization",
        "Labor & Economic Reaction": "Labor & Economy",
        "Institutional & Political Behavior": "Institutional",
        "Digital Reaction": "Digital",
        "Conflict Reaction": "Conflict",
    };
    return map[cat] || cat;
}

function toggleCategory(category) {
    if (state.activeCategories.has(category)) {
        state.activeCategories.delete(category);
    } else {
        state.activeCategories.add(category);
    }
    state.markers.forEach(({ marker, category: cat }) => {
        if (state.activeCategories.has(cat)) {
            marker.addTo(state.map);
        } else {
            marker.remove();
        }
    });
}

// ═══════════════════════════════════════════════════════════════
// Basemap Switcher
// ═══════════════════════════════════════════════════════════════
function initBasemapSwitcher() {
    document.querySelectorAll(".basemap-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".basemap-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            setBasemap(btn.dataset.basemap);
        });
    });
}

// ═══════════════════════════════════════════════════════════════
// Civic Response Map Layer
// ═══════════════════════════════════════════════════════════════
function initCivicLayer() {
    const toggle = document.getElementById("civic-toggle");
    const body = document.getElementById("civic-options");
    const arrow = toggle.querySelector(".civic-arrow");

    toggle.addEventListener("click", () => {
        body.classList.toggle("hidden");
        arrow.classList.toggle("open");
    });

    // Checkboxes are placeholders — actual data layers TBD
    document.querySelectorAll("#civic-options input[type=checkbox]").forEach(cb => {
        cb.addEventListener("change", () => {
            // Future: toggle corresponding map layer group
            console.log(`Civic layer "${cb.dataset.layer}" ${cb.checked ? "ON" : "OFF"}`);
        });
    });
}

// ═══════════════════════════════════════════════════════════════
// Breaking News Ticker
// ═══════════════════════════════════════════════════════════════
function renderBreakingNews() {
    const ticker = document.getElementById("ticker");
    ticker.innerHTML = "";

    if (!state.events.length) {
        ticker.innerHTML = '<span class="ticker-item" style="color:var(--text-muted)">No events available</span>';
        return;
    }

    // Sort by date descending, take top 20
    const sorted = [...state.events]
        .sort((a, b) => (b.event_date || "").localeCompare(a.event_date || ""))
        .slice(0, 20);

    // Duplicate items to create seamless loop
    const items = [...sorted, ...sorted];

    for (const event of items) {
        const span = document.createElement("span");
        span.className = "ticker-item";
        span.innerHTML = `
            <span class="ticker-dot" style="background:${categoryColor(event.reaction_category)}"></span>
            ${escapeHtml(event.summary_en || "Unclassified event")}
        `;
        span.addEventListener("click", () => {
            state.selectedEvent = event;
            setDashboardView("events");
            renderDashboard();
        });
        ticker.appendChild(span);
    }
}

// ═══════════════════════════════════════════════════════════════
// Dashboard Navigation
// ═══════════════════════════════════════════════════════════════
function initDashboardNav() {
    document.querySelectorAll("#dashboard-nav .nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const view = btn.dataset.view;
            // Reset selections when switching to generic view
            if (view === "country") { state.selectedCategory = null; state.selectedEvent = null; }
            if (view === "categories") { state.selectedEvent = null; }
            if (view === "events") { state.selectedCategory = null; }
            setDashboardView(view);
            renderDashboard();
        });
    });
}

function setDashboardView(view) {
    state.currentView = view;
    document.querySelectorAll("#dashboard-nav .nav-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.view === view);
    });
}

// ═══════════════════════════════════════════════════════════════
// Dashboard Rendering
// ═══════════════════════════════════════════════════════════════
function renderDashboard() {
    const container = document.getElementById("dashboard-content");
    container.innerHTML = "";

    switch (state.currentView) {
        case "country":
            renderCountryView(container);
            break;
        case "categories":
            renderCategoriesView(container);
            break;
        case "events":
            renderEventsView(container);
            break;
    }

    // Initialize Sortable on dashboard cards
    initDashboardCardSortable();
}

// ── Country View ──
function renderCountryView(container) {
    // Country overview card
    container.innerHTML += dashCard("COUNTRY OVERVIEW", `
        <div class="country-header">
            <span class="country-flag">${GREECE.flag}</span>
            <div class="country-names">
                <h2>${GREECE.name}</h2>
                <span class="country-name-el">${GREECE.nameEl} · ${GREECE.officialName}</span>
            </div>
        </div>
        <p class="country-desc">${GREECE.description}</p>
    `);

    // Info grid card
    let infoCells = GREECE.info.map(i =>
        `<div class="info-cell"><div class="info-key">${i.key}</div><div class="info-val">${i.val}</div></div>`
    ).join("");
    container.innerHTML += dashCard("BASIC INFORMATION", `<div class="info-grid">${infoCells}</div>`);

    // Stats card
    if (state.stats) {
        container.innerHTML += dashCard("STATISTICS", `
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">${formatNumber(state.stats.total_events)}</div>
                    <div class="stat-label">Events</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${formatNumber(state.stats.total_articles)}</div>
                    <div class="stat-label">Articles</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${formatNumber(state.stats.geocoded_articles)}</div>
                    <div class="stat-label">Geocoded</div>
                </div>
            </div>
        `);
    }

    // Distribution chart card
    if (state.stats && Object.keys(state.stats.categories).length > 0) {
        container.innerHTML += dashCard("DISTRIBUTION", '<div class="chart-container"><canvas id="bar-chart"></canvas></div>');
        renderChart(state.stats.categories);
    }
}

// ── Categories View ──
function renderCategoriesView(container) {
    if (state.selectedCategory && CATEGORY_INFO[state.selectedCategory]) {
        renderSingleCategoryView(container, state.selectedCategory);
        return;
    }

    // Show all categories overview
    container.innerHTML += '<a class="back-link" id="cat-back">← Back to Country</a>';

    for (const [cat, info] of Object.entries(CATEGORY_INFO)) {
        const color = categoryColor(cat);
        const count = state.stats?.categories[cat] ?? 0;
        const articleCount = state.events
            .filter(e => e.reaction_category === cat)
            .reduce((sum, e) => sum + e.article_count, 0);

        container.innerHTML += dashCard(cat.toUpperCase(), `
            <div class="cat-header">
                <span class="cat-icon">${info.icon}</span>
                <span class="cat-name"><span class="cat-badge" style="background:${color}"></span>${cat}</span>
            </div>
            <p class="cat-desc">${info.description}</p>
            <div class="cat-stats">
                <span class="cat-stat"><strong>${count}</strong> events</span>
                <span class="cat-stat"><strong>${articleCount}</strong> articles</span>
            </div>
        `, `cursor:pointer`, `data-cat="${escapeAttr(cat)}"`);
    }

    // Click handlers for category cards
    setTimeout(() => {
        document.querySelectorAll("[data-cat]").forEach(el => {
            el.addEventListener("click", () => {
                state.selectedCategory = el.dataset.cat;
                renderDashboard();
            });
        });
        const backLink = document.getElementById("cat-back");
        if (backLink) backLink.addEventListener("click", () => { setDashboardView("country"); renderDashboard(); });
    }, 0);
}

function renderSingleCategoryView(container, cat) {
    const info = CATEGORY_INFO[cat];
    const color = categoryColor(cat);
    const catEvents = state.events.filter(e => e.reaction_category === cat);
    const articleCount = catEvents.reduce((sum, e) => sum + e.article_count, 0);

    container.innerHTML += '<a class="back-link" id="cat-back-single">← Back to All Categories</a>';

    container.innerHTML += dashCard("CATEGORY DETAIL", `
        <div class="cat-header">
            <span class="cat-icon">${info.icon}</span>
            <span class="cat-name"><span class="cat-badge" style="background:${color}"></span>${cat}</span>
        </div>
        <p class="cat-desc">${info.description}</p>
        <div class="cat-stats">
            <span class="cat-stat"><strong>${catEvents.length}</strong> events</span>
            <span class="cat-stat"><strong>${articleCount}</strong> articles</span>
        </div>
    `);

    // Recent events in this category
    if (catEvents.length > 0) {
        let eventListHtml = catEvents
            .sort((a, b) => (b.event_date || "").localeCompare(a.event_date || ""))
            .slice(0, 30)
            .map(e => `
                <div class="event-list-item" data-event-id="${e.event_id}">
                    <span class="event-cat-dot" style="background:${color}"></span>
                    <div class="event-list-info">
                        <div class="event-list-title">${escapeHtml(e.summary_en || "No summary")}</div>
                        <div class="event-list-meta">${e.event_date || "—"} · ${e.article_count} articles · ${e.sources.join(", ")}</div>
                    </div>
                </div>
            `).join("");
        container.innerHTML += dashCard(`RECENT EVENTS (${catEvents.length})`, eventListHtml);
    }

    // Click handlers
    setTimeout(() => {
        document.querySelectorAll(".event-list-item[data-event-id]").forEach(el => {
            el.addEventListener("click", () => {
                const ev = state.events.find(e => e.event_id === el.dataset.eventId);
                if (ev) { state.selectedEvent = ev; setDashboardView("events"); renderDashboard(); }
            });
        });
        const backLink = document.getElementById("cat-back-single");
        if (backLink) backLink.addEventListener("click", () => { state.selectedCategory = null; renderDashboard(); });
    }, 0);
}

// ── Events View ──
function renderEventsView(container) {
    if (state.selectedEvent) {
        renderSingleEventView(container, state.selectedEvent);
        return;
    }

    // Show all events list
    container.innerHTML += '<a class="back-link" id="evt-back">← Back to Country</a>';

    if (!state.events.length) {
        container.innerHTML += '<div class="empty-state"><div class="empty-state-icon">📡</div><p>No events loaded yet.</p></div>';
        setTimeout(() => {
            const backLink = document.getElementById("evt-back");
            if (backLink) backLink.addEventListener("click", () => { setDashboardView("country"); renderDashboard(); });
        }, 0);
        return;
    }

    const sorted = [...state.events].sort((a, b) => (b.event_date || "").localeCompare(a.event_date || ""));
    let listHtml = sorted.map(e => `
        <div class="event-list-item" data-event-id="${e.event_id}">
            <span class="event-cat-dot" style="background:${categoryColor(e.reaction_category)}"></span>
            <div class="event-list-info">
                <div class="event-list-title">${escapeHtml(e.summary_en || "No summary")}</div>
                <div class="event-list-meta">${e.event_date || "—"} · ${e.reaction_category} · ${e.article_count} articles</div>
            </div>
        </div>
    `).join("");

    container.innerHTML += dashCard(`ALL EVENTS (${state.events.length})`, listHtml);

    setTimeout(() => {
        document.querySelectorAll(".event-list-item[data-event-id]").forEach(el => {
            el.addEventListener("click", () => {
                const ev = state.events.find(e => e.event_id === el.dataset.eventId);
                if (ev) { state.selectedEvent = ev; renderDashboard(); }
            });
        });
        const backLink = document.getElementById("evt-back");
        if (backLink) backLink.addEventListener("click", () => { setDashboardView("country"); renderDashboard(); });
    }, 0);
}

function renderSingleEventView(container, event) {
    const color = categoryColor(event.reaction_category);

    container.innerHTML += '<a class="back-link" id="evt-back-single">← Back to Events</a>';

    container.innerHTML += dashCard("EVENT DETAIL", `
        <span class="popup-badge" style="background:${color}">${event.reaction_category}</span>
        <p class="event-detail-summary">${escapeHtml(event.summary_en || "No summary available.")}</p>
        <div class="event-detail-meta">
            ${event.event_date ? `<span>📅 ${event.event_date}</span>` : ""}
            ${event.location_name ? `<span>📍 ${event.location_name}</span>` : ""}
            <span>📰 ${event.article_count} article${event.article_count !== 1 ? "s" : ""}</span>
            <span>📡 ${event.sources.join(", ")}</span>
        </div>
    `);

    // Greek summary
    if (event.summary_el) {
        container.innerHTML += dashCard("SUMMARY (GREEK)", `
            <p class="event-detail-summary">${escapeHtml(event.summary_el)}</p>
        `);
    }

    // Fetch articles for this event
    fetchEventArticles(event.event_id, container);

    // Pan map to event location
    if (event.lat != null && event.lon != null) {
        state.map.flyTo([event.lat, event.lon], 10, { duration: 1 });
    }

    setTimeout(() => {
        const backLink = document.getElementById("evt-back-single");
        if (backLink) backLink.addEventListener("click", () => { state.selectedEvent = null; renderDashboard(); });
    }, 0);
}

async function fetchEventArticles(eventId, container) {
    try {
        const res = await fetch(`${CONFIG.API_BASE}/events/${eventId}`);
        if (!res.ok) return;
        const detail = await res.json();
        if (!detail.articles || !detail.articles.length) return;

        let articlesHtml = detail.articles.map((a, i) => `
            <div class="article-item">
                <span class="article-idx">${i + 1}</span>
                <div class="article-info">
                    <div class="article-title" onclick="window.open('${escapeAttr(a.url)}', '_blank')">${escapeHtml(a.title || "Untitled")}</div>
                    <div class="article-meta">${a.source} · ${a.published_at || "—"}</div>
                </div>
            </div>
        `).join("");

        // Append articles card
        const card = document.createElement("div");
        card.innerHTML = dashCard(`ARTICLES (${detail.articles.length})`, articlesHtml);
        container.appendChild(card.firstElementChild);
    } catch (err) {
        console.warn("Could not fetch event articles:", err);
    }
}

// ═══════════════════════════════════════════════════════════════
// Dashboard Card helper
// ═══════════════════════════════════════════════════════════════
function dashCard(title, bodyHtml, extraStyle, extraAttr) {
    return `<div class="dash-card" ${extraAttr || ""} ${extraStyle ? `style="${extraStyle}"` : ""}>
        <div class="dash-card-header">
            <span>${title}</span>
            <span class="card-drag">⋮⋮</span>
        </div>
        <div class="dash-card-body">${bodyHtml}</div>
    </div>`;
}

// ═══════════════════════════════════════════════════════════════
// Chart (Bar chart)
// ═══════════════════════════════════════════════════════════════
function renderChart(categoryCounts) {
    const canvas = document.getElementById("bar-chart");
    if (!canvas) return;

    const entries = Object.entries(categoryCounts)
        .filter(([, v]) => v > 0)
        .sort((a, b) => b[1] - a[1]);

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: entries.map(([k]) => shortCategoryName(k)),
            datasets: [{
                data: entries.map(([, v]) => v),
                backgroundColor: entries.map(([k]) => categoryColor(k)),
                borderWidth: 0,
                borderRadius: 3,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: { color: "#484f58", font: { size: 10 } },
                },
                y: {
                    grid: { display: false },
                    ticks: { color: "#8b949e", font: { size: 10 } },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════
// Drag & Drop (Sortable.js)
// ═══════════════════════════════════════════════════════════════
function initSortable() {
    // Main panels (map + dashboard) can be reordered
    const content = document.getElementById("content");
    if (typeof Sortable !== "undefined") {
        new Sortable(content, {
            animation: 200,
            handle: ".panel-handle",
            ghostClass: "sortable-ghost",
            chosenClass: "sortable-chosen",
            direction: "horizontal",
        });
    }
}

function initDashboardCardSortable() {
    const container = document.getElementById("dashboard-content");
    if (typeof Sortable !== "undefined" && container) {
        new Sortable(container, {
            animation: 150,
            handle: ".dash-card-header",
            ghostClass: "sortable-ghost",
            draggable: ".dash-card",
        });
    }
}

// ═══════════════════════════════════════════════════════════════
// Settings Modal
// ═══════════════════════════════════════════════════════════════
function initSettings() {
    const overlay = document.getElementById("settings-overlay");
    const btnOpen = document.getElementById("btn-settings");
    const btnClose = document.getElementById("settings-close");
    const btnSave = document.getElementById("settings-save");
    const providerSelect = document.getElementById("setting-map-provider");
    const apikeyGroup = document.getElementById("setting-apikey-group");

    btnOpen.addEventListener("click", () => overlay.classList.remove("hidden"));
    btnClose.addEventListener("click", () => overlay.classList.add("hidden"));
    overlay.addEventListener("click", e => { if (e.target === overlay) overlay.classList.add("hidden"); });

    // Load saved settings
    const savedApi = localStorage.getItem("sra_api");
    if (savedApi) document.getElementById("setting-api").value = savedApi;
    const savedRegions = localStorage.getItem("sra_regions");
    if (savedRegions !== null) document.getElementById("setting-regions").checked = savedRegions !== "false";

    // Show/hide API key field based on provider
    providerSelect.addEventListener("change", () => {
        apikeyGroup.classList.toggle("hidden", providerSelect.value === "free");
    });

    btnSave.addEventListener("click", () => {
        const apiVal = document.getElementById("setting-api").value.trim();
        if (apiVal) localStorage.setItem("sra_api", apiVal);
        localStorage.setItem("sra_regions", document.getElementById("setting-regions").checked);
        overlay.classList.add("hidden");
        location.reload();
    });
}

// ═══════════════════════════════════════════════════════════════
// Fullscreen Toggle
// ═══════════════════════════════════════════════════════════════
function initFullscreen() {
    document.getElementById("btn-fullscreen").addEventListener("click", () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(() => {});
        } else {
            document.exitFullscreen().catch(() => {});
        }
    });
}

// ═══════════════════════════════════════════════════════════════
// GitHub Stars
// ═══════════════════════════════════════════════════════════════
async function fetchGithubStars() {
    try {
        const res = await fetch(`https://api.github.com/repos/${CONFIG.GITHUB_REPO}`);
        if (!res.ok) return;
        const data = await res.json();
        const count = data.stargazers_count ?? 0;
        document.getElementById("github-stars").textContent = `★ ${formatNumber(count)}`;
    } catch { /* silent fail */ }
}

// ═══════════════════════════════════════════════════════════════
// Error Banner
// ═══════════════════════════════════════════════════════════════
function showError(msg) {
    const el = document.getElementById("error-banner");
    el.textContent = "⚠ " + msg;
    el.style.display = "block";
}

// ═══════════════════════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════════════════════
function formatNumber(n) {
    if (n == null) return "—";
    return n.toLocaleString("en-US");
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#39;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ═══════════════════════════════════════════════════════════════
// Entry point
// ═══════════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", init);
