// Personality gallery — standalone plugin UI (left-pane iframe).
// Browse sci-fi AI personalities; apply one by writing the owner's identity via
// core's PUT /api/p/plugin-identity/. Auth token arrives via postMessage from
// the shell (same handshake as the Marketplace/Interview panes).

const API = '/api/p/personality-template';
const IDENTITY_API = '/api/p/plugin-identity';
const PERSONALITY_FIELDS = ['persona', 'tone', 'verbosity', 'formality', 'use_emoji', 'proactive', 'honesty_mode'];
const GROUPS = [
  { key: 'strict', label: 'Strict — exacting & relentless' },
  { key: 'balanced', label: 'Balanced — capable & composed' },
  { key: 'warm', label: 'Warm — supportive & kind' },
];

let TOKEN = '';
let booted = false;
let CATALOG = null;        // { personalities, allowed_values, default }
let IDENTITY = null;       // current identity snapshot
let selected = null;       // currently previewed personality card

window.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'luna-auth') {
    TOKEN = e.data.token;
    if (!booted) { booted = true; boot(); }
  }
});
setTimeout(() => {
  if (!TOKEN) {
    TOKEN = localStorage.getItem('luna.token') || '';
    if (!booted) { booted = true; boot(); }
  }
}, 400);

const el = (id) => document.getElementById(id);
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function showError(m) {
  const e = el('error');
  if (m) { e.textContent = m; e.classList.remove('hidden'); }
  else { e.classList.add('hidden'); }
}
let toastTimer = null;
function toast(msg, kind) {
  const t = el('toast');
  t.textContent = msg;
  t.className = `toast ${kind || ''}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add('hidden'), 2600);
}

async function req(method, base, path, body) {
  const init = { method, headers: { Authorization: `Bearer ${TOKEN}` } };
  if (body !== undefined) {
    init.headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }
  const res = await fetch(`${base}${path}`, init);
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try { const j = await res.json(); if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail); } catch {}
    throw new Error(msg);
  }
  return res.status === 204 ? null : res.json();
}

async function boot() {
  showError(null);
  try {
    [CATALOG, IDENTITY] = await Promise.all([
      req('GET', API, '/catalog'),
      req('GET', IDENTITY_API, '/'),
    ]);
  } catch (e) {
    el('loading').classList.add('hidden');
    showError(`Could not load: ${e.message}`);
    return;
  }
  el('loading').classList.add('hidden');
  el('gallery').classList.remove('hidden');
  render();
}

// Build a flat field map for a personality card (persona + knobs).
// `apply_persona` is the composed, in-character persona (names the character,
// folds in catchphrase + GIF guidance); fall back to the plain persona.
function cardFields(p) {
  return { persona: p.apply_persona || p.persona, ...(p.knobs || {}) };
}

function render() {
  const g = el('gallery');
  g.innerHTML = '';
  for (const grp of GROUPS) {
    const items = CATALOG.personalities.filter((p) => p.strictness === grp.key);
    if (!items.length) continue;
    const h = document.createElement('div');
    h.className = 'group-title';
    h.textContent = grp.label;
    g.appendChild(h);
    const grid = document.createElement('div');
    grid.className = 'grid';
    for (const p of items) grid.appendChild(cardEl(p));
    g.appendChild(grid);
  }
}

// Horizontal card: large avatar on the left (full height), details to the right.
// No "active" state — applying just copies the personality's details into Luna's
// identity, which the user can freely edit afterwards.
function cardEl(p) {
  const card = document.createElement('button');
  card.className = 'card';
  card.setAttribute('data-testid', 'personality-card');
  card.setAttribute('data-id', p.id);
  const knobs = p.knobs || {};
  const chips = [knobs.tone, knobs.verbosity, knobs.honesty_mode]
    .filter(Boolean).map((c) => `<span class="chip">${esc(c)}</span>`).join('');
  card.innerHTML =
    `<img class="avatar" src="${esc(p.avatar)}" alt="" loading="lazy" />` +
    `<div class="info">` +
      `<div class="name">${esc(p.name)} <span class="name-emoji">${esc(p.emoji)}</span></div>` +
      `<div class="source">${esc(p.source)}</div>` +
      `<div class="tagline">${esc(p.tagline)}</div>` +
      `<div class="chips">${chips}${p.novelty ? '<span class="chip tag-novelty">novelty</span>' : ''}</div>` +
    `</div>`;
  card.addEventListener('click', () => openDrawer(p));
  return card;
}

// ---- Drawer / preview ----

function openDrawer(p) {
  selected = p;
  el('d-avatar').src = p.avatar;
  el('d-name').textContent = `${p.name} ${p.emoji}`;
  el('d-source').textContent = p.source;
  el('d-archetype').textContent = p.archetype;
  const knobs = p.knobs || {};
  el('d-voice').textContent = ['tone', 'verbosity', 'formality', 'proactive', 'honesty_mode', 'use_emoji']
    .map((k) => knobs[k]).filter(Boolean).join(' · ');
  el('d-novelty').classList.toggle('hidden', !p.novelty);
  el('d-sample').textContent = p.sample_reply;
  el('d-persona').textContent = p.persona;

  // Signature lines (catchphrases) + GIF vibes — flavor that makes it in-character.
  const phrases = p.catchphrases || [];
  el('d-phrases-block').classList.toggle('hidden', !phrases.length);
  el('d-phrases').innerHTML = phrases
    .map((c) => `<span class="phrase">${esc(c)}</span>`).join('');
  const gifs = p.gif_terms || [];
  el('d-gif-block').classList.toggle('hidden', !gifs.length);
  el('d-gifs').innerHTML = gifs
    .map((t) => `<span class="chip gif-chip">${esc(t)}</span>`).join('');

  // diff
  const want = { ...cardFields(p), emoji: p.emoji };
  const rows = [];
  for (const [f, v] of Object.entries(want)) {
    const cur = IDENTITY[f];
    if (String(cur || '') !== String(v || '')) {
      rows.push({ f, from: cur, to: v });
    }
  }
  const diff = el('d-diff');
  if (!rows.length) {
    diff.innerHTML = '<div class="diff-none">No change — this is your current voice.</div>';
  } else {
    diff.innerHTML = rows.map((r) => {
      const from = r.f === 'persona' ? '(custom persona)' : (r.from || '—');
      const to = r.f === 'persona' ? '(new persona)' : r.to;
      return `<div class="diff-row"><span class="f">${esc(r.f)}</span>` +
        `<span class="from">${esc(from)}</span><span class="arrow">→</span>` +
        `<span class="to">${esc(to)}</span></div>`;
    }).join('');
  }
  el('apply-btn').textContent = `Copy ${p.name}'s voice to Luna`;
  el('apply-btn').disabled = false;
  el('drawer').classList.remove('hidden');
}

function closeDrawer() {
  el('drawer').classList.add('hidden');
  selected = null;
}

async function applySelected() {
  if (!selected) return;
  const name = selected.name;
  const body = { ...cardFields(selected), emoji: selected.emoji };
  const btn = el('apply-btn');
  btn.disabled = true;
  try {
    IDENTITY = await req('PUT', IDENTITY_API, '/', body);
    notifyIdentityChanged();
    btn.textContent = 'Details copied ✓';
    toast(`${name}'s details copied to Luna — edit anytime in Settings`, 'ok');
    setTimeout(closeDrawer, 700);
  } catch (e) {
    toast(`Failed: ${e.message}`, 'err');
    btn.disabled = false;
  }
}

async function resetDefault() {
  if (!CATALOG) return;
  if (!confirm("Restore Luna's default voice?")) return;
  const body = { ...CATALOG.default };
  try {
    IDENTITY = await req('PUT', IDENTITY_API, '/', body);
    toast('Restored default Luna', 'ok');
    notifyIdentityChanged();
    render();
  } catch (e) {
    toast(`Failed: ${e.message}`, 'err');
  }
}

function notifyIdentityChanged() {
  try { parent.postMessage({ type: 'luna-identity-changed' }, '*'); } catch {}
}

el('refresh-btn').addEventListener('click', boot);
el('reset-btn').addEventListener('click', resetDefault);
el('drawer-close').addEventListener('click', closeDrawer);
el('drawer-backdrop').addEventListener('click', closeDrawer);
el('cancel-btn').addEventListener('click', closeDrawer);
el('apply-btn').addEventListener('click', applySelected);
