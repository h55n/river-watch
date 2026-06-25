# River Watch — SAR-Based Illegal Sand Mining Detection Platform
### Complete Project Specification (Idea, Architecture, Tech Stack, Build Plan)

**Status:** Pre-build, zero-cost, solo/small-team
**Type:** Open public-good geospatial web tool, India-focused
**Build philosophy:** AI-agent-assisted development, free data + free hosting only, credible-first with a controlled attention layer

---

## 1. Problem Statement

Illegal riverbed sand mining in India causes real, documented damage:

- **Economic:** estimated losses in the tens of thousands of crores annually (state-level CAG/PAC audits, e.g. Karnataka alone estimated ₹18,000–20,000 crore — always cite the specific source used in any given pitch, never a single unsourced headline number)
- **Infrastructure:** bridge and embankment destabilization from undermined foundations near active mining
- **Ecological:** riverbed incision, bank erosion, altered river courses, groundwater table depletion, loss of sandbar nesting habitat (e.g. gharial and turtle nesting sites in stretches like the Chambal)

**Why enforcement fails today:**
- Sand is a "minor mineral" under the MMDR Act, 1957 — regulated **state-by-state** under Section 15 (concessions) and Section 23C (illegal mining prevention), with 21+ states running their own, inconsistent rules
- Detection is largely manual: patrol boats, occasional drone sorties, sparse state programs (e.g. Gujarat's Trinetra drone pilot)
- The central Mining Surveillance System (MSS) focuses on **major mineral leases**; minor minerals like sand are far less covered
- **Core insight:** the bottleneck is rarely visibility — officials and locals often already know where illegal mining happens. The bottleneck is *actionable, dated, defensible evidence* reaching someone with the power and motivation to act, before the evidence (and the sandbar) disappears.

---

## 2. What This Is (Honest Technical Framing)

### 2.1 What it is NOT — guardrails, never violate these in product copy
- **NOT a riverbed depth/elevation tool.** SAR (radar) does not penetrate water to measure what's underneath it on a river. SAR bathymetry only works indirectly via swell/wave-pattern inversion on open coastal/ocean water — a mechanism that does not apply to river settings. Never claim "elevation change detection." This is the single fastest way to lose a technical reviewer's trust.
- **NOT real-time.** Sentinel-1/2 revisit is in days, not minutes. Every layer shows a visible last-updated/last-pass timestamp. Never use "live" without that timestamp next to it.
- **NOT a deforestation detector.** Global Forest Watch (WRI) + RADD alerts already solve this at planetary scale using Sentinel-1 SAR, updated weekly. Don't rebuild it — integrate their free public API as a credited reference layer only.
- **NOT an "illegal mining confirmed" tool.** It flags *anomalies* against a seasonal baseline. Confirmation is a human/legal/journalistic judgment, never an automated claim.
- **NOT gated behind login/sales/procurement.** Public, free, browsable from day one.

### 2.2 What it actually detects

**Signal 1 — Equipment & Vessel Presence (SAR backscatter anomaly)**
Metal objects (dredgers, excavators, trucks parked on sandbars) cause strong specular radar returns even when smaller than a pixel — the same physics used to detect ships at sea. Sudden high-backscatter anomalies in a normally "quiet" riverbed/sandbar zone — especially at night or under cloud cover, when optical imagery is blind — are a strong proxy for active extraction equipment.
- Source: Sentinel-1 GRD (C-band SAR), VV/VH polarization
- Method: log-ratio difference between successive passes over the same area; flag pixels/clusters exceeding a noise-adjusted threshold

**Signal 2 — Sandbar / Bankline Morphology Change (optical + SAR fusion)**
Track exposed sandbar area and waterbody extent per river segment, compared against a **rolling seasonal baseline** — critical, because a raw before/after comparison without seasonal normalization will misfire on monsoon-driven natural channel shifts (the single most likely "gotcha" question from any technical reviewer or skeptical official).
- Source: Sentinel-2 optical (NDWI water index) primary; Sentinel-1 as cloud-cover backup
- Method: NDWI-based water/sediment mask, segment-wise area time series, anomaly = deviation beyond the historical seasonal range for that *specific* segment, not a global threshold

**Signal 3 — Supplementary "live-feel" layers (clearly separate, clearly credited, not original detection work)**
- **NASA FIRMS** — free, genuinely near-real-time fire/thermal anomaly data (kiln burning, land-clearing fires), used to make the map feel alive without overstating SAR's own cadence
- **Global Forest Watch public API** — credited reference layer only

### 2.3 Current revisit cadence (state as of build time, verify before any pitch)
Sentinel-1 constellation is mid-transition: Sentinel-1C (launched Dec 2024) and Sentinel-1D (launched Nov 2025) are both operational, moving toward a steady **~6-day** nominal revisit once final constellation configuration completes, replacing the older single-satellite 12-day cycle. State this accurately — "improving toward 6-day revisit," not "real-time."

---

## 3. Validation Strategy — Backtest First, Always

No live/real-time claims at launch. The credibility anchor is **historical backtesting against a documented incident**:

1. Identify a specific river stretch with a known, news-reported or court-documented illegal sand mining case (regional press, NGT orders, court judgments)
2. Pin down the approximate location and date range of the incident
3. Run the detection pipeline against the Sentinel-1/2 archive for that exact window plus a clean "before" baseline period
4. Show the anomaly flag lining up with the real-world, independently-verified incident date
5. Package this as the first **Case File** (Section 5.2) — this is the credibility anchor for the entire project, the thing that gets shared and sent to journalists/lawyers/NGOs, not the raw live feed

---

## 4. Buyer / Beneficiary Thesis

**Rejected as primary target:** state mining departments as direct customers/buyers. Statutory duty (Section 23C) does not reliably convert to demand — fragmented across 21+ states, several already run their own surveillance, and enforcement sometimes intersects with the same local political-mafia nexus the tool would expose. Government access is **earned later**, through track record, never pitched cold as a sale.

**Primary beneficiaries — real people with a real, immediate action available to them:**

| Beneficiary | Action they take with a flag | Why they're motivated |
|---|---|---|
| NGT litigants / environmental lawyers | File as evidence in active cases | Already need exactly this kind of dated, defensible evidence; have legal standing |
| Journalists / RTI activists | Investigate, publish, create public pressure | Story-driven; satellite evidence is citable and visual |
| Local river-conservation NGOs / citizen groups | Escalate locally, repeat usage (their river) | Direct stake; most likely to be a returning user |
| Legal sand lease-holder associations | Use as evidence illegal operators are undercutting them | Commercial motive, not statutory — most novel, underused angle |
| Private infrastructure owners (bridges/assets near mining) | Risk monitoring, may commission deeper service later | Their own asset risk, not goodwill |

**Path to government:** earned, never sold cold. One verified case that "caught" something before it became a court case or news story is the credibility door-opener. Position to government always as "independent, complementary evidence layer" — never a replacement for or competitor to MSS.

**Credible + Attention, reconciled:** every individual live flag stays conservative and hedged (credibility layer — protects you legally and reputationally). Public attention is earned through a small number of fully verified, backtested Case Files that get actively sent to journalists, lawyers, and NGOs (attention layer, routed through people who can apply real pressure — not virality for its own sake).

---

## 5. Product Structure — Two-Tier Public Website

### 5.1 Tier 1 — Anomaly Watch (always-on, hedged, low-drama)
- Live(ish) map of monitored river segments
- Every anomaly labeled "Anomaly detected — under review," never "confirmed illegal"
- Visible last-updated timestamp per layer (SAR pass date, optical pass date)
- Seasonal baseline range shown alongside the current reading, so "is this just monsoon variation" is answered before it's asked
- Builds trust over time through consistency and restraint

### 5.2 Tier 2 — Case Files (the attention layer)
- Small, curated set of **fully backtested, independently verified** incidents
- Each = before/after imagery, anomaly score, matching real-world news/court reference, written as a clear narrative
- This is what gets shared publicly and sent directly to journalists/lawyers/NGOs
- Quality over quantity — one rigorous Case File beats five speculative ones

### 5.3 Evidence Card (atomic unit, used in both tiers)
- Coordinates + map thumbnail
- Date(s) of imagery
- Before/after visual
- Anomaly type (equipment-backscatter vs. morphology-change) and score
- Seasonal baseline comparison chart
- Explicit confidence/hedge language
- Downloadable/shareable (PDF or image export) for use in filings or articles

---

## 6. Complete Tech Stack (Zero Cost)

| Layer | Tool | Cost | Notes |
|---|---|---|---|
| SAR imagery | Sentinel-1 GRD via Google Earth Engine | Free | No download needed, server-side compute |
| Optical imagery | Sentinel-2 via Google Earth Engine | Free | NDWI water index |
| Raw archive access (fallback) | Copernicus Data Space Ecosystem / Sentinel Hub | Free | If GEE collection has gaps |
| Processing / compute | Google Earth Engine (JS or Python API) | Free tier | Core anomaly + baseline engine lives here |
| Supplementary live layer | NASA FIRMS API | Free | Fire/thermal near-real-time overlay |
| Supplementary reference layer | Global Forest Watch public API | Free | Credited, not built by this project |
| Frontend mapping | Leaflet.js (recommended) or Mapbox GL JS | Free tier | Leaflet has no API key friction |
| Frontend framework | Static HTML/JS or lightweight React | Free | Keep it simple — no build complexity needed |
| App hosting | Streamlit Community Cloud OR Earth Engine Apps | Free | Streamlit is faster to iterate on for a solo build |
| Evidence card export | Client-side PDF/image generation (e.g. browser-native canvas/print) | Free | No backend needed |
| Version control / collaboration | GitHub (public repo) | Free | Also doubles as transparency/credibility signal |
| Dev approach | AI-agent-assisted, multiple agents on subsystems (data pipeline, frontend, case-file authoring) in parallel | Time only | Mirrors fast solo-build patterns: agents on different subsystems simultaneously |

**No imagery purchase. No GPU rental. No backend server cost.**

---

## 7. Project Structure

```
river-watch/
├── README.md                       # public-facing project overview
├── river-watch-full-spec.md        # this document
├── data/
│   ├── segments/                   # GeoJSON definitions of monitored river segments
│   │   └── segment_<id>.geojson
│   ├── baselines/                  # cached seasonal baseline stats per segment
│   │   └── baseline_<segment_id>.json
│   └── case_files/                 # source data backing each verified case file
│       └── case_<id>/
│           ├── metadata.json       # location, date range, source citations
│           ├── before.tif / after.tif
│           └── writeup.md
├── pipeline/
│   ├── gee_auth.py                 # Earth Engine auth/init
│   ├── sar_anomaly.py              # Sentinel-1 backscatter log-ratio detection
│   ndwi_baseline.py                # Sentinel-2 NDWI + seasonal baseline calc
│   ├── seasonal_baseline_builder.py # builds rolling baseline per segment
│   ├── anomaly_scorer.py           # combines signals into anomaly score
│   └── export_evidence_card.py     # generates Evidence Card JSON/image
├── integrations/
│   ├── firms_client.py             # NASA FIRMS fetch
│   └── gfw_client.py               # Global Forest Watch fetch (reference layer only)
├── app/
│   ├── streamlit_app.py            # main Streamlit entrypoint (or app.py for static/Leaflet)
│   ├── pages/
│   │   ├── 1_anomaly_watch.py      # Tier 1
│   │   └── 2_case_files.py         # Tier 2
│   ├── components/
│   │   ├── map_view.py
│   │   ├── evidence_card.py
│   │   └── baseline_chart.py
│   └── static/
│       ├── style.css
│       └── assets/
├── scripts/
│   ├── backtest_case.py            # runs pipeline against a known historical incident
│   └── add_segment.py              # CLI helper to register a new river segment
├── tests/
│   └── test_anomaly_scorer.py
└── requirements.txt
```

---

## 8. Phase-Wise Build Plan

Each phase is gated on the previous one. Do not parallelize phases 1–4; the whole project's credibility depends on getting phase 3 right before anything public ships.

### Phase 0 — Research & Grounding (before writing any code)
- [ ] Identify one river segment with a real, documented, dateable illegal sand mining incident (news/court-verifiable — search Indian regional press, NGT orders, court judgments)
- [ ] Pin down approximate location (coordinates/bounding box) and date range of the incident
- [ ] Identify one clean "before" baseline period for that same segment (no known incidents)
- [ ] Note exact source citations for every figure/claim used later in copy (no unsourced headline numbers)

### Phase 1 — Core Detection Pipeline (single segment only)
- [ ] Set up Google Earth Engine account + authentication
- [ ] Build Sentinel-1 GRD ingestion for the chosen segment (VV/VH)
- [ ] Implement backscatter log-ratio anomaly detection between successive passes
- [ ] Build Sentinel-2 NDWI water/sediment mask for the same segment
- [ ] Build seasonal baseline calculator (rolling historical range, segment-specific)
- [ ] Combine both signals into a single anomaly score

### Phase 2 — Backtest & Validate
- [ ] Run the full pipeline against the known incident's date window + baseline period
- [ ] Confirm the anomaly flag aligns with the real-world incident date
- [ ] If it doesn't align cleanly: diagnose (wrong segment boundary? noisy vegetation? wrong date range?) before moving forward — do not proceed to Phase 3 on a shaky result
- [ ] Document the full backtest methodology for transparency (this is part of your credibility story)

### Phase 3 — First Case File
- [ ] Generate before/after imagery for the verified incident
- [ ] Write the narrative: what was flagged, when, matched against the independent news/court reference
- [ ] Build the Evidence Card for this case (Section 5.3 fields)
- [ ] Internal review: does every claim use hedged language? Any claim that could read as an accusation rather than an anomaly flag?

### Phase 4 — Minimal Public Site
- [ ] Build Tier 1 Anomaly Watch map, scoped to just this one segment
- [ ] Build Tier 2 Case Files page with the single verified case
- [ ] Add visible last-updated timestamps everywhere
- [ ] Add NASA FIRMS overlay (clearly labeled, clearly separate from SAR detection)
- [ ] Deploy to Streamlit Community Cloud (or Earth Engine Apps)
- [ ] Publish GitHub repo publicly (transparency signal)

### Phase 5 — First Real Outreach
- [ ] Identify one real lawyer/NGT litigant, journalist, or river-conservation NGO actually working that river/region
- [ ] Send them the Case File directly, with context on what it is and isn't
- [ ] Track any response/usage — this becomes your credibility asset

### Phase 6 — Expand (only after Phase 5 has real signal)
- [ ] Add additional river segments using the same pipeline
- [ ] Consider additional verticals (quarry-boundary expansion, wetland encroachment) — **only after independently verifying ground-truth data and lease-boundary GIS availability for each; do not assume the engine transfers without validation**
- [ ] Add Global Forest Watch reference layer if relevant to the region
- [ ] Track any real-world pickup (citation, use in filing, published story) — this is the asset for any future government outreach

---

## 9. Known Open Risks (be honest about these, in the product and in any pitch)

- **False positive risk to credibility and to real people** — a single wrongly-flagged location, publicly displayed, is a real legal and reputational risk. Every public-facing flag must use hedged language ("anomaly," "under review"), never accusatory language ("illegal mining confirmed").
- **No live ground-truth feed** — the tool cannot confirm anything on its own; it depends entirely on humans (lawyers, journalists, NGOs) converting flags into real-world action. If no one picks it up, it's an awareness tool with no enforcement teeth — the same failure mode as MSS.
- **Multi-vertical expansion is unvalidated** — wetland encroachment and quarry-boundary detection *may* reuse the core engine, but each needs independent ground-truth validation and (for quarry boundaries specifically) confirmed availability of free, usable lease-boundary GIS data before being presented as functional. Treat as labeled future scope only until verified.
- **Sandbar/water masking accuracy** in turbid, narrow, or heavily vegetated river segments may be noisy — pick validation segments where the signal is clean before generalizing.
- **Attention vs. credibility tension** — language drift toward dramatic/accusatory framing in pursuit of attention is the single biggest way this project could damage its own credibility. Every piece of public copy should be reviewed against Section 2.1's guardrails before publishing.

---

## 10. One-Line Pitch

*"A free, open, evidence-grade satellite watch for India's rivers — built to give lawyers, journalists, and local communities the dated proof they need to act on illegal sand mining, before the sandbar disappears."*
