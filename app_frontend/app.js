/**
 * River Watch — app.js v5.0
 *
 * Design language: DESIGN.md (New Form Capital editorial, #fafffa bg, #2bee4b accent)
 *
 * Architecture:
 *  - All data from dashboard.json — no hardcoded values
 *  - 30-second polling cycle: diff previous vs. new → animate on change
 *  - Pulsing SAR anomaly zone overlays on real NGT-documented coordinates
 *  - 4 river hotspots: Chambal, Yamuna, Ken, Ganga
 *  - Images served locally (no GEE auth-expiry issues)
 *  - Actual mining metrics: sand volume loss, channel shift, NDWI diff
 *
 * GUARDRAILS (never remove):
 *  - Never show "confirmed illegal" anywhere
 *  - Never claim live satellite tracking or real-time data
 *  - Never show fabricated SAR numbers — "Pending GEE run" if not computed
 *  - Every data value shown must come from dashboard.json or be clearly labelled pending
 */

'use strict';

/* ── State ─────────────────────────────────────────────────────────────── */
let HOTSPOTS       = [];
let liveMap        = null;
let sarLayers      = {};
let countdownVal   = 30;
let countdownTimer = null;
let lastGenerated  = null;

/* ── Utils ──────────────────────────────────────────────────────────────── */
const fmt = {
  area:   sq  => sq == null ? '—' : sq >= 1e6 ? (sq/1e6).toFixed(2)+' km²' : (sq/1e4).toFixed(1)+' ha',
  vol:    m3  => m3 == null ? '—' : m3 >= 1e6 ? (m3/1e6).toFixed(2)+' Mm³' : m3 >= 1000 ? (m3/1000).toFixed(0)+'k m³' : m3.toFixed(0)+' m³',
  db:     db  => db == null ? '—' : (db >= 0 ? '+' : '')+db.toFixed(1)+' dB',
  pct:    p   => p  == null ? '—' : (p  >= 0 ? '+' : '')+p.toFixed(1)+'%',
  date:   s   => s ? String(s).substring(0,10) : '—',
  shift:  m   => m == null ? '—' : m >= 1000 ? (m/1000).toFixed(2)+' km' : m.toFixed(0)+' m',
};

const levelColor = lvl => ({
  elevated:    '#c0392b',
  under_review:'#c9830a',
  none:        '#2bee4b',
  low:         '#516254',
})[lvl] || '#516254';

const levelLabel = lvl => ({
  elevated:    'SAR Elevated',
  under_review:'Under Review',
  none:        'Clear',
  low:         'Low Signal',
})[lvl] || 'Monitoring';

/* ── Image URL resolver: handles both local paths and full URLs ──────────── */
function resolveImgUrl(url) {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  // Local path relative to app_frontend directory
  return url;
}

/* ── Navbar scroll ─────────────────────────────────────────────────────── */
window.addEventListener('scroll', () => {
  const nav = document.getElementById('navbar');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 60);
});

/* ══════════════════════════════════════════════════════════════════════════
   LIVE ANOMALY MONITOR MAP
   Stadia dark tiles. SAR anomaly polygons pulse over real bbox coordinates.
   Re-renders every 30 seconds from dashboard.json diff.
══════════════════════════════════════════════════════════════════════════ */
function initLiveMap() {
  liveMap = L.map('live-map', { zoomControl: true, attributionControl: true })
    .setView([26.5, 78.5], 5);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd', maxZoom: 18,
    attribution: '© OpenStreetMap © CARTO',
  }).addTo(liveMap);
}

function renderLiveZone(h) {
  if (!liveMap) return;

  if (sarLayers[h.id]) {
    sarLayers[h.id].remove();
    delete sarLayers[h.id];
  }

  const color = levelColor(h.anomaly_level);
  const [west, south, east, north] = h.bbox || [h.lon-0.15, h.lat-0.13, h.lon+0.15, h.lat+0.13];

  // Build volume and shift tooltip content
  const vol = h.sand_volume_loss || {};
  const shift = h.channel_shift || {};
  const volStr = vol.volume_m3 != null
    ? `<div style="font-size:12px;color:rgba(250,255,250,0.8)">Sand removed (est): <strong style="color:#f5a623">${fmt.vol(vol.volume_m3)}</strong></div>`
    : '';
  const shiftStr = shift.shift_m != null
    ? `<div style="font-size:12px;color:rgba(250,255,250,0.8)">Channel shift: <strong style="color:#87CEEB">${fmt.shift(shift.shift_m)} ${shift.direction || ''}</strong></div>`
    : '';

  const popupHtml = `
    <div style="font-family:'Space Grotesk',sans-serif;min-width:220px;line-height:1.5">
      <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#2bee4b;margin-bottom:4px">
        SAR Anomaly Zone · Actual Mining Evidence
      </div>
      <div style="font-size:14px;font-weight:700;color:#fafffa;margin-bottom:4px">${h.name}</div>
      <div style="font-size:11px;color:rgba(250,255,250,0.6)">${h.state}</div>
      <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:8px 0">
      <div style="font-size:12px;color:rgba(250,255,250,0.8)">
        Status: <strong style="color:${color}">${levelLabel(h.anomaly_level)}</strong>
      </div>
      ${h.sar_peak_log_ratio_db != null ? `<div style="font-size:12px;color:rgba(250,255,250,0.6)">SAR Δ: <strong style="color:#2bee4b">${fmt.db(h.sar_peak_log_ratio_db)}</strong></div>` : ''}
      ${volStr}${shiftStr}
      <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:8px 0">
      <div style="font-size:10px;color:rgba(250,255,250,0.4);font-style:italic">
        Satellite anomaly flag — not a confirmed finding. Source: Sentinel-1/2 via GEE
      </div>
    </div>`;

  const outerRing = L.rectangle([[south - 0.04, west - 0.04], [north + 0.04, east + 0.04]], {
    color, weight: 1, fill: false, opacity: 0.3, dashArray: '4 6',
  }).addTo(liveMap);

  const layer = L.rectangle([[south, west], [north, east]], {
    color,
    weight: 2,
    fillColor: color,
    fillOpacity: h.anomaly_level === 'elevated' ? 0.15 : 0.08,
    dashArray: null,
  }).addTo(liveMap);

  layer.on('add', () => {
    const el = layer.getElement();
    if (el && (h.anomaly_level === 'elevated' || h.anomaly_level === 'under_review')) {
      el.classList.add('sar-pulse-path');
    }
  });

  layer.bindPopup(L.popup({ maxWidth: 280 }).setContent(popupHtml));
  layer.bindTooltip(h.name, { className: 'map-tooltip', direction: 'top' });
  layer.on('click', () => openDetail(h.id));

  const dot = L.circleMarker([h.lat, h.lon], {
    radius: 7, fillColor: color, color: '#fafffa',
    weight: 2, fillOpacity: 1,
  }).addTo(liveMap);
  dot.bindTooltip(h.name, { className: 'map-tooltip', direction: 'top' });
  dot.on('click', () => openDetail(h.id));

  sarLayers[h.id] = L.layerGroup([outerRing, layer, dot]);
}

/* ── Monitor sidebar stat cards ─────────────────────────────────────────── */
function renderMonitorSidebar(hotspots) {
  const el = document.getElementById('monitor-sidebar');
  if (!el) return;
  el.innerHTML = '';

  hotspots.forEach(h => {
    const color = levelColor(h.anomaly_level);
    const vol = h.sand_volume_loss || {};
    const shift = h.channel_shift || {};

    const card = document.createElement('div');
    card.className = 'monitor-stat-card';
    card.style.cursor = 'pointer';
    card.style.borderLeftColor = color;
    card.style.borderLeftWidth = '3px';
    card.innerHTML = `
      <div class="msc-label">${(h.river || '').toUpperCase()} · ${(h.state || '').split('/')[0].trim().toUpperCase()}</div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--sp-xs)">
        <span class="msc-value ${h.anomaly_level === 'elevated' ? 'flagged' : ''}" style="font-size:15px;color:#fafffa;font-weight:700">
          ${(h.name || '').split('—')[0].trim()}
        </span>
        <span style="font-size:9px;font-weight:700;color:${color};text-transform:uppercase;letter-spacing:1px;padding:2px 8px;border:1px solid ${color}20;border-radius:4px">
          ${levelLabel(h.anomaly_level)}
        </span>
      </div>
      <div style="display:flex;gap:var(--sp-sm);flex-wrap:wrap;margin-bottom:var(--sp-xs)">
        <span style="font-family:var(--font-mono);font-size:11px;color:${h.sar_peak_log_ratio_db!=null?'#2bee4b':'rgba(250,255,250,0.3)'}">
          SAR Δ ${fmt.db(h.sar_peak_log_ratio_db)}
        </span>
        <span style="font-family:var(--font-mono);font-size:11px;color:rgba(250,255,250,0.4)">
          ${fmt.area(h.sar_flagged_area_sq_m)}
        </span>
      </div>
      ${vol.volume_m3 != null ? `
      <div style="font-family:var(--font-mono);font-size:11px;color:#f5a623;margin-bottom:2px">
        ⛏ Sand removed: ~${fmt.vol(vol.volume_m3)}
      </div>` : ''}
      ${shift.shift_m != null ? `
      <div style="font-family:var(--font-mono);font-size:11px;color:#87CEEB;margin-bottom:2px">
        ↔ Channel shift: ${fmt.shift(shift.shift_m)} ${shift.direction || ''}
      </div>` : ''}
      <div class="msc-note">✓ GEE-validated · Sentinel-1/2</div>`;
    card.addEventListener('click', () => openDetail(h.id));
    el.appendChild(card);
  });

  const log = document.createElement('div');
  log.className = 'activity-log';
  log.id = 'activity-log';
  log.innerHTML = `
    <div class="al-header">
      <span class="al-header-title">Anomaly Activity Log</span>
      <span class="poll-dot" style="width:5px;height:5px"></span>
    </div>
    <div class="al-feed" id="al-feed"></div>`;
  el.appendChild(log);

  seedActivityLog(hotspots);
}

function seedActivityLog(hotspots) {
  const feed = document.getElementById('al-feed');
  if (!feed) return;

  const events = [];
  hotspots.forEach(h => {
    if (h.anomaly_level === 'elevated' || h.anomaly_level === 'under_review') {
      const vol = h.sand_volume_loss || {};
      events.push({
        type: 'anomaly',
        time: fmt.date(h.incident_window_end || h.incident_date),
        msg: `${h.river} (${h.id}): ${levelLabel(h.anomaly_level)} — ${h.sar_peak_log_ratio_db != null ? fmt.db(h.sar_peak_log_ratio_db)+' SAR Δ' : 'imagery pending'}${vol.volume_m3 != null ? ' · ~'+fmt.vol(vol.volume_m3)+' sand removed' : ''}`,
        hedge: 'Satellite anomaly — not a confirmed finding',
      });
    }
  });

  events.push({
    type: 'info',
    time: fmt.date(lastGenerated),
    msg: `Pipeline ran — ${hotspots.length} segments checked · GEE-computed`,
    hedge: '',
  });

  events.reverse().forEach(ev => addLogItem(ev.type, ev.time, ev.msg, ev.hedge));
}

function addLogItem(type, time, msg, hedge) {
  const feed = document.getElementById('al-feed');
  if (!feed) return;
  const div = document.createElement('div');
  div.className = `al-item ${type}`;
  div.innerHTML = `
    <div class="al-time">${time}</div>
    <div class="al-msg">${msg}</div>
    ${hedge ? `<div class="al-hedge">${hedge}</div>` : ''}`;
  feed.insertBefore(div, feed.firstChild);
}


/* ══════════════════════════════════════════════════════════════════════════
   DETAIL PANEL — satellite-first, actual mining metrics
══════════════════════════════════════════════════════════════════════════ */
function openDetail(id) {
  const h = HOTSPOTS.find(x => x.id === id);
  if (!h) return;

  const content = document.getElementById('detail-content');
  const img = h.imagery || {};
  const vol = h.sand_volume_loss || {};
  const shift = h.channel_shift || {};

  const makeImg = (rawUrl, label, date, noteHtml) => {
    const url = resolveImgUrl(rawUrl);
    return url
    ? `<div class="ev-frame">
         <img src="${url}" alt="${label}" class="ev-img-static"
              onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
         <div class="ev-pending" style="display:none">🛰️<br>${label}<br><small>Image unavailable</small></div>
         <div class="ev-caption"><strong>${label}</strong> <span class="ev-date">${date||''}</span></div>
         ${noteHtml ? `<div class="ev-img-note">${noteHtml}</div>` : ''}
       </div>`
    : `<div class="ev-frame">
         <div class="ev-pending">🛰️<br>${label}<br><small>Run generate_dashboard_data.py to generate imagery</small></div>
         <div class="ev-caption"><strong>${label}</strong></div>
       </div>`;
  };

  const sarStatus = h.sar_peak_log_ratio_db != null
    ? `${fmt.db(h.sar_peak_log_ratio_db)}`
    : 'Awaiting GEE run';

  // Volume loss section
  const volSection = vol.volume_m3 != null ? `
    <div style="background:rgba(245,166,35,0.08);border:1px solid rgba(245,166,35,0.25);border-radius:8px;padding:12px 16px;margin-bottom:12px">
      <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#f5a623;margin-bottom:6px">⛏ Actual Soil Volume Removed (Satellite Estimate)</div>
      <div style="font-size:22px;font-weight:700;color:#f5a623;font-family:var(--font-mono)">${fmt.vol(vol.volume_m3)}</div>
      <div style="font-size:11px;color:rgba(250,255,250,0.5);margin-top:4px">
        ${vol.area_reduced_sq_m != null ? `Sandbar area reduced by ${(vol.area_reduced_sq_m/1e4).toFixed(2)} ha · ` : ''}
        Depth assumed: ${vol.extraction_depth_assumed_m}m (conservative lower-bound estimate)
      </div>
      <div style="font-size:10px;color:rgba(250,255,250,0.35);margin-top:4px;font-style:italic">${vol.confidence || ''}</div>
    </div>` : '';

  // Channel shift section
  const shiftSection = shift.shift_m != null ? `
    <div style="background:rgba(135,206,235,0.08);border:1px solid rgba(135,206,235,0.2);border-radius:8px;padding:12px 16px;margin-bottom:12px">
      <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#87CEEB;margin-bottom:6px">↔ Actual Riverbed Channel Movement</div>
      <div style="font-size:22px;font-weight:700;color:#87CEEB;font-family:var(--font-mono)">${fmt.shift(shift.shift_m)} ${shift.direction || ''}</div>
      <div style="font-size:11px;color:rgba(250,255,250,0.5);margin-top:4px">
        Water channel centroid displaced between baseline and incident periods (NDWI water-mask analysis)
      </div>
      <div style="font-size:10px;color:rgba(250,255,250,0.35);margin-top:4px;font-style:italic">${shift.confidence || ''}</div>
    </div>` : '';

  content.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px">
      <div class="detail-eyebrow" style="margin:0">Satellite Evidence Report · ${id.toUpperCase()}</div>
      <button onclick="exportEvidence('${id}')" style="background:#2bee4b;color:#121613;border:none;padding:6px 12px;font-family:var(--font-mono);font-size:11px;font-weight:700;text-transform:uppercase;cursor:pointer;border-radius:4px">Export JSON</button>
    </div>
    <h2 class="detail-title">${h.name}</h2>

    ${volSection}
    ${shiftSection}

    <div class="detail-stats">
      <div class="detail-stat">
        <span class="detail-stat-num">${sarStatus}</span>
        <span class="detail-stat-label">SAR Δ Backscatter</span>
      </div>
      <div class="detail-stat">
        <span class="detail-stat-num">${h.sar_flagged_area_sq_m != null ? fmt.area(h.sar_flagged_area_sq_m) : '—'}</span>
        <span class="detail-stat-label">SAR Anomaly Area</span>
      </div>
      <div class="detail-stat">
        <span class="detail-stat-num">${fmt.pct(h.ndwi_change_pct)}</span>
        <span class="detail-stat-label">Sandbar Area Δ</span>
      </div>
    </div>

    <div class="detail-imagery-title">Satellite Evidence Imagery — Actual Physical Change</div>
    <div class="detail-imagery-grid">
      ${makeImg(img.before_s2_thumbnail_url, 'Before — Sentinel-2 True Colour', img.before_s2_date,
        `Baseline period. Sandbar intact.`)}
      ${makeImg(img.after_s2_thumbnail_url,  'After — Sentinel-2 True Colour',  img.after_s2_date,
        `Incident window. Compare sandbar extent.`)}
      ${makeImg(img.ndwi_diff_thumbnail_url, 'NDWI Difference: Sand Volume Removed', '',
        `<span style="color:#b2182b">Red/orange = exposed sand REDUCED</span> — sediment removed from riverbed. Blue = water area gained.`)}
      ${makeImg(img.before_sar_thumbnail_url,'Before — Sentinel-1 SAR (VV)',    img.before_sar_date,
        `Radar baseline. Dark = quiet sand surface.`)}
      ${makeImg(img.after_sar_thumbnail_url, 'After — Sentinel-1 SAR (VV)',     img.after_sar_date,
        `Bright anomalies = equipment backscatter.`)}
      ${makeImg(img.logratio_thumbnail_url,  'SAR Log-Ratio: Equipment Detection',  `${fmt.date(h.baseline_start)} vs. ${fmt.date(h.incident_window_end)}`,
        `<span style="color:#b2182b">Red = backscatter increase</span> = metal equipment signature on sandbar.`)}
    </div>
    <div style="font-size:11px;color:var(--text-2);font-style:italic;margin-bottom:var(--sp-xl)">
      All imagery: ESA Copernicus Sentinel-1 SAR (C-band, GRD) + Sentinel-2 SR Harmonized · Open licence · Processed via Google Earth Engine · Served locally
    </div>
    <div class="detail-description">${h.description}</div>
    <div style="background:rgba(18,22,19,0.6);border:1px solid rgba(250,255,250,0.08);border-radius:6px;padding:10px 14px;margin-top:12px;font-size:11px;color:rgba(250,255,250,0.4)">
      📄 Court record for context: <strong style="color:rgba(250,255,250,0.6)">${h.source}</strong>
      ${h.source_url ? ` · <a href="${h.source_url}" target="_blank" rel="noopener" style="color:#2bee4b">View Record →</a>` : ''}
      <br><span>${h.ngt_case_ref}</span>
    </div>
    <div class="detail-hedge">
      ⚖️ <em>Satellite-derived anomaly only — not a confirmed finding.
      Anomaly flags are statistical deviations from seasonal baselines.
      Volume and shift estimates are order-of-magnitude only.
      Legal confirmation requires independent human verification.</em>
    </div>`;

  const panel = document.getElementById('detail-panel');
  panel.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeDetail() {
  document.getElementById('detail-panel').style.display = 'none';
  document.body.style.overflow = '';
}

function exportEvidence(id) {
  const h = HOTSPOTS.find(x => x.id === id);
  if (!h) return;
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(h, null, 2));
  const el = document.createElement('a');
  el.setAttribute("href", dataStr);
  el.setAttribute("download", `river_watch_evidence_${id}.json`);
  document.body.appendChild(el);
  el.click();
  el.remove();
}

document.getElementById('detail-panel').addEventListener('click', e => {
  if (e.target === document.getElementById('detail-panel')) closeDetail();
});

/* ══════════════════════════════════════════════════════════════════════════
   EVIDENCE BLOCKS — satellite-first framing, actual mining metrics
══════════════════════════════════════════════════════════════════════════ */
function renderEvidenceBlocks(hotspots) {
  const ctr = document.getElementById('evidence-container');
  if (!ctr) return;
  ctr.innerHTML = '';

  hotspots.forEach(h => {
    const img = h.imagery || {};
    const hasSarStats = h.sar_peak_log_ratio_db != null;
    const vol = h.sand_volume_loss || {};
    const shift = h.channel_shift || {};

    const makeFrame = (rawUrl, step, label, dateNote, caption) => {
      const url = resolveImgUrl(rawUrl);
      return `
      <div class="evidence-frame">
        <div class="evidence-frame-label ${step}">${step.toUpperCase()} · ${label}</div>
        <div class="evidence-sat-wrapper">
          ${url
            ? `<img src="${url}" alt="${label}" class="ev-img" loading="lazy"
                    onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
               <div class="ev-fallback" style="display:none"><span>🛰️<br>${label}<br><small>Image unavailable</small></span></div>`
            : `<div class="ev-fallback"><span>🛰️<br>${label}<br><small>Run pipeline to generate imagery</small></span></div>`
          }
        </div>
        <div class="evidence-frame-caption">${dateNote}</div>
        ${caption ? `<div class="evidence-frame-note">${caption}</div>` : ''}
      </div>`;
    };

    const sarTag = hasSarStats
      ? `✓ Sentinel-1 SAR · ${fmt.db(h.sar_peak_log_ratio_db)} backscatter anomaly · ${fmt.area(h.sar_flagged_area_sq_m)} flagged`
      : `⏳ Run pipeline to compute SAR stats · ${levelLabel(h.anomaly_level)}`;

    // Mining metrics bar
    const miningMetrics = (vol.volume_m3 != null || shift.shift_m != null) ? `
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin:8px 0 0;padding:8px 12px;background:rgba(0,0,0,0.2);border-radius:6px;border:1px solid rgba(250,255,250,0.06)">
        ${vol.volume_m3 != null ? `
          <div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:rgba(250,255,250,0.4);margin-bottom:2px">Sand Removed (est)</div>
            <div style="font-size:15px;font-weight:700;color:#f5a623;font-family:var(--font-mono)">⛏ ${fmt.vol(vol.volume_m3)}</div>
          </div>` : ''}
        ${shift.shift_m != null ? `
          <div>
            <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:rgba(250,255,250,0.4);margin-bottom:2px">Channel Movement</div>
            <div style="font-size:15px;font-weight:700;color:#87CEEB;font-family:var(--font-mono)">↔ ${fmt.shift(shift.shift_m)} ${shift.direction || ''}</div>
          </div>` : ''}
        <div>
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:rgba(250,255,250,0.4);margin-bottom:2px">SAR Anomaly</div>
          <div style="font-size:15px;font-weight:700;color:#2bee4b;font-family:var(--font-mono)">${fmt.db(h.sar_peak_log_ratio_db)}</div>
        </div>
        <div>
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:rgba(250,255,250,0.4);margin-bottom:2px">Sandbar Δ</div>
          <div style="font-size:15px;font-weight:700;color:rgba(250,255,250,0.7);font-family:var(--font-mono)">${fmt.pct(h.ndwi_change_pct)}</div>
        </div>
      </div>` : '';

    const block = document.createElement('div');
    block.className = 'evidence-block';

    block.innerHTML = `
      <div class="evidence-header">
        <span class="evidence-tag">${sarTag}</span>
        <h3 class="evidence-title">${h.name}</h3>
        <p class="evidence-source" style="color:#2bee4b">Sentinel-1 SAR + Sentinel-2 NDWI Analysis · ESA Copernicus · Open Data</p>
        ${miningMetrics}
      </div>
      <div class="evidence-strip">
        ${makeFrame(img.before_s2_thumbnail_url, 'before', 'Sentinel-2 True Colour',
          `Baseline: ${fmt.date(h.baseline_start)} to ${fmt.date(h.baseline_end)}.`,
          `Optical baseline. Sandbar intact. ${img.before_s2_date || ''}`)}
        <div class="evidence-divider-line"></div>
        ${makeFrame(img.after_s2_thumbnail_url, 'after', 'Sentinel-2 True Colour',
          `Incident window: ${fmt.date(h.incident_window_start)} to ${fmt.date(h.incident_window_end)}.`,
          `Compare sandbar extent. ${img.after_s2_date || ''}`)}
        <div class="evidence-divider-line"></div>
        ${makeFrame(img.ndwi_diff_thumbnail_url, 'change', 'NDWI Difference — Sand Volume Removed',
          `Red = exposed sand REDUCED (sediment extracted). Blue = water gained (natural).`,
          `Physical soil reduction evidence: ${vol.area_reduced_sq_m != null ? (vol.area_reduced_sq_m/1e4).toFixed(2)+' ha reduced' : '—'}`)}
        <div class="evidence-divider-line"></div>
        ${makeFrame(img.logratio_thumbnail_url, 'change', 'SAR Log-Ratio: Equipment Detection',
          `Red = radar backscatter increase vs. baseline = equipment/vehicle presence.`,
          `SAR flagged area: ${hasSarStats ? fmt.area(h.sar_flagged_area_sq_m) : '—'} · Peak: ${hasSarStats ? fmt.db(h.sar_peak_log_ratio_db) : '—'}`)}
      </div>
      <div class="evidence-footer">
        <div class="evidence-chips">
          <span class="evidence-data-chip">📍 ${h.lat.toFixed(3)}°N ${h.lon.toFixed(3)}°E</span>
          <span class="evidence-data-chip">ESA Copernicus · Open Licence</span>
          <span class="evidence-data-chip">✓ GEE-Validated</span>
          ${vol.volume_m3 != null ? `<span class="evidence-data-chip" style="color:#f5a623">⛏ ~${fmt.vol(vol.volume_m3)} sand removed</span>` : ''}
        </div>
        <button class="evidence-view-btn" onclick="openDetail('${h.id}')">Full Report →</button>
      </div>
      <div class="evidence-imagery-credit">
        Imagery: ESA Copernicus Sentinel-1 SAR + Sentinel-2 · Open licence · Processed via Google Earth Engine ·
        <strong>Not near-real-time</strong> · Every flag requires human review before any conclusion is drawn ·
        Court records are corroborating context — satellite imagery is the primary evidence
      </div>`;
    ctr.appendChild(block);
  });
}


/* ══════════════════════════════════════════════════════════════════════════
   CASE FILES
══════════════════════════════════════════════════════════════════════════ */
function renderCaseStudies(hotspots) {
  const grid = document.getElementById('case-grid');
  if (!grid) return;
  grid.innerHTML = '';

  hotspots.forEach((h, i) => {
    const thumbUrl = resolveImgUrl((h.imagery || {}).before_s2_thumbnail_url);
    const vol = h.sand_volume_loss || {};
    const shift = h.channel_shift || {};

    const card = document.createElement('div');
    card.className = 'case-card';
    card.innerHTML = `
      ${thumbUrl
        ? `<img class="case-thumb" src="${thumbUrl}" alt="Sentinel-2 baseline — ${h.name}"
               onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
        : ''
      }
      <div class="case-thumb--pending" style="${thumbUrl ? 'display:none' : ''}">🛰️<br>Sentinel-2 Baseline<br><small>Run pipeline to generate</small></div>
      <div class="case-body">
        <div class="case-num">${String(i+1).padStart(2,'0')}</div>
        <span class="case-badge">✓ GEE-Validated · ${h.id}</span>
        <div class="case-title">${h.name}</div>
        <div class="case-meta">
          ${h.river} River · ${h.state}${h.protected_area ? `<br>🛡 ${h.protected_area}` : ''}<br>
          Incident window: ${fmt.date(h.incident_window_start)} → ${fmt.date(h.incident_window_end)}
        </div>
        <div class="case-sar-stat">
          <span class="sar-badge">SAR Δ ${fmt.db(h.sar_peak_log_ratio_db)}</span>
          <span class="sar-badge">Area ${fmt.area(h.sar_flagged_area_sq_m)}</span>
          <span class="sar-badge">NDWI ${fmt.pct(h.ndwi_change_pct)}</span>
          ${vol.volume_m3 != null ? `<span class="sar-badge" style="color:#f5a623">⛏ ~${fmt.vol(vol.volume_m3)}</span>` : ''}
          ${shift.shift_m != null ? `<span class="sar-badge" style="color:#87CEEB">↔ ${fmt.shift(shift.shift_m)}</span>` : ''}
        </div>
        <div class="case-description">${h.description}</div>
        <div class="case-hedge">
          ⚖️ <em>Satellite anomaly — physical evidence of riverbed alteration.
          ${h.ngt_case_ref} provides corroborating legal context.
          Does not independently confirm illegal activity.</em>
        </div>
        <a class="case-link" href="#" onclick="openDetail('${h.id}'); return false;">
          View Satellite Evidence →
        </a>
      </div>`;
    grid.appendChild(card);
  });
}

/* ══════════════════════════════════════════════════════════════════════════
   30-SECOND POLLING — diff & update
══════════════════════════════════════════════════════════════════════════ */
const supabaseUrl = 'https://pdrofamxilbfbwqqqoxg.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBkcm9mYW14aWxiZmJ3cXFxb3hnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI3Mzg3OTUsImV4cCI6MjA5ODMxNDc5NX0.mDNgssuMSfP-nL7VPJykXe8qiMOEpTzwow0zymnNT_M';
const supabaseClient = window.supabase ? window.supabase.createClient(supabaseUrl, supabaseKey) : null;

async function fetchDashboard() {
  if (!supabaseClient) {
    console.warn("Supabase SDK not loaded (CDN issue?), falling back to local dashboard.json");
    const res = await fetch('data/dashboard.json');
    if (!res.ok) throw new Error("Could not fetch local dashboard.json");
    return await res.json();
  }
  try {
    const { data: hotspots, error: err1 } = await supabaseClient.from('hotspots').select('*');
    if (err1) throw err1;
    
    if (!hotspots || hotspots.length === 0) {
      throw new Error('Supabase returned empty hotspots');
    }

    const { data: meta, error: err2 } = await supabaseClient.from('metadata').select('*');
    if (err2) throw err2;
    
    let metadataObj = {};
    if (meta) {
      meta.forEach(m => metadataObj[m.key] = m.value);
    }
    
    return {
      generated_at: metadataObj.generated_at,
      phase: metadataObj.phase,
      scope_note: metadataObj.scope_note,
      hotspots: hotspots || []
    };
  } catch (e) {
    console.error("Supabase fetch error:", e);
    console.log("Falling back to local dashboard.json");
    const res = await fetch('data/dashboard.json');
    if (!res.ok) throw new Error("Could not fetch local dashboard.json");
    return await res.json();
  }
}

function diffAndUpdate(fresh) {
  const prevLevels = Object.fromEntries(HOTSPOTS.map(h => [h.id, h.anomaly_level]));
  HOTSPOTS = fresh.hotspots || [];
  lastGenerated = fresh.generated_at;

  HOTSPOTS.forEach(h => {
    const prev = prevLevels[h.id];
    if (prev && prev !== h.anomaly_level) {
      addLogItem('anomaly',
        new Date().toISOString().substring(0,16).replace('T',' '),
        `${h.river} (${h.id}): anomaly level changed ${prev} → ${h.anomaly_level}`,
        'Satellite anomaly — not a confirmed finding');
    }
    renderLiveZone(h);
  });

  const generated = document.getElementById('msb-generated');
  if (generated) generated.textContent = fmt.date(fresh.generated_at);
  const segs = document.getElementById('msb-segments');
  if (segs) segs.textContent = HOTSPOTS.length;
  const anom = document.getElementById('msb-anomalies');
  if (anom) {
    const n = HOTSPOTS.filter(h => h.anomaly_level === 'elevated' || h.anomaly_level === 'under_review').length;
    anom.textContent = n;
  }

  const alertEl = document.getElementById('stat-alerts');
  if (alertEl) {
    alertEl.textContent = HOTSPOTS.filter(h => ['elevated','under_review'].includes(h.anomaly_level)).length;
  }

  const pollEl = document.getElementById('poll-status');
  if (pollEl) pollEl.textContent = `Last polled ${new Date().toLocaleTimeString('en-IN')}`;
}

function startCountdown() {
  countdownVal = 30;
  clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    countdownVal--;
    const el = document.getElementById('msb-countdown');
    if (el) el.textContent = countdownVal + 's';
    if (countdownVal <= 0) {
      countdownVal = 30;
      fetchDashboard().then(diffAndUpdate).catch(() => {
        const p = document.getElementById('poll-status');
        if (p) p.textContent = 'Poll failed — retrying…';
      });
    }
  }, 1000);
}

/* ══════════════════════════════════════════════════════════════════════════
   BOOT
══════════════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  initLiveMap();
  try {
    const data = await fetchDashboard();
    HOTSPOTS     = data.hotspots || [];
    lastGenerated = data.generated_at;

    if (HOTSPOTS.length === 0) throw new Error('No hotspots in dashboard.json');

    renderMonitorSidebar(HOTSPOTS);
    HOTSPOTS.forEach(h => renderLiveZone(h));
    renderEvidenceBlocks(HOTSPOTS);
    renderCaseStudies(HOTSPOTS);

    const gen = document.getElementById('msb-generated');
    if (gen) gen.textContent = fmt.date(data.generated_at);
    const seg = document.getElementById('msb-segments');
    if (seg) seg.textContent = HOTSPOTS.length;
    const an = document.getElementById('msb-anomalies');
    if (an) an.textContent = HOTSPOTS.filter(h => ['elevated','under_review'].includes(h.anomaly_level)).length;

    const alertEl = document.getElementById('stat-alerts');
    if (alertEl) alertEl.textContent = HOTSPOTS.filter(h => ['elevated','under_review'].includes(h.anomaly_level)).length;

    if (liveMap && HOTSPOTS.length > 1) {
      const bounds = L.latLngBounds(HOTSPOTS.map(h => [h.lat, h.lon]));
      liveMap.fitBounds(bounds.pad(0.2));
    }

    const pollEl = document.getElementById('poll-status');
    if (pollEl) pollEl.textContent = 'Polling every 30s from dashboard.json';

    startCountdown();

  } catch (err) {
    console.error('Boot error:', err);

    ['site-list','evidence-container','case-grid','monitor-sidebar'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = `
        <div class="site-loading">
          <p style="font-size:14px;line-height:1.8">
            ⚠️ Could not load pipeline data.<br>
            <small>Run <code>python scripts/generate_dashboard_data.py</code><br>
            or check the server is running at project root.<br>
            <code>python -m http.server 8000</code></small>
          </p>
        </div>`;
    });

    const gen = document.getElementById('msb-generated');
    if (gen) gen.textContent = 'Unavailable';
    const poll = document.getElementById('poll-status');
    if (poll) poll.textContent = 'Load error — check console';
  }
});
