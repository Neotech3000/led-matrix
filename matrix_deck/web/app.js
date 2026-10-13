const WIDTH = 9;
const HEIGHT = 34;
const PIXELS = WIDTH * HEIGHT;
const DEFAULT_BRIGHTNESS = 180;
const DEFAULT_SPEED = 100;
const HINT_KEY = "ledmatrix.firstRunHint.v1";
const IGNORE_KEYS = new Set([
  "ShiftLeft",
  "ShiftRight",
  "ControlLeft",
  "ControlRight",
  "AltLeft",
  "AltRight",
  "MetaLeft",
  "MetaRight",
  "Tab",
  "CapsLock",
  "NumLock",
  "ScrollLock",
]);

const GAME_HINTS = {
  flappy: "click, space, or ↑ to flap",
  snake: "tap a side of the well, or arrows / WASD",
  pong: "you are the bright bottom paddle · drag or ← →",
  breakout: "click, drag, or arrows",
  dodge: "click, drag, or arrows",
  tetris: "arrows or WASD · live score at the top",
  invaders: "← → move · space shoots",
  dino: "click, Space, or ↑ to jump",
  frogger: "tap or ↑ hop · ← → dodge traffic",
  asteroids: "← → rotate · ↑ thrust · space shoot",
  centipede: "drag or A/D · space / click to shoot",
  "space-shooter": "← → or drag · space to fire",
  "brick-stack": "click or space to drop the bar",
  catcher: "drag or ← → to catch falling bits",
  whack: "tap bright moles before they hide",
  slither: "tap a side or arrows · wrap, rocks kill",
  racetrack: "drag or ← → and stay on the road",
  jumper: "space / click to hop · ← → drift",
  sokoban: "arrows push the crate onto the goal",
  minesweeper: "click reveal · shift-click flag",
  memory: "click a card, then its matching glyph",
  "lights-out": "click a cell to toggle neighbors",
  2048: "arrows or swipe to slide tiles",
  connect4: "click a column or ← → then space",
  simon: "click the quadrant that just lit · Q W A S or 1–4",
  rhythm: "hit notes on the line · space / click lane",
  cannons: "tap to burst incoming missiles",
  "pinball-game": "drag or space to kick the flipper",
  maze: "arrows or tap · a new maze each round",
};

const UTILITY_KEYS = {
  timer: "click/space start-pause · ↑↓ or +/− add 30s · C/R reset to 60s",
  pomodoro: "click/space start-pause · C/R reset · 25 then 5",
  stopwatch: "click/space start-pause · C/R zero",
  "tap-tempo": "tap or space · C resets",
  dice: "click or space to roll",
  "coin-flip": "click or space to toss",
  progress: "click +5 · ↑↓ · C zeros",
  "chess-clock": "click/space punch · C/R reset",
  "water-reminder": "click logs a sip · ↑↓ interval",
  "focus-bar": "click start · ↑↓ length · C/R reset",
  life: "drag paints · Shift-drag erases · R reseeds · P pauses",
  sketch: "drag draws one LED at a time · Shift-drag erases · C clears",
  sand: "drag pours sand · Shift-drag erases · C clears",
  marquee: "type in the box under the well",
};

const GLOBAL_KEYS = [
  ["1", "Send keys to the left well"],
  ["2", "Send keys to the right well"],
  ["F", "Favorite or unfavorite what the focused well is playing"],
  ["?", "Open or close this sheet"],
  ["Esc", "Close this sheet, leave selection mode, or clear search"],
  ["Tab / Enter", "In search: Tab fills the best match, Enter plays it on the focused well"],
  ["Enter / Space", "On a card: play it on the focused well"],
  ["Space · arrows · WASD", "Always go to the focused well (games, timers, drawing) — even while a card or button has focus"],
];

// Keys a focused button or card keeps for itself. Everything else goes to the focused well.
const CONTROL_KEYS = new Set(["Enter", "Space", "NumpadEnter"]);

const leftCanvas = document.getElementById("left");
const rightCanvas = document.getElementById("right");
const leftBezel = document.getElementById("left-bezel");
const rightBezel = document.getElementById("right-bezel");
const leftCtx = leftCanvas.getContext("2d", { alpha: false });
const rightCtx = rightCanvas.getContext("2d", { alpha: false });
const leftPill = document.getElementById("left-pill");
const rightPill = document.getElementById("right-pill");
const leftName = document.getElementById("left-name");
const rightName = document.getElementById("right-name");
const leftHud = document.getElementById("left-hud");
const rightHud = document.getElementById("right-hud");
const brightnessEl = document.getElementById("brightness");
const speedEl = document.getElementById("speed");
const brightnessValue = document.getElementById("brightness-value");
const speedValue = document.getElementById("speed-value");
const randomBtn = document.getElementById("random-btn");
const helpBtn = document.getElementById("help-btn");
const helpSheet = document.getElementById("help-sheet");
const helpBody = document.getElementById("help-body");
const helpClose = document.getElementById("help-close");
const firstRun = document.getElementById("first-run");
const hintDismiss = document.getElementById("hint-dismiss");
const toastsEl = document.getElementById("toasts");
const searchEl = document.getElementById("search");
const searchGhost = document.getElementById("search-ghost");
const searchFill = document.getElementById("search-fill");
const typeFilters = document.getElementById("type-filters");
const groupsEl = document.getElementById("groups");
const libraryLeft = document.getElementById("library-left");
const libraryRight = document.getElementById("library-right");
const railLeftLabel = document.getElementById("rail-left-label");
const railRightLabel = document.getElementById("rail-right-label");
const railRight = document.querySelector(".rail-right");
const leftText = document.getElementById("left-text");
const rightText = document.getElementById("right-text");
const leftMarquee = document.getElementById("left-marquee");
const rightMarquee = document.getElementById("right-marquee");
const scenesEl = document.getElementById("scenes");
const idleBtn = document.getElementById("idle-btn");
const idleMinutesEl = document.getElementById("idle-minutes");

let scenes = [];
let activeScene = null;
let scenesStatus = "loading";
let confirmDeleteScene = "";
let lastSceneUiKey = "";
let idleState = { enabled: false, minutes: 10, dimmed: false, effective: 180 };
const narrowQuery = window.matchMedia("(max-width: 980px)");

let catalog = [];
let catalogRev = "";
let catalogLoading = null;
let searchQuery = "";
let kindFilter = "";
let favorites = new Set();
let groups = [];
let activeGroup = "";
let selectionGroup = "";
let confirmDeleteGroup = "";
let groupsStatus = "loading";
let randomGroup = null;
let lastGroupUiKey = "";
let focus = "left";
let drawing = null;
let inputQueue = Promise.resolve();
let lastLibKey = "";
let narrow = narrowQuery.matches;
let offline = false;
let lastReturnFocus = null;
const pendingAnim = { left: null, right: null };
let state = {
  left_anim: "flappy",
  right_anim: "fishtank",
  info: { left: {}, right: {} },
};
const lastPixels = {
  left: new Array(PIXELS).fill(0),
  right: new Array(PIXELS).fill(0),
};
const THEME_CSS = {
  accent: "--accent",
  ink: "--ink",
  muted: "--muted",
  surface: "--panel",
  border: "--line",
};
let themeRev = "";
const overlay = {
  left: new Uint8Array(PIXELS),
  right: new Uint8Array(PIXELS),
};
const overlayOn = {
  left: new Uint8Array(PIXELS),
  right: new Uint8Array(PIXELS),
};

function applyTheme(data) {
  if (!data || !data.colors) return;
  const root = document.documentElement;
  const colors = data.colors;
  for (const [key, cssVar] of Object.entries(THEME_CSS)) {
    if (typeof colors[key] === "string" && colors[key]) {
      root.style.setProperty(cssVar, colors[key]);
    }
  }
  if (colors.accent) {
    root.style.setProperty("--orange", colors.accent);
  }
  if (typeof colors.success === "string" && colors.success) {
    root.style.setProperty("--success", colors.success);
  }
  // Theme wallpaper / background never paints the page. --bg stays black.
  root.style.setProperty("--bg", "#000");
  if (data.source) root.dataset.themeSource = data.source;
  if (data.name) root.dataset.themeName = data.name;
  if (data.rev) themeRev = data.rev;
}

async function refreshTheme(force) {
  try {
    const res = await fetch("/api/theme", { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    if (!force && data.rev && data.rev === themeRev) return;
    applyTheme(data);
  } catch {
    /* keep the CSS fallback palette */
  }
}

function canvasSize(canvas) {
  const cssW = canvas.clientWidth || 126;
  const cssH = canvas.clientHeight || Math.round(cssW * (HEIGHT / WIDTH) * 0.92);
  return { cssW, cssH };
}

function drawMatrix(ctx, canvas, pixels) {
  const dpr = window.devicePixelRatio || 1;
  const { cssW, cssH } = canvasSize(canvas);
  if (canvas.width !== Math.floor(cssW * dpr) || canvas.height !== Math.floor(cssH * dpr)) {
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);
  ctx.fillStyle = "#07080a";
  ctx.fillRect(0, 0, cssW, cssH);

  const pad = 8;
  const gap = 3;
  const usableW = cssW - pad * 2;
  const usableH = cssH - pad * 2;
  const cellW = (usableW - gap * (WIDTH - 1)) / WIDTH;
  const cellH = (usableH - gap * (HEIGHT - 1)) / HEIGHT;
  const led = Math.min(cellW, cellH) * 0.42;

  for (let y = 0; y < HEIGHT; y++) {
    for (let x = 0; x < WIDTH; x++) {
      const v = (pixels[y * WIDTH + x] || 0) / 255;
      const cx = pad + x * (cellW + gap) + cellW / 2;
      const cy = pad + y * (cellH + gap) + cellH / 2;
      ctx.beginPath();
      ctx.arc(cx, cy, led * 1.05, 0, Math.PI * 2);
      ctx.fillStyle = "#14161c";
      ctx.fill();
      if (v < 0.02) continue;
      const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, led * 3.2);
      glow.addColorStop(0, `rgba(255, 244, 208, ${0.18 + v * 0.55})`);
      glow.addColorStop(0.45, `rgba(255, 186, 92, ${v * 0.22})`);
      glow.addColorStop(1, "rgba(255, 116, 79, 0)");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, led * 3.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx, cy, led, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 248, 230, ${0.25 + v * 0.75})`;
      ctx.fill();
    }
  }
}

function pill(el, side, value) {
  const live = value && !["simulated", "disconnected", "error"].includes(value);
  el.classList.toggle("live", !!live);
  const short = String(value || "simulated").replace(/^.*\//, "");
  el.textContent = `${side} · ${short}`;
}

function catalogItem(id) {
  return catalog.find((c) => c.id === id) || null;
}

function animName(id) {
  const item = catalogItem(id);
  return item ? item.name : String(id || "");
}

function sideLabel(side) {
  return side === "right" ? "Right" : "Left";
}

function utilityHint(id, info) {
  const UTILITY_HINTS = {
    timer: `${info.running ? "RUN" : info.done ? "DONE" : "PAUSE"} ${info.remaining || "01:00"} · ${UTILITY_KEYS.timer}`,
    pomodoro: `${(info.phase || "work").toUpperCase()} ${info.remaining || ""} · ${UTILITY_KEYS.pomodoro}`,
    stopwatch: `${info.running ? "RUN" : "PAUSE"} ${info.elapsed || "00:00"} · ${UTILITY_KEYS.stopwatch}`,
    utc: `UTC ${info.time || ""} · same stacked digits as Clock`,
    date: `${info.weekday || ""} ${info.date || ""}`,
    "week-number": `ISO week ${info.week ?? ""} · ${info.year ?? ""}`,
    "fuzzy-clock": info.words ? `${info.words} · ${info.time || ""}` : "Time in words, nearest five minutes",
    "binary-clock": `Binary ${info.time || ""} · H M S as bit columns`,
    "seconds-bar": `Second ${info.second ?? ""} · column fills through the minute`,
    alarm: `${info.time || ""} · lights up at :00 of each minute`,
    "tap-tempo": `${info.bpm || 0} BPM · ${UTILITY_KEYS["tap-tempo"]}`,
    "battery-bar": `${info.percent ?? "?"} percent${info.live ? "" : " (simulated)"}`,
    "cpu-pulse": `Load ${info.load ?? "sim"} · nine bars`,
    "moon-phase": `${info.phase || ""} · real synodic phase`,
    dice: `Rolled ${info.value ?? 6} · ${UTILITY_KEYS.dice}`,
    "coin-flip": `${info.side || "heads"} · ${UTILITY_KEYS["coin-flip"]}`,
    progress: `${info.percent ?? 0} percent · ${UTILITY_KEYS.progress}`,
    "chess-clock": `${info.white || "05:00"} / ${info.black || "05:00"} · ${info.active || "white"} · ${UTILITY_KEYS["chess-clock"]}`,
    "breath-pacer": `${info.phase || "IN"} · box breathing 4-4-4-4 on the wall clock`,
    "water-reminder": info.due ? "SIP · click when you drank" : `${info.remaining || ""} until a sip · ${UTILITY_KEYS["water-reminder"]}`,
    "focus-bar": `${info.running ? "RUN" : "PAUSE"} ${info.remaining || ""} of ${info.duration_min ?? 50} min · ${UTILITY_KEYS["focus-bar"]}`,
  };
  return UTILITY_HINTS[id] || "";
}

function hudText(side, data) {
  const id = data[`${side}_anim`];
  const info = (data.info && data.info[side]) || {};
  const item = catalogItem(id);
  if (id === "flappy") {
    const pilot = info.alive ? (info.auto ? "AUTO" : "YOU") : "CRASH";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · ${GAME_HINTS.flappy}`;
  }
  if (id === "snake") {
    const pilot = info.alive ? (info.auto ? "AUTO until you steer" : "YOU") : "DEAD";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · ${GAME_HINTS.snake}`;
  }
  if (id === "pong") {
    const pilot = info.auto ? "AUTO" : "YOU";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · ${GAME_HINTS.pong}`;
  }
  if (id === "dino") {
    const pilot = info.alive ? (info.auto ? "AUTO" : "YOU") : "HIT";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · ${GAME_HINTS.dino}`;
  }
  if (GAME_HINTS[id]) {
    const dead = info.alive === false;
    const pilot = dead ? "DEAD" : info.auto ? "AUTO" : "YOU";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · ${GAME_HINTS[id]}`;
  }
  if (id === "life") {
    const mode = info.paused ? "PAUSED" : "LIVE";
    return `Gen ${info.gen ?? 0} · ${mode} · drag to paint, Shift-drag erases, R reseeds, P pauses`;
  }
  if (id === "sketch") {
    return "Drag on this well to draw one LED at a time. Shift-drag erases. C clears.";
  }
  if (id === "sand") {
    return "Drag to pour sand. Shift-drag erases. C clears.";
  }
  if (id === "marquee") {
    return "Type in the box under this well. Words enter at the top and loop down forever.";
  }
  if (id === "ecg") {
    return "A scrolling EKG trace — P wave, QRS spike, T wave. No heart icon.";
  }
  if (id === "hearts") {
    return "Hearts falling down the well.";
  }
  if (id === "clock") {
    return `Local time ${info.time || ""}`.trim() + " · hours, minutes, then seconds.";
  }
  const utility = utilityHint(id, info);
  if (utility) return utility;
  return item ? item.description : "";
}

function toast(text, { kind = "", duration = 1500 } = {}) {
  if (!toastsEl || !text) return;
  const el = document.createElement("div");
  el.className = kind ? `toast ${kind}` : "toast";
  el.setAttribute("role", "status");
  el.textContent = text;
  toastsEl.appendChild(el);
  while (toastsEl.children.length > 3) toastsEl.firstElementChild.remove();
  requestAnimationFrame(() => el.classList.add("show"));
  window.setTimeout(() => {
    el.classList.remove("show");
    window.setTimeout(() => el.remove(), 360);
  }, duration);
}

function setFocus(side, { rebuild = true } = {}) {
  focus = side;
  document.querySelectorAll(".module").forEach((mod) => {
    mod.classList.toggle("focused", mod.dataset.side === side);
  });
  updateRailLabels();
  if (rebuild) {
    lastLibKey = "";
    maybeRenderLibrary();
  }
}

// Move DOM focus onto a well's bezel so a card or button that was just clicked
// stops being the key target; the game on that well gets the keyboard.
function focusWell(side) {
  const bezel = side === "right" ? rightBezel : leftBezel;
  if (!bezel || document.activeElement === bezel) return;
  try {
    bezel.focus({ preventScroll: true });
  } catch {
    bezel.focus();
  }
}

function updateRailLabels() {
  if (railLeftLabel) {
    railLeftLabel.textContent = narrow ? `Library · tap sends to ${sideLabel(focus)}` : "Left well · first half · click plays here";
  }
  if (railRightLabel) railRightLabel.textContent = "Right well · second half · click plays here";
  if (railRight) railRight.hidden = narrow;
}

function activeGroupRecord() {
  return groups.find((item) => item.id === activeGroup) || null;
}

function groupIds(group) {
  return group && Array.isArray(group.ids) ? group.ids : [];
}

function mergeGroups(serverGroups) {
  if (!Array.isArray(serverGroups)) return;
  groups = serverGroups.map((group) => ({
    id: group.id,
    name: group.name,
    ids: Array.isArray(group.ids) ? group.ids.slice() : [],
  }));
  if (groupsStatus !== "ready") groupsStatus = "ready";
  if (activeGroup && !groups.some((group) => group.id === activeGroup)) {
    activeGroup = "";
  }
  if (selectionGroup && !groups.some((group) => group.id === selectionGroup)) {
    selectionGroup = "";
  }
  if (confirmDeleteGroup && !groups.some((group) => group.id === confirmDeleteGroup)) {
    confirmDeleteGroup = "";
  }
  if (renamingGroup && !groups.some((group) => group.id === renamingGroup)) {
    renamingGroup = "";
  }
}

function maybeRenderLibrary() {
  const favKey = [...favorites].sort().join(",");
  const groupKey = groups.map((group) => `${group.id}:${group.name}:${(group.ids || []).join("+")}`).join(";");
  const key = `${state.left_anim}|${state.right_anim}|${focus}|${narrow}|${searchQuery}|${kindFilter}|${activeGroup}|${selectionGroup}|${favKey}|${groupKey}|${groupsStatus}|${catalogRev}|${catalog.length}`;
  if (key === lastLibKey) return;
  lastLibKey = key;
  document.body.classList.toggle("filing", !!selectionGroup);
  document.body.classList.toggle("selecting", !!selectionGroup);
  renderLibrary();
  maybeRenderGroups();
}

function kindLabel(kind) {
  if (kind === "game") return "Game";
  if (kind === "sketch") return "Draw";
  if (kind === "utility") return "Utility";
  if (kind === "weather") return "Weather";
  if (kind === "music") return "Music";
  if (kind === "puzzle") return "Puzzle";
  if (kind === "status") return "Status";
  if (kind === "ambient") return "Ambient";
  if (kind === "omarchy") return "Omarchy";
  return "Loop";
}

function normalize(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function levenshtein(a, b) {
  if (a === b) return 0;
  if (!a) return b.length;
  if (!b) return a.length;
  if (Math.abs(a.length - b.length) > 4) return 99;
  const rows = b.length + 1;
  let prev = new Array(rows);
  let cur = new Array(rows);
  for (let j = 0; j < rows; j++) prev[j] = j;
  for (let i = 1; i <= a.length; i++) {
    cur[0] = i;
    const ca = a.charCodeAt(i - 1);
    for (let j = 1; j <= b.length; j++) {
      const cost = ca === b.charCodeAt(j - 1) ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
    }
    [prev, cur] = [cur, prev];
  }
  return prev[b.length];
}

function subsequenceScore(query, text) {
  let qi = 0;
  let consecutive = 0;
  let bestConsec = 0;
  let first = -1;
  for (let i = 0; i < text.length && qi < query.length; i++) {
    if (text[i] === query[qi]) {
      if (first < 0) first = i;
      consecutive += 1;
      bestConsec = Math.max(bestConsec, consecutive);
      qi += 1;
    } else {
      consecutive = 0;
    }
  }
  if (qi < query.length) return 0;
  return 400 + bestConsec * 24 - first * 3 - (text.length - query.length);
}

function fuzzyScore(query, item) {
  const q = query.trim().toLowerCase();
  if (!q) return 1;
  const name = item.name.toLowerCase();
  const id = item.id.toLowerCase();
  const desc = item.description.toLowerCase();
  const nq = normalize(q);
  const nn = normalize(item.name);
  const nid = normalize(item.id);
  let best = 0;
  if (name === q || nn === nq || id === q || nid === nq) return 1000;
  if (name.startsWith(q) || nn.startsWith(nq)) best = Math.max(best, 920 - Math.abs(name.length - q.length));
  if (id.startsWith(q) || nid.startsWith(nq)) best = Math.max(best, 860);
  for (const word of name.split(/\s+/)) {
    if (word.startsWith(q)) best = Math.max(best, 840);
  }
  best = Math.max(best, subsequenceScore(q, name), subsequenceScore(nq, nn), subsequenceScore(q, id));
  const targets = [nn, nid, ...name.split(/\s+/).map(normalize)];
  for (const target of targets) {
    if (!target) continue;
    const d = levenshtein(nq, target);
    const allow = Math.max(1, Math.floor(Math.max(nq.length, target.length) * 0.4));
    if (d <= allow) best = Math.max(best, 520 - d * 50);
    if (target.length >= nq.length) {
      for (let i = 0; i <= target.length - nq.length; i++) {
        const slice = target.slice(i, i + nq.length);
        const dd = levenshtein(nq, slice);
        if (dd <= 2) best = Math.max(best, 480 - dd * 50);
      }
    }
  }
  if (desc.includes(q)) best = Math.max(best, 140);
  return best;
}

function visibleCatalog() {
  let items = catalog;
  if (kindFilter === "favorites") {
    items = items.filter((item) => favorites.has(item.id));
  } else if (kindFilter) {
    items = items.filter((item) => item.kind === kindFilter);
  }
  // Viewing a populated group filters to its ids. Selection mode does not —
  // adding does not require a library filter; keep All/type/search.
  // Empty groups keep the full catalog so the view is not a blank list.
  if (activeGroup && !selectionGroup) {
    const group = activeGroupRecord();
    const ids = groupIds(group);
    if (group && ids.length > 0) {
      const want = new Set(ids);
      items = items.filter((item) => want.has(item.id));
    }
  }
  return items;
}

function emptyLibraryMessage() {
  if (kindFilter === "favorites" && favorites.size === 0) {
    return "No favorites yet. Tap the heart on a card.";
  }
  return "No animations match.";
}

function rankedCatalog() {
  const items = visibleCatalog();
  const q = searchQuery.trim();
  if (!q) return items.map((item) => ({ item, score: 1 }));
  const ranked = [];
  for (const item of items) {
    const score = fuzzyScore(q, item);
    if (score > 0) ranked.push({ item, score });
  }
  ranked.sort((a, b) => b.score - a.score || a.item.name.localeCompare(b.item.name));
  return ranked;
}

function bestMatch() {
  if (!searchQuery.trim()) return null;
  const ranked = rankedCatalog();
  return ranked.length ? ranked[0].item : null;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function updateSearchChrome() {
  const q = searchQuery;
  const match = bestMatch();
  if (!q || !match) {
    searchGhost.innerHTML = "";
    searchFill.classList.add("hidden");
    searchFill.textContent = "";
    return;
  }
  const name = match.name;
  const lower = name.toLowerCase();
  const ql = q.toLowerCase();
  if (lower.startsWith(ql)) {
    searchGhost.innerHTML = `<span class="typed">${escapeHtml(q)}</span>${escapeHtml(name.slice(q.length))}`;
    searchFill.classList.add("hidden");
  } else {
    searchGhost.innerHTML = "";
    searchFill.textContent = name;
    searchFill.classList.remove("hidden");
  }
}

function acceptSearch(assignIt) {
  const match = bestMatch();
  if (!match) return;
  searchEl.value = match.name;
  searchQuery = match.name;
  lastLibKey = "";
  updateSearchChrome();
  maybeRenderLibrary();
  if (assignIt) assign(focus, match.id);
}

const ROW_GAP = 8;
const OVERSCAN = 6;
const THUMB_W = 18;
const THUMB_H = 68;
const THUMB_FRAME_MS = 500;
const rails = {
  left: makeRail(libraryLeft, "left"),
  right: makeRail(libraryRight, "right"),
};
const previewCache = new Map();
let hoverThumb = null;
let dragKind = "";
let dragId = "";
let dragGroupId = "";
let renamingGroup = "";
let windowRaf = 0;

function makeRail(root, side) {
  return { root, side, items: [], clickSide: side, topId: null, cards: new Map(), start: -1, end: -1 };
}

function cardHeight() {
  const raw = getComputedStyle(document.documentElement).getPropertyValue("--card-h");
  const px = parseFloat(raw);
  return Number.isFinite(px) && px > 0 ? px : 92;
}

function rowHeight() {
  return cardHeight() + ROW_GAP;
}

function renderLibrary() {
  if (!catalog.length) return;
  const q = searchQuery.trim();
  const items = q ? rankedCatalog().map((row) => row.item) : visibleCatalog();
  const topId = q && items[0] ? items[0].id : null;
  if (narrow) {
    // One merged list under the wells; cards go to the focused well, L/R badges pick a side.
    setRail(rails.left, items, null, topId);
    setRail(rails.right, [], "right", null);
    return;
  }
  // The filtered catalog is split across the two rails — first half left, second half
  // right — so each column is half as long to scroll. The rail is still the target well;
  // the L/R badges send a card to the other side.
  const mid = Math.ceil(items.length / 2);
  setRail(rails.left, items.slice(0, mid), "left", topId);
  setRail(rails.right, items.slice(mid), "right", null);
}

function playingCaption(leftOn, rightOn) {
  if (leftOn && rightOn) return "Playing · Both";
  if (leftOn) return "Playing · Left";
  if (rightOn) return "Playing · Right";
  return "";
}

function setRail(rail, items, clickSide, topId) {
  rail.items = items;
  rail.clickSide = clickSide;
  rail.topId = topId && items.some((item) => item.id === topId) ? topId : null;
  const root = rail.root;
  const empty = root.querySelector(".empty-search");
  if (!items.length) {
    for (const entry of rail.cards.values()) entry.el.remove();
    rail.cards.clear();
    rail.start = rail.end = -1;
    root.style.height = "";
    root.classList.remove("virtual");
    // The right rail is simply empty when one match lands on the left; say so quietly.
    const message = rail.side === "right" && !narrow && rails.left.items.length ? "" : emptyLibraryMessage();
    if (!empty) {
      const note = document.createElement("p");
      note.className = "empty-search";
      note.textContent = message;
      root.appendChild(note);
    } else {
      empty.textContent = message;
    }
    return;
  }
  if (empty) empty.remove();
  root.classList.add("virtual");
  root.style.height = `${items.length * rowHeight() - ROW_GAP}px`;
  renderWindow(rail, true);
}

function railViewport(rail) {
  const container = narrow ? null : rail.root.closest(".library-col");
  const rootTop = rail.root.getBoundingClientRect().top;
  if (container) {
    const box = container.getBoundingClientRect();
    return { from: box.top - rootTop, to: box.bottom - rootTop, container };
  }
  return { from: -rootTop, to: window.innerHeight - rootTop, container: null };
}

function renderWindow(rail, force = false) {
  const items = rail.items;
  if (!items.length) return;
  const row = rowHeight();
  const { from, to } = railViewport(rail);
  const start = Math.max(0, Math.floor(from / row) - OVERSCAN);
  const end = Math.min(items.length, Math.ceil(to / row) + OVERSCAN);
  if (!force && start === rail.start && end === rail.end) return;
  rail.start = start;
  rail.end = end;
  const wanted = new Set();
  for (let index = start; index < end; index++) {
    const item = items[index];
    wanted.add(item.id);
    ensureCard(rail, item, index, row);
  }
  for (const [id, entry] of rail.cards) {
    if (wanted.has(id)) continue;
    if (hoverThumb && hoverThumb.card === entry.el) stopHoverThumb();
    entry.el.remove();
    rail.cards.delete(id);
  }
}

function renderAllWindows() {
  windowRaf = 0;
  renderWindow(rails.left);
  renderWindow(rails.right);
}

function scheduleWindows() {
  if (windowRaf) return;
  windowRaf = requestAnimationFrame(renderAllWindows);
}

function cardSignature(rail, item) {
  const leftOn = state.left_anim === item.id;
  const rightOn = state.right_anim === item.id;
  const liked = favorites.has(item.id);
  const filing = !!selectionGroup;
  const inGroup = filing ? groupIds(selectionGroupRecord()).includes(item.id) : false;
  const target = rail.clickSide || focus;
  return `${leftOn}|${rightOn}|${liked}|${filing}|${inGroup}|${rail.topId === item.id}|${target}|${item.name}`;
}

function ensureCard(rail, item, index, row) {
  const sig = cardSignature(rail, item);
  let entry = rail.cards.get(item.id);
  if (!entry) {
    const el = buildCard(rail, item);
    entry = { el, sig };
    rail.cards.set(item.id, entry);
    rail.root.appendChild(el);
  } else if (entry.sig !== sig) {
    const el = buildCard(rail, item);
    const hadFocus = document.activeElement === entry.el;
    entry.el.replaceWith(el);
    entry.el = el;
    entry.sig = sig;
    if (hadFocus) el.focus({ preventScroll: true });
  }
  entry.el.dataset.index = String(index);
  const top = `${index * row}px`;
  if (entry.el.style.top !== top) entry.el.style.top = top;
}

function drawThumb(canvas, pixels) {
  const ctx = canvas.getContext("2d", { alpha: false });
  if (!ctx) return;
  ctx.fillStyle = "#07080a";
  ctx.fillRect(0, 0, THUMB_W, THUMB_H);
  for (let y = 0; y < HEIGHT; y++) {
    for (let x = 0; x < WIDTH; x++) {
      const v = (pixels[y * WIDTH + x] || 0) / 255;
      if (v < 0.02) continue;
      ctx.fillStyle = `rgba(255, 244, 208, ${0.25 + v * 0.75})`;
      ctx.fillRect(x * 2, y * 2, 2, 2);
    }
  }
}

async function loadPreview(id) {
  if (previewCache.has(id)) return previewCache.get(id);
  const promise = (async () => {
    try {
      const res = await fetch(`/api/preview?id=${encodeURIComponent(id)}`);
      if (!res.ok) throw new Error("preview");
      const data = await res.json();
      const frames = Array.isArray(data.frames) ? data.frames : [];
      previewCache.set(id, frames);
      return frames;
    } catch {
      previewCache.delete(id);
      return [];
    }
  })();
  previewCache.set(id, promise);
  return promise;
}

function isPlaying(id) {
  return state.left_anim === id || state.right_anim === id;
}

function stopHoverThumb() {
  if (!hoverThumb) return;
  const { card, id, timer } = hoverThumb;
  if (timer) clearInterval(timer);
  if (!isPlaying(id)) card.classList.remove("show-thumb");
  hoverThumb = null;
}

async function startHoverThumb(card, item) {
  if (hoverThumb && hoverThumb.card === card) return;
  stopHoverThumb();
  if (isPlaying(item.id)) return;
  const canvas = card.querySelector("canvas.thumb");
  if (!canvas) return;
  const token = { card, id: item.id, timer: 0 };
  hoverThumb = token;
  const frames = await loadPreview(item.id);
  if (hoverThumb !== token || !frames.length) return;
  let index = 0;
  drawThumb(canvas, frames[0]);
  card.classList.add("show-thumb");
  if (frames.length > 1) {
    token.timer = window.setInterval(() => {
      index = (index + 1) % frames.length;
      drawThumb(canvas, frames[index]);
    }, THUMB_FRAME_MS);
  }
}

function drawPlayingThumbs() {
  for (const rail of [rails.left, rails.right]) {
    for (const side of ["left", "right"]) {
      const id = state[`${side}_anim`];
      const entry = rail.cards.get(id);
      if (!entry) continue;
      if (side === "right" && state.left_anim === id) continue;
      const canvas = entry.el.querySelector("canvas.thumb");
      if (!canvas) continue;
      entry.el.classList.add("show-thumb");
      drawThumb(canvas, lastPixels[side]);
    }
  }
}

function clearDropTargets() {
  document.querySelectorAll(".module.drop-hover").forEach((mod) => mod.classList.remove("drop-hover"));
  document.body.classList.remove("dragging-card");
}

function buildCard(rail, item) {
  const clickSide = rail.clickSide;
  const card = document.createElement("article");
  card.className = "card";
  card.tabIndex = 0;
  card.setAttribute("role", "button");
  card.dataset.id = item.id;
  card.draggable = true;
  const leftOn = state.left_anim === item.id;
  const rightOn = state.right_anim === item.id;
  if (leftOn || rightOn) card.classList.add("active", "show-thumb");
  if (rail.topId && item.id === rail.topId) card.classList.add("suggest");
  const target = clickSide || focus;
  card.setAttribute("aria-label", `${item.name}. ${kindLabel(item.kind)}. Press Enter to play on the ${target} well. Drag onto a well to play it there.`);

  const thumb = document.createElement("canvas");
  thumb.className = "thumb";
  thumb.width = THUMB_W;
  thumb.height = THUMB_H;
  thumb.setAttribute("aria-hidden", "true");
  if (leftOn || rightOn) drawThumb(thumb, lastPixels[leftOn ? "left" : "right"]);

  const body = document.createElement("div");
  body.className = "card-body";

  const title = document.createElement("h3");
  const name = document.createElement("span");
  name.className = "card-name";
  name.textContent = item.name;
  title.appendChild(name);
  const caption = playingCaption(leftOn, rightOn);
  if (caption) {
    const playing = document.createElement("span");
    playing.className = "playing";
    playing.textContent = caption;
    title.appendChild(playing);
  }
  const blurb = document.createElement("p");
  blurb.textContent = item.description;
  const badges = document.createElement("div");
  badges.className = "badges";

  const kind = document.createElement("span");
  kind.className = "badge kind";
  kind.textContent = kindLabel(item.kind);
  badges.appendChild(kind);

  const heart = document.createElement("button");
  heart.type = "button";
  const liked = favorites.has(item.id);
  heart.className = liked ? "heart on" : "heart";
  heart.textContent = liked ? "♥" : "♡";
  const filing = !!selectionGroup;
  const filingRecord = filing ? selectionGroupRecord() : null;
  heart.title = filing
    ? liked
      ? `Unfavorite and remove ${item.name} from the group`
      : `Favorite and add ${item.name} to the group`
    : liked
      ? "Remove favorite"
      : "Save as favorite";
  heart.setAttribute("aria-label", liked ? `Unfavorite ${item.name}` : `Favorite ${item.name}`);
  heart.setAttribute("aria-pressed", liked ? "true" : "false");
  heart.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleHeart(item);
  });
  badges.appendChild(heart);

  if (filing) {
    const inGroup = groupIds(filingRecord).includes(item.id);
    if (inGroup) card.classList.add("in-group");
    const plus = document.createElement("button");
    plus.type = "button";
    plus.className = inGroup ? "card-add on" : "card-add";
    plus.textContent = inGroup ? "✓" : "+";
    plus.title = inGroup
      ? `Remove ${item.name} from ${filingRecord ? filingRecord.name : "group"}`
      : `Add ${item.name} to ${filingRecord ? filingRecord.name : "group"}`;
    plus.setAttribute("aria-label", plus.title);
    plus.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleGroupItem(item, !inGroup);
    });
    badges.appendChild(plus);
  }

  for (const [side, on, label] of [
    ["left", leftOn, "L"],
    ["right", rightOn, "R"],
  ]) {
    const badge = document.createElement("button");
    badge.type = "button";
    badge.className = `badge assign ${on ? "on" : ""}`;
    badge.textContent = label;
    badge.title = `Run ${item.name} on the ${side} module`;
    badge.setAttribute("aria-label", badge.title);
    badge.setAttribute("aria-pressed", on ? "true" : "false");
    badge.addEventListener("click", (event) => {
      event.stopPropagation();
      assign(side, item.id);
      // A mouse click leaves the keyboard on the well it just filled, not on the badge.
      if (event.detail > 0) focusWell(side);
    });
    badges.appendChild(badge);
  }

  body.append(title, blurb, badges);
  card.append(thumb, body);
  const activate = () => {
    if (selectionGroup) {
      const group = selectionGroupRecord();
      const inGroup = groupIds(group).includes(item.id);
      toggleGroupItem(item, !inGroup);
      return false;
    }
    assign(clickSide || focus, item.id);
    return true;
  };
  card.addEventListener("click", (event) => {
    const played = activate();
    // Pointer clicks hand the keyboard to the well so arrows reach the game at once.
    // Keyboard users (Enter/Space) keep their place in the rail.
    if (played && event.detail > 0) focusWell(clickSide || focus);
  });
  card.addEventListener("keydown", (event) => {
    if (event.target !== card) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      activate();
    }
  });
  card.addEventListener("pointerenter", () => startHoverThumb(card, item));
  card.addEventListener("pointerleave", () => {
    if (hoverThumb && hoverThumb.card === card) stopHoverThumb();
  });
  card.addEventListener("focus", () => startHoverThumb(card, item));
  card.addEventListener("blur", () => {
    if (hoverThumb && hoverThumb.card === card && !card.matches(":hover")) stopHoverThumb();
  });
  card.addEventListener("dragstart", (event) => {
    dragKind = "card";
    dragId = item.id;
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = "copy";
      event.dataTransfer.setData("text/plain", item.id);
      event.dataTransfer.setData("application/x-ledmatrix-anim", item.id);
    }
    card.classList.add("dragging");
    document.body.classList.add("dragging-card");
  });
  card.addEventListener("dragend", () => {
    card.classList.remove("dragging");
    dragKind = "";
    dragId = "";
    clearDropTargets();
  });
  return card;
}

function bindDropTargets() {
  document.querySelectorAll(".module").forEach((mod) => {
    const side = mod.dataset.side === "right" ? "right" : "left";
    mod.addEventListener("dragenter", (event) => {
      if (dragKind !== "card") return;
      event.preventDefault();
      mod.classList.add("drop-hover");
    });
    mod.addEventListener("dragover", (event) => {
      if (dragKind !== "card") return;
      event.preventDefault();
      if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
      mod.classList.add("drop-hover");
    });
    mod.addEventListener("dragleave", (event) => {
      if (mod.contains(event.relatedTarget)) return;
      mod.classList.remove("drop-hover");
    });
    mod.addEventListener("drop", (event) => {
      if (dragKind !== "card") return;
      event.preventDefault();
      const id = (event.dataTransfer && event.dataTransfer.getData("application/x-ledmatrix-anim")) || dragId;
      clearDropTargets();
      dragKind = "";
      dragId = "";
      if (id) {
        assign(side, id);
        focusWell(side);
      }
    });
  });
}

function post(path, body) {
  inputQueue = inputQueue.then(() =>
    fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).catch(() => {})
  );
  return inputQueue;
}

async function postJson(path, body) {
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data = null;
    try {
      data = await res.json();
    } catch {
      data = null;
    }
    if (!res.ok) {
      const reason = data && data.error ? data.error : `HTTP ${res.status}`;
      toast(`Couldn't save — ${reason}`, { kind: "error", duration: 2600 });
      return null;
    }
    return data;
  } catch {
    toast("Couldn't reach the app — change not saved", { kind: "error", duration: 2600 });
    return null;
  }
}

function applyLibrary(data) {
  if (!data || typeof data !== "object") return;
  if (Array.isArray(data.favorites)) favorites = new Set(data.favorites);
  if (Array.isArray(data.groups)) mergeGroups(data.groups);
  if ("randomGroup" in data) randomGroup = data.randomGroup || null;
}

function selectionGroupRecord() {
  return groups.find((item) => item.id === selectionGroup) || null;
}

function filingHint() {
  if (!selectionGroup) return "";
  const group = selectionGroupRecord();
  return group ? `Adding to ${group.name} — tap cards to add. Esc or Done to exit.` : "";
}

function exitSelectionMode() {
  if (!selectionGroup) return;
  selectionGroup = "";
  lastLibKey = "";
  lastGroupUiKey = "";
  maybeRenderLibrary();
}

function enterSelectionMode(groupId) {
  if (selectionGroup === groupId) {
    selectionGroup = "";
  } else {
    selectionGroup = groupId;
    activeGroup = "";
  }
  confirmDeleteGroup = "";
  lastLibKey = "";
  lastGroupUiKey = "";
  maybeRenderLibrary();
}

function openGroupView(groupId) {
  if (selectionGroup === groupId) {
    selectionGroup = "";
    activeGroup = groupId;
  } else if (activeGroup === groupId) {
    activeGroup = "";
  } else {
    selectionGroup = "";
    activeGroup = groupId;
  }
  confirmDeleteGroup = "";
  lastLibKey = "";
  lastGroupUiKey = "";
  maybeRenderLibrary();
}

function setGroupMembership(group, animId, on) {
  if (!group) return;
  const ids = group.ids || (group.ids = []);
  if (on && !ids.includes(animId)) ids.push(animId);
  if (!on) group.ids = ids.filter((id) => id !== animId);
}

async function toggleHeart(item) {
  const on = !favorites.has(item.id);
  if (on) favorites.add(item.id);
  else favorites.delete(item.id);
  const group = selectionGroup ? selectionGroupRecord() : null;
  if (group) {
    setGroupMembership(group, item.id, on);
  }
  lastLibKey = "";
  maybeRenderLibrary();
  const fav = await postJson("/api/favorite", { id: item.id, on });
  if (fav) {
    applyLibrary(fav);
    toast(on ? `♥ ${item.name}` : `Removed ${item.name} from favorites`);
  }
  if (selectionGroup) {
    const filed = await postJson("/api/groups/item", { groupId: selectionGroup, animId: item.id, on });
    if (filed) {
      applyLibrary(filed);
      if (group) toast(on ? `Added to ${group.name}` : `Removed from ${group.name}`);
    }
  }
  lastLibKey = "";
  maybeRenderLibrary();
}

async function toggleGroupItem(item, on) {
  if (!selectionGroup) return;
  const group = selectionGroupRecord();
  setGroupMembership(group, item.id, on);
  lastLibKey = "";
  maybeRenderLibrary();
  const filed = await postJson("/api/groups/item", { groupId: selectionGroup, animId: item.id, on });
  if (filed) {
    applyLibrary(filed);
    if (group) toast(on ? `Added to ${group.name}` : `Removed from ${group.name}`);
  }
  lastLibKey = "";
  maybeRenderLibrary();
}

function maybeRenderGroups(force = false) {
  if (!force && document.querySelector(".group-composer")) return;
  const key = `${groupsStatus}|${activeGroup}|${selectionGroup}|${confirmDeleteGroup}|${renamingGroup}|${randomGroup || ""}|${groups.map((group) => `${group.id}:${group.name}:${(group.ids || []).join("+")}`).join(",")}`;
  if (!force && key === lastGroupUiKey) return;
  lastGroupUiKey = key;
  renderGroups();
}

async function deleteGroup(group) {
  confirmDeleteGroup = "";
  const data = await postJson("/api/groups/delete", { id: group.id });
  if (data && Array.isArray(data.groups)) groups = data.groups;
  else if (data) groups = groups.filter((row) => row.id !== group.id);
  if (!data) {
    lastGroupUiKey = "";
    maybeRenderGroups();
    return;
  }
  if (activeGroup === group.id) activeGroup = "";
  if (selectionGroup === group.id) selectionGroup = "";
  if (randomGroup === group.id) randomGroup = null;
  toast(`Deleted ${group.name}`);
  lastLibKey = "";
  lastGroupUiKey = "";
  maybeRenderLibrary();
}

function renderGroups() {
  if (!groupsEl) return;
  groupsEl.innerHTML = "";
  const row = document.createElement("div");
  row.className = "group-row";
  row.id = "group-row";

  if (groupsStatus === "loading") {
    const status = document.createElement("p");
    status.className = "groups-status";
    status.id = "groups-status";
    status.textContent = "Loading groups…";
    row.appendChild(status);
  } else if (groupsStatus === "error") {
    const status = document.createElement("p");
    status.className = "groups-status error";
    status.id = "groups-status";
    status.textContent = "Could not load groups.";
    row.appendChild(status);
  } else if (!groups.length) {
    const status = document.createElement("p");
    status.className = "groups-status";
    status.id = "groups-status";
    status.textContent = "No groups yet.";
    row.appendChild(status);
  }

  for (const group of groups) {
    const bubble = document.createElement("div");
    bubble.className = activeGroup === group.id ? "group-bubble active" : "group-bubble";
    if (selectionGroup === group.id) bubble.classList.add("selecting");
    bubble.dataset.groupId = group.id;

    if (confirmDeleteGroup === group.id) {
      bubble.classList.add("confirming");
      const prompt = document.createElement("span");
      prompt.className = "group-confirm-text";
      prompt.textContent = `Delete ${group.name}?`;
      const yes = document.createElement("button");
      yes.type = "button";
      yes.className = "group-confirm yes";
      yes.textContent = "Yes";
      yes.setAttribute("aria-label", `Yes, delete ${group.name}`);
      yes.addEventListener("click", (event) => {
        event.stopPropagation();
        deleteGroup(group);
      });
      const no = document.createElement("button");
      no.type = "button";
      no.className = "group-confirm no";
      no.textContent = "No";
      no.setAttribute("aria-label", `Keep ${group.name}`);
      no.addEventListener("click", (event) => {
        event.stopPropagation();
        confirmDeleteGroup = "";
        lastGroupUiKey = "";
        maybeRenderGroups();
      });
      bubble.append(prompt, yes, no);
      row.appendChild(bubble);
      queueMicrotask(() => no.focus());
      continue;
    }

    if (renamingGroup === group.id) {
      bubble.classList.add("renaming");
      const form = document.createElement("form");
      form.className = "group-composer rename";
      const input = document.createElement("input");
      input.type = "text";
      input.maxLength = 40;
      input.value = group.name;
      input.setAttribute("aria-label", `Rename ${group.name}`);
      const save = document.createElement("button");
      save.type = "submit";
      save.textContent = "Save";
      form.append(input, save);
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        renameGroup(group, input.value);
      });
      input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopPropagation();
          renamingGroup = "";
          lastGroupUiKey = "";
          maybeRenderGroups(true);
        }
      });
      bubble.appendChild(form);
      row.appendChild(bubble);
      queueMicrotask(() => {
        input.focus();
        input.select();
      });
      continue;
    }

    bubble.draggable = true;
    bubble.addEventListener("dragstart", (event) => {
      dragKind = "group";
      dragGroupId = group.id;
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("application/x-ledmatrix-group", group.id);
        event.dataTransfer.setData("text/plain", group.name);
      }
      bubble.classList.add("dragging");
    });
    bubble.addEventListener("dragend", () => {
      bubble.classList.remove("dragging");
      dragKind = "";
      dragGroupId = "";
      groupsEl.querySelectorAll(".group-bubble.drop-before, .group-bubble.drop-after").forEach((el) => {
        el.classList.remove("drop-before", "drop-after");
      });
    });
    bubble.addEventListener("dragover", (event) => {
      if (dragKind !== "group" || dragGroupId === group.id) return;
      event.preventDefault();
      if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
      const box = bubble.getBoundingClientRect();
      const before = event.clientX < box.left + box.width / 2;
      bubble.classList.toggle("drop-before", before);
      bubble.classList.toggle("drop-after", !before);
    });
    bubble.addEventListener("dragleave", (event) => {
      if (bubble.contains(event.relatedTarget)) return;
      bubble.classList.remove("drop-before", "drop-after");
    });
    bubble.addEventListener("drop", (event) => {
      if (dragKind !== "group") return;
      event.preventDefault();
      const movedId = (event.dataTransfer && event.dataTransfer.getData("application/x-ledmatrix-group")) || dragGroupId;
      const before = bubble.classList.contains("drop-before");
      bubble.classList.remove("drop-before", "drop-after");
      dragKind = "";
      dragGroupId = "";
      if (movedId && movedId !== group.id) moveGroup(movedId, group.id, before);
    });

    const select = document.createElement("button");
    select.type = "button";
    select.className = "group-select";
    select.textContent = `${group.name} · ${(group.ids || []).length}`;
    select.title = `Show ${group.name}. Double-click to rename. Alt+← / Alt+→ to reorder.`;
    select.setAttribute("aria-pressed", activeGroup === group.id ? "true" : "false");
    select.addEventListener("click", () => {
      openGroupView(group.id);
    });
    select.addEventListener("dblclick", (event) => {
      event.preventDefault();
      beginRename(group.id);
    });
    select.addEventListener("keydown", (event) => {
      if (!event.altKey || (event.key !== "ArrowLeft" && event.key !== "ArrowRight")) return;
      event.preventDefault();
      const index = groups.findIndex((row) => row.id === group.id);
      const target = index + (event.key === "ArrowLeft" ? -1 : 1);
      if (index < 0 || target < 0 || target >= groups.length) return;
      moveGroup(group.id, groups[target].id, event.key === "ArrowLeft");
      queueMicrotask(() => {
        const btn = groupsEl.querySelector(`.group-bubble[data-group-id="${group.id}"] .group-select`);
        if (btn) btn.focus();
      });
    });

    const rename = document.createElement("button");
    rename.type = "button";
    rename.className = "group-rename";
    rename.textContent = "✎";
    rename.title = `Rename ${group.name}`;
    rename.setAttribute("aria-label", rename.title);
    rename.addEventListener("click", (event) => {
      event.stopPropagation();
      beginRename(group.id);
    });

    const add = document.createElement("button");
    add.type = "button";
    add.className = selectionGroup === group.id ? "group-add on" : "group-add";
    add.setAttribute("data-add", "true");
    add.textContent = "+";
    add.title = selectionGroup === group.id
      ? `Stop adding to ${group.name}`
      : `Add animations to ${group.name}`;
    add.setAttribute("aria-label", add.title);
    add.setAttribute("aria-pressed", selectionGroup === group.id ? "true" : "false");
    add.addEventListener("click", (event) => {
      event.stopPropagation();
      enterSelectionMode(group.id);
    });

    const rand = document.createElement("button");
    rand.type = "button";
    rand.className = randomGroup === group.id ? "group-random on" : "group-random";
    rand.textContent = randomGroup === group.id ? "Random · on" : "Random";
    rand.title = `Cycle only ${group.name} for 10–30 seconds each`;
    rand.setAttribute("aria-pressed", randomGroup === group.id ? "true" : "false");
    rand.addEventListener("click", async (event) => {
      event.stopPropagation();
      const enabled = randomGroup !== group.id;
      const data = await postJson("/api/group-random", { groupId: group.id, enabled });
      if (data) {
        randomGroup = data.randomGroup || null;
        if (randomBtn) {
          const globalOn = !!data.random && !data.randomGroup;
          randomBtn.classList.toggle("on", globalOn);
          randomBtn.textContent = globalOn ? "Random · on" : "Random";
        }
        toast(enabled ? `Shuffling ${group.name}` : "Shuffle off");
      }
      lastGroupUiKey = "";
      maybeRenderGroups();
    });

    const del = document.createElement("button");
    del.type = "button";
    del.className = "group-delete";
    del.textContent = "×";
    del.setAttribute("aria-label", `Delete ${group.name}`);
    del.title = `Delete ${group.name}`;
    del.addEventListener("click", (event) => {
      event.stopPropagation();
      confirmDeleteGroup = group.id;
      lastGroupUiKey = "";
      maybeRenderGroups();
    });

    bubble.append(select, rename, add, rand, del);
    row.appendChild(bubble);
  }

  const newBtn = document.createElement("button");
  newBtn.type = "button";
  newBtn.className = "group-new";
  newBtn.id = "new-group";
  newBtn.textContent = "New group";
  newBtn.addEventListener("click", beginNewGroup);
  row.appendChild(newBtn);
  groupsEl.appendChild(row);

  const hint = document.createElement("p");
  hint.className = "groups-hint";
  hint.id = "groups-hint";
  const text = filingHint();
  hint.textContent = text;
  hint.hidden = !text || !!selectionGroup;
  groupsEl.appendChild(hint);

  if (selectionGroup && text) {
    const bar = document.createElement("div");
    bar.className = "selection-bar";
    bar.id = "selection-bar";
    const banner = document.createElement("p");
    banner.className = "filing-banner";
    banner.id = "filing-banner";
    banner.textContent = text;
    const done = document.createElement("button");
    done.type = "button";
    done.className = "selection-done";
    done.id = "selection-done";
    done.textContent = "Done";
    done.title = "Exit selection mode";
    done.addEventListener("click", () => exitSelectionMode());
    bar.append(banner, done);
    groupsEl.appendChild(bar);
  } else if (activeGroup) {
    const group = activeGroupRecord();
    if (group && groupIds(group).length === 0) {
      const banner = document.createElement("p");
      banner.className = "filing-banner";
      banner.id = "filing-banner";
      banner.textContent = `${group.name} is empty. Tap + on the group to add.`;
      groupsEl.appendChild(banner);
    }
  }
}

function libraryPayload() {
  return {
    favorites: [...favorites],
    groups: groups.map((group) => ({ id: group.id, name: group.name, ids: (group.ids || []).slice() })),
  };
}

async function saveLibrary(successText) {
  const data = await postJson("/api/library", libraryPayload());
  if (data) {
    applyLibrary(data);
    if (successText) toast(successText);
  } else {
    await loadLibrary();
  }
  lastLibKey = "";
  lastGroupUiKey = "";
  maybeRenderGroups(true);
  maybeRenderLibrary();
}

function beginRename(groupId) {
  renamingGroup = groupId;
  confirmDeleteGroup = "";
  lastGroupUiKey = "";
  maybeRenderGroups(true);
}

async function renameGroup(group, rawName) {
  const name = String(rawName || "").trim().slice(0, 40);
  renamingGroup = "";
  if (!name || name === group.name) {
    lastGroupUiKey = "";
    maybeRenderGroups(true);
    return;
  }
  const previous = group.name;
  const record = groups.find((row) => row.id === group.id);
  if (record) record.name = name;
  await saveLibrary(`Renamed ${previous} to ${name}`);
}

async function moveGroup(movedId, targetId, before) {
  const from = groups.findIndex((row) => row.id === movedId);
  const to = groups.findIndex((row) => row.id === targetId);
  if (from < 0 || to < 0 || from === to) return;
  const next = groups.slice();
  const [moved] = next.splice(from, 1);
  let insertAt = next.findIndex((row) => row.id === targetId);
  if (!before) insertAt += 1;
  next.splice(insertAt, 0, moved);
  groups = next;
  await saveLibrary(`Moved ${moved.name}`);
}

function applyScenes(data) {
  if (!data || typeof data !== "object") return;
  if (Array.isArray(data.scenes)) {
    scenes = data.scenes.map((scene) => ({
      id: scene.id,
      name: scene.name,
      left: scene.left,
      right: scene.right,
      brightness: scene.brightness,
      speed: scene.speed,
      schedule: scene.schedule ? { start: scene.schedule.start, end: scene.schedule.end, days: scene.schedule.days || [] } : null,
    }));
    scenesStatus = "ready";
  }
  if ("activeScene" in data) activeScene = data.activeScene || null;
  if (confirmDeleteScene && !scenes.some((scene) => scene.id === confirmDeleteScene)) confirmDeleteScene = "";
  maybeRenderScenes();
}

function sceneSummary(scene) {
  const parts = [`${animName(scene.left)} / ${animName(scene.right)}`, `${scene.brightness}`, `${Number(scene.speed).toFixed(2).replace(/0$/, "")}×`];
  if (scene.schedule) parts.push(`${scene.schedule.start}–${scene.schedule.end} daily`);
  return parts.join(" · ");
}

function maybeRenderScenes(force = false) {
  if (!scenesEl) return;
  if (!force && scenesEl.querySelector(".scene-composer")) return;
  const key = `${scenesStatus}|${activeScene || ""}|${confirmDeleteScene}|${scenes
    .map((scene) => `${scene.id}:${scene.name}:${scene.left}:${scene.right}:${scene.brightness}:${scene.speed}:${scene.schedule ? scene.schedule.start + scene.schedule.end : ""}`)
    .join(",")}|${catalog.length}`;
  if (!force && key === lastSceneUiKey) return;
  lastSceneUiKey = key;
  renderScenes();
}

function renderScenes() {
  scenesEl.innerHTML = "";
  const row = document.createElement("div");
  row.className = "scene-row";
  row.id = "scene-row";
  const label = document.createElement("span");
  label.className = "scene-label";
  label.textContent = "Scenes";
  row.appendChild(label);

  if (scenesStatus === "loading") {
    const status = document.createElement("p");
    status.className = "groups-status";
    status.textContent = "Loading scenes…";
    row.appendChild(status);
  } else if (!scenes.length) {
    const status = document.createElement("p");
    status.className = "groups-status";
    status.textContent = "No scenes yet — save the current desk to recall it later.";
    row.appendChild(status);
  }

  for (const scene of scenes) {
    const chip = document.createElement("div");
    chip.className = activeScene === scene.id ? "scene-chip active" : "scene-chip";
    chip.dataset.sceneId = scene.id;
    if (confirmDeleteScene === scene.id) {
      chip.classList.add("confirming");
      const prompt = document.createElement("span");
      prompt.className = "group-confirm-text";
      prompt.textContent = `Delete ${scene.name}?`;
      const yes = document.createElement("button");
      yes.type = "button";
      yes.className = "group-confirm yes";
      yes.textContent = "Yes";
      yes.setAttribute("aria-label", `Yes, delete scene ${scene.name}`);
      yes.addEventListener("click", async (event) => {
        event.stopPropagation();
        confirmDeleteScene = "";
        const data = await postJson("/api/scenes/delete", { id: scene.id });
        if (data) {
          applyScenes(data);
          toast(`Deleted scene ${scene.name}`);
        }
        lastSceneUiKey = "";
        maybeRenderScenes(true);
      });
      const no = document.createElement("button");
      no.type = "button";
      no.className = "group-confirm no";
      no.textContent = "No";
      no.setAttribute("aria-label", `Keep scene ${scene.name}`);
      no.addEventListener("click", (event) => {
        event.stopPropagation();
        confirmDeleteScene = "";
        lastSceneUiKey = "";
        maybeRenderScenes(true);
      });
      chip.append(prompt, yes, no);
      row.appendChild(chip);
      queueMicrotask(() => no.focus());
      continue;
    }
    const apply = document.createElement("button");
    apply.type = "button";
    apply.className = "scene-apply";
    apply.textContent = scene.name;
    apply.title = `Recall ${scene.name}: ${sceneSummary(scene)}`;
    apply.setAttribute("aria-pressed", activeScene === scene.id ? "true" : "false");
    apply.addEventListener("click", async () => {
      const data = await postJson("/api/scenes/apply", { id: scene.id });
      if (data) {
        applyScenes(data);
        for (const side of ["left", "right"]) {
          pendingAnim[side] = scene[side];
          state[`${side}_anim`] = scene[side];
          clearOverlay(side);
        }
        lastLibKey = "";
        maybeRenderLibrary();
        showMarqueeFields();
        toast(`Scene ${scene.name}`);
      }
    });
    chip.appendChild(apply);
    if (scene.schedule) {
      const when = document.createElement("span");
      when.className = "scene-when";
      when.textContent = `${scene.schedule.start}–${scene.schedule.end}`;
      when.title = `Applies itself every day from ${scene.schedule.start} to ${scene.schedule.end}`;
      chip.appendChild(when);
    }
    const update = document.createElement("button");
    update.type = "button";
    update.className = "scene-update";
    update.textContent = "↻";
    update.title = `Overwrite ${scene.name} with what is playing now`;
    update.setAttribute("aria-label", update.title);
    update.addEventListener("click", async (event) => {
      event.stopPropagation();
      const data = await postJson("/api/scenes", {
        id: scene.id,
        left: state.left_anim,
        right: state.right_anim,
        brightness: Number(brightnessEl.value),
        speed: Number(speedEl.value) / 100,
      });
      if (data) {
        applyScenes(data);
        toast(`Updated ${scene.name}`);
      }
    });
    chip.appendChild(update);
    const del = document.createElement("button");
    del.type = "button";
    del.className = "group-delete";
    del.textContent = "×";
    del.title = `Delete scene ${scene.name}`;
    del.setAttribute("aria-label", del.title);
    del.addEventListener("click", (event) => {
      event.stopPropagation();
      confirmDeleteScene = scene.id;
      lastSceneUiKey = "";
      maybeRenderScenes(true);
    });
    chip.appendChild(del);
    row.appendChild(chip);
  }

  const newBtn = document.createElement("button");
  newBtn.type = "button";
  newBtn.className = "scene-new";
  newBtn.id = "new-scene";
  newBtn.textContent = "Save scene";
  newBtn.title = "Save both wells plus brightness and speed as a named scene";
  newBtn.addEventListener("click", beginNewScene);
  row.appendChild(newBtn);
  scenesEl.appendChild(row);
}

function beginNewScene() {
  const row = scenesEl && scenesEl.querySelector(".scene-row");
  if (!row || row.querySelector(".scene-composer")) return;
  const form = document.createElement("form");
  form.className = "scene-composer";
  const name = document.createElement("input");
  name.type = "text";
  name.maxLength = 40;
  name.placeholder = "Evening";
  name.setAttribute("aria-label", "Scene name");
  const scheduleWrap = document.createElement("label");
  scheduleWrap.className = "scene-schedule";
  const scheduleOn = document.createElement("input");
  scheduleOn.type = "checkbox";
  scheduleOn.setAttribute("aria-label", "Apply this scene automatically in a daily time window");
  const scheduleText = document.createElement("span");
  scheduleText.textContent = "daily from";
  const start = document.createElement("input");
  start.type = "time";
  start.value = "22:00";
  start.disabled = true;
  start.setAttribute("aria-label", "Window start");
  const to = document.createElement("span");
  to.textContent = "to";
  const end = document.createElement("input");
  end.type = "time";
  end.value = "07:00";
  end.disabled = true;
  end.setAttribute("aria-label", "Window end");
  scheduleOn.addEventListener("change", () => {
    start.disabled = end.disabled = !scheduleOn.checked;
  });
  scheduleWrap.append(scheduleOn, scheduleText, start, to, end);
  const save = document.createElement("button");
  save.type = "submit";
  save.textContent = "Save";
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.className = "scene-cancel";
  cancel.textContent = "Cancel";
  cancel.addEventListener("click", () => {
    form.remove();
    lastSceneUiKey = "";
    maybeRenderScenes(true);
  });
  form.append(name, scheduleWrap, save, cancel);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const label = name.value.trim();
    if (!label) {
      name.focus();
      return;
    }
    const payload = {
      name: label,
      left: state.left_anim,
      right: state.right_anim,
      brightness: Number(brightnessEl.value),
      speed: Number(speedEl.value) / 100,
      schedule: scheduleOn.checked && start.value && end.value ? { start: start.value, end: end.value } : null,
    };
    const data = await postJson("/api/scenes", payload);
    form.remove();
    if (data) {
      applyScenes(data);
      toast(payload.schedule ? `Saved ${label} · ${payload.schedule.start}–${payload.schedule.end} daily` : `Saved scene ${label}`);
    }
    lastSceneUiKey = "";
    maybeRenderScenes(true);
  });
  name.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      cancel.click();
    }
  });
  const newBtn = row.querySelector(".scene-new");
  if (newBtn) row.insertBefore(form, newBtn);
  else row.appendChild(form);
  name.focus();
}

function applyIdle(info) {
  if (!info || typeof info !== "object") return;
  idleState = {
    enabled: !!info.enabled,
    minutes: Number(info.minutes) || idleState.minutes,
    dimmed: !!info.dimmed,
    effective: Number(info.effective),
  };
  if (idleBtn) {
    idleBtn.classList.toggle("on", idleState.enabled);
    idleBtn.classList.toggle("dimmed", idleState.dimmed);
    idleBtn.setAttribute("aria-pressed", idleState.enabled ? "true" : "false");
    const text = idleState.dimmed ? "Dimmed · any input wakes" : idleState.enabled ? "Idle dim · on" : "Idle dim";
    if (idleBtn.textContent !== text) idleBtn.textContent = text;
  }
  if (idleMinutesEl && document.activeElement !== idleMinutesEl) {
    idleMinutesEl.value = String(idleState.minutes);
  }
  document.body.classList.toggle("dimmed", idleState.dimmed);
}

function beginNewGroup() {
  const row = document.getElementById("group-row") || (groupsEl && groupsEl.querySelector(".group-row"));
  if (!row || row.querySelector(".group-composer")) return;
  const form = document.createElement("form");
  form.className = "group-composer";
  const input = document.createElement("input");
  input.type = "text";
  input.maxLength = 40;
  input.placeholder = "Desk mix";
  input.setAttribute("aria-label", "New group name");
  const save = document.createElement("button");
  save.type = "submit";
  save.textContent = "Add";
  form.append(input, save);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = input.value.trim();
    if (!name) {
      input.focus();
      return;
    }
    const data = await postJson("/api/groups", { name });
    form.remove();
    if (data && Array.isArray(data.groups)) {
      mergeGroups(data.groups);
    }
    if (data && data.group && data.group.id) {
      if (!groups.some((row) => row.id === data.group.id)) {
        groups = groups.concat([{ id: data.group.id, name: data.group.name, ids: data.group.ids || [] }]);
      }
      groupsStatus = "ready";
      activeGroup = "";
      selectionGroup = data.group.id;
      toast(`Created ${data.group.name} — tap cards to add`);
    }
    lastLibKey = "";
    lastGroupUiKey = "";
    maybeRenderGroups(true);
    maybeRenderLibrary();
  });
  const newBtn = row.querySelector(".group-new");
  if (newBtn) row.insertBefore(form, newBtn);
  else row.appendChild(form);
  input.focus();
}

async function loadLibrary() {
  try {
    const res = await fetch("/api/library", { cache: "no-store" });
    if (!res.ok) throw new Error("library");
    const data = await res.json();
    applyLibrary(data);
    groupsStatus = "ready";
  } catch {
    groupsStatus = "error";
  }
  lastLibKey = "";
  lastGroupUiKey = "";
  maybeRenderLibrary();
}

async function loadCatalog(rev) {
  if (catalogLoading) return catalogLoading;
  catalogLoading = (async () => {
    try {
      const res = await fetch("/api/animations", { cache: "no-store" });
      if (!res.ok) throw new Error("animations");
      const data = await res.json();
      if (Array.isArray(data.animations) && data.animations.length) {
        catalog = data.animations;
        catalogRev = data.rev || rev || "";
        lastLibKey = "";
        maybeRenderLibrary();
        showMarqueeFields();
      }
    } catch {
      /* the next frame tick retries while the rev still differs */
    } finally {
      catalogLoading = null;
    }
  })();
  return catalogLoading;
}

function clearOverlay(side) {
  overlay[side].fill(0);
  overlayOn[side].fill(0);
}

async function assign(side, id) {
  setFocus(side);
  pendingAnim[side] = id;
  state[`${side}_anim`] = id;
  clearOverlay(side);
  lastLibKey = "";
  maybeRenderLibrary();
  showMarqueeFields();
  toast(`${animName(id)} → ${sideLabel(side)}`);
  if (id === "marquee") {
    const input = side === "right" ? rightText : leftText;
    queueMicrotask(() => {
      input.focus();
      input.select();
    });
  }
  await post("/api/animation", { side, id });
}

function showMarqueeFields() {
  for (const [side, field] of [
    ["left", leftMarquee],
    ["right", rightMarquee],
  ]) {
    const on = currentAnim(side) === "marquee";
    field.classList.toggle("hidden", !on);
  }
}

function ledFromEvent(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  const pad = 8;
  const gap = 3;
  const usableW = Math.max(1, rect.width - pad * 2);
  const usableH = Math.max(1, rect.height - pad * 2);
  const cellW = (usableW - gap * (WIDTH - 1)) / WIDTH;
  const cellH = (usableH - gap * (HEIGHT - 1)) / HEIGHT;
  const strideW = cellW + gap;
  const strideH = cellH + gap;
  const x = Math.floor((event.clientX - rect.left - pad) / strideW);
  const y = Math.floor((event.clientY - rect.top - pad) / strideH);
  return {
    x: Math.max(0, Math.min(WIDTH - 1, x)),
    y: Math.max(0, Math.min(HEIGHT - 1, y)),
  };
}

function currentAnim(side) {
  return state[`${side}_anim`];
}

function paintsInk(id) {
  return ["sketch", "sand", "life"].includes(id);
}

function wantsDrag(id) {
  const item = catalogItem(id);
  if (item && item.drag) return true;
  return paintsInk(id) || [
    "pong",
    "snake",
    "breakout",
    "tetris",
    "invaders",
    "dodge",
    "frogger",
    "asteroids",
    "centipede",
    "space-shooter",
    "catcher",
    "whack",
    "slither",
    "racetrack",
    "jumper",
    "2048",
    "cannons",
    "pinball-game",
    "maze",
  ].includes(id);
}

function lineCells(x0, y0, x1, y1) {
  const cells = [];
  const dx = Math.abs(x1 - x0);
  const dy = -Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1;
  const sy = y0 < y1 ? 1 : -1;
  let err = dx + dy;
  let x = x0;
  let y = y0;
  while (true) {
    cells.push({ x, y });
    if (x === x1 && y === y1) break;
    const e2 = 2 * err;
    if (e2 >= dy) {
      err += dy;
      x += sx;
    }
    if (e2 <= dx) {
      err += dx;
      y += sy;
    }
    if (cells.length > PIXELS) break;
  }
  return cells;
}

function paintLocal(side, x, y, erase) {
  const i = y * WIDTH + x;
  const value = erase ? 0 : 255;
  overlay[side][i] = value;
  overlayOn[side][i] = 1;
  lastPixels[side][i] = value;
}

function mergeOverlay(side, pixels) {
  const out = pixels.slice();
  const on = overlayOn[side];
  const vals = overlay[side];
  for (let i = 0; i < PIXELS; i++) {
    if (on[i]) out[i] = vals[i];
  }
  return out;
}

function reconcileOverlay(side, pixels) {
  const on = overlayOn[side];
  const vals = overlay[side];
  for (let i = 0; i < PIXELS; i++) {
    if (on[i] && pixels[i] === vals[i]) on[i] = 0;
  }
}

function redraw(side) {
  const canvas = side === "right" ? rightCanvas : leftCanvas;
  const ctx = side === "right" ? rightCtx : leftCtx;
  drawMatrix(ctx, canvas, lastPixels[side]);
}

function inkStroke(side, from, to, erase) {
  const cells = from ? lineCells(from.x, from.y, to.x, to.y) : [to];
  const id = currentAnim(side);
  if (paintsInk(id)) {
    for (const cell of cells) paintLocal(side, cell.x, cell.y, erase);
    redraw(side);
  }
  const points = from ? [[from.x, from.y], [to.x, to.y]] : [[to.x, to.y]];
  post("/api/stroke", { side, points, erase });
}

function sideFromPoint(clientX, clientY) {
  for (const side of ["left", "right"]) {
    const canvas = side === "right" ? rightCanvas : leftCanvas;
    const r = canvas.getBoundingClientRect();
    if (clientX >= r.left && clientX <= r.right && clientY >= r.top && clientY <= r.bottom) {
      return side;
    }
  }
  for (const side of ["left", "right"]) {
    const bezel = side === "right" ? rightBezel : leftBezel;
    const r = bezel.getBoundingClientRect();
    if (clientX >= r.left && clientX <= r.right && clientY >= r.top && clientY <= r.bottom) {
      return side;
    }
  }
  return null;
}

function isHeld(event) {
  if (typeof event.buttons === "number") return (event.buttons & 1) !== 0 || (event.buttons & 2) !== 0;
  return !!drawing;
}

function startDraw(side, event) {
  setFocus(side, { rebuild: false });
  // pointerdown is prevented below, so the browser will not move focus itself.
  focusWell(side);
  const canvas = side === "right" ? rightCanvas : leftCanvas;
  const cell = ledFromEvent(canvas, event);
  const erase = event.shiftKey || event.button === 2 || (event.buttons & 2) !== 0;
  drawing = {
    side,
    last: cell,
    erase,
    pointerId: event.pointerId,
    paint: wantsDrag(currentAnim(side)) || currentAnim(side) === "sketch",
  };
  inkStroke(side, null, cell, erase);
}

function continueDraw(event) {
  if (!drawing) return;
  const id = currentAnim(drawing.side);
  if (!wantsDrag(id) && id !== "sketch") return;
  const canvas = drawing.side === "right" ? rightCanvas : leftCanvas;
  const cell = ledFromEvent(canvas, event);
  if (cell.x === drawing.last.x && cell.y === drawing.last.y) return;
  const erase = drawing.erase || event.shiftKey;
  inkStroke(drawing.side, drawing.last, cell, erase);
  drawing.last = cell;
}

function onDocPointerDown(event) {
  if (helpOpen()) return;
  if (event.target && event.target.closest && event.target.closest(".card, .badge, .heart, .card-add, .group-add, .selection-done, .selection-bar, .filing-banner, input, textarea, button, label, .meter, .random-btn, .search-wrap, .search-fill, .type-filter, .type-filters, .stage-tools, .groups, .group-bubble, .group-new, .group-random, .group-delete, .group-composer, .group-select, .scenes, .scene-chip, .scene-composer, .idle-ctl, .module-tools, .first-run, .toasts, .sheet-scrim")) {
    return;
  }
  if (typeof event.button === "number" && event.button === 1) return;
  const side = sideFromPoint(event.clientX, event.clientY);
  if (!side) return;
  event.preventDefault();
  startDraw(side, event);
  try {
    event.target.setPointerCapture && event.target.setPointerCapture(event.pointerId);
  } catch {
    /* window move handlers still work */
  }
}

function onDocPointerMove(event) {
  if (!isHeld(event) && !drawing) return;
  if (drawing) {
    event.preventDefault();
    continueDraw(event);
    return;
  }
  if (helpOpen()) return;
  const side = sideFromPoint(event.clientX, event.clientY);
  if (!side) return;
  startDraw(side, event);
}

function onDocPointerUp() {
  drawing = null;
}

function sendKey(side, code) {
  setFocus(side, { rebuild: false });
  if (["KeyC", "Escape", "Delete", "Backspace"].includes(code)) {
    const id = currentAnim(side);
    if (id === "sketch" || id === "sand") {
      clearOverlay(side);
      lastPixels[side] = new Array(PIXELS).fill(id === "sand" ? 6 : 0);
      redraw(side);
    }
  }
  post("/api/key", { side, code });
}

function formatBrightness(value) {
  return String(Math.round(Number(value) || 0));
}

function formatSpeed(value) {
  return `${(Number(value) / 100).toFixed(2).replace(/0$/, "")}×`;
}

function updateMeterLabels() {
  if (brightnessValue) {
    brightnessValue.textContent = idleState.dimmed
      ? `${formatBrightness(brightnessEl.value)} → ${formatBrightness(idleState.effective)}`
      : formatBrightness(brightnessEl.value);
  }
  if (speedValue) speedValue.textContent = formatSpeed(speedEl.value);
}

function setOffline(on) {
  if (on === offline) return;
  offline = on;
  document.body.classList.toggle("offline", on);
  if (on) {
    toast("Offline — retrying", { kind: "error", duration: 2200 });
  } else {
    toast("Back online");
  }
}

async function tick() {
  try {
    const res = await fetch("/api/frame", { cache: "no-store" });
    if (!res.ok) throw new Error("frame");
    const data = await res.json();
    setOffline(false);
    if (data.catalogRev && data.catalogRev !== catalogRev) {
      loadCatalog(data.catalogRev);
    } else if (!catalog.length) {
      loadCatalog("");
    }
    for (const side of ["left", "right"]) {
      const serverId = data[`${side}_anim`];
      if (pendingAnim[side] && serverId === pendingAnim[side]) {
        pendingAnim[side] = null;
      }
      if (!pendingAnim[side]) {
        state[`${side}_anim`] = serverId;
      }
    }
    state.info = data.info || {};
    for (const side of ["left", "right"]) {
      reconcileOverlay(side, data[side]);
      lastPixels[side] = mergeOverlay(side, data[side]);
    }
    drawMatrix(leftCtx, leftCanvas, lastPixels.left);
    drawMatrix(rightCtx, rightCanvas, lastPixels.right);
    drawPlayingThumbs();
    const leftLabel = animName(data.left_anim);
    const rightLabel = animName(data.right_anim);
    if (leftName.textContent !== leftLabel) leftName.textContent = leftLabel;
    if (rightName.textContent !== rightLabel) rightName.textContent = rightLabel;
    const leftHudText = hudText("left", data);
    const rightHudText = hudText("right", data);
    if (leftHud.textContent !== leftHudText) leftHud.textContent = leftHudText;
    if (rightHud.textContent !== rightHudText) rightHud.textContent = rightHudText;
    pill(leftPill, "Left", data.hardware.left);
    pill(rightPill, "Right", data.hardware.right);
    if (document.activeElement !== brightnessEl) brightnessEl.value = data.brightness;
    if (document.activeElement !== speedEl && typeof data.speed === "number") {
      speedEl.value = Math.round(data.speed * 100);
    }
    updateMeterLabels();
    if (Array.isArray(data.favorites)) favorites = new Set(data.favorites);
    if (Array.isArray(data.groups)) {
      mergeGroups(data.groups);
    }
    if ("randomGroup" in data) randomGroup = data.randomGroup || null;
    if (Array.isArray(data.scenes)) applyScenes(data);
    applyIdle(data.idle);
    if (randomBtn) {
      const globalOn = !!data.random && !data.randomGroup;
      randomBtn.classList.toggle("on", globalOn);
      randomBtn.textContent = globalOn ? "Random · on" : "Random";
      randomBtn.setAttribute("aria-pressed", globalOn ? "true" : "false");
    }
    const texts = data.text || {};
    showMarqueeFields();
    for (const [side, input] of [
      ["left", leftText],
      ["right", rightText],
    ]) {
      const isMarquee = currentAnim(side) === "marquee";
      if (isMarquee && document.activeElement !== input && typeof texts[side] === "string") {
        input.value = texts[side];
      }
    }
    maybeRenderLibrary();
    if (data.themeRev && data.themeRev !== themeRev) {
      refreshTheme(true);
    }
  } catch (err) {
    leftPill.textContent = "Left · offline";
    rightPill.textContent = "Right · offline";
    leftPill.classList.remove("live");
    rightPill.classList.remove("live");
    setOffline(true);
  }
}

function helpOpen() {
  return !!helpSheet && !helpSheet.classList.contains("hidden");
}

function renderHelp() {
  if (!helpBody) return;
  const rows = [];
  rows.push('<section class="help-section"><h3>Everywhere</h3><dl class="keys">');
  for (const [key, what] of GLOBAL_KEYS) {
    rows.push(`<div><dt><kbd>${escapeHtml(key)}</kbd></dt><dd>${escapeHtml(what)}</dd></div>`);
  }
  rows.push("</dl></section>");

  rows.push('<section class="help-section"><h3>Playing now</h3><dl class="keys">');
  for (const side of ["left", "right"]) {
    const id = currentAnim(side);
    const hint = GAME_HINTS[id] || UTILITY_KEYS[id] || "";
    const name = animName(id);
    const focused = focus === side ? " · keys go here" : "";
    rows.push(
      `<div><dt>${escapeHtml(sideLabel(side))}${escapeHtml(focused)}</dt><dd><strong>${escapeHtml(name)}</strong>${
        hint ? ` — ${escapeHtml(hint)}` : " — no keys; it just runs"
      }</dd></div>`
    );
  }
  rows.push("</dl></section>");

  rows.push('<section class="help-section"><h3>How it works</h3>');
  rows.push(
    "<p>The library is split across the two rails — first half on the left, second half on the right — so each column is half as long. A card plays on the well its rail belongs to; drag it onto either well or use the <strong>L</strong>/<strong>R</strong> badges to send it to the other side. Heart a card to favorite it. Click a group name to view it, or its <strong>+</strong> to add many cards at once. <strong>Save scene</strong> keeps both wells plus brightness and speed, with an optional daily window. <strong>Idle dim</strong> fades both wells after a quiet spell and any input brings them back. Double-click a slider to reset it.</p>"
  );
  rows.push("</section>");

  rows.push('<section class="help-section"><h3>Games</h3><dl class="keys compact">');
  for (const [id, hint] of Object.entries(GAME_HINTS)) {
    rows.push(`<div><dt>${escapeHtml(animName(id))}</dt><dd>${escapeHtml(hint)}</dd></div>`);
  }
  rows.push("</dl></section>");

  rows.push('<section class="help-section"><h3>Utilities and drawing</h3><dl class="keys compact">');
  for (const [id, hint] of Object.entries(UTILITY_KEYS)) {
    rows.push(`<div><dt>${escapeHtml(animName(id))}</dt><dd>${escapeHtml(hint)}</dd></div>`);
  }
  rows.push("</dl></section>");
  helpBody.innerHTML = rows.join("");
}

function openHelp() {
  if (!helpSheet || helpOpen()) return;
  renderHelp();
  lastReturnFocus = document.activeElement;
  helpSheet.classList.remove("hidden");
  helpSheet.setAttribute("aria-hidden", "false");
  document.body.classList.add("sheet-open");
  if (helpBtn) helpBtn.setAttribute("aria-expanded", "true");
  queueMicrotask(() => helpClose && helpClose.focus());
}

function closeHelp() {
  if (!helpSheet || !helpOpen()) return;
  helpSheet.classList.add("hidden");
  helpSheet.setAttribute("aria-hidden", "true");
  document.body.classList.remove("sheet-open");
  if (helpBtn) helpBtn.setAttribute("aria-expanded", "false");
  const back = lastReturnFocus;
  lastReturnFocus = null;
  if (back && typeof back.focus === "function" && document.contains(back)) back.focus();
  else if (helpBtn) helpBtn.focus();
}

function toggleHelp() {
  if (helpOpen()) closeHelp();
  else openHelp();
}

function hintDismissed() {
  try {
    return window.localStorage.getItem(HINT_KEY) === "1";
  } catch {
    return false;
  }
}

function dismissHint() {
  try {
    window.localStorage.setItem(HINT_KEY, "1");
  } catch {
    /* private mode: hide for this session only */
  }
  if (firstRun) firstRun.hidden = true;
}

function showHintIfFirstRun() {
  if (!firstRun) return;
  firstRun.hidden = hintDismissed();
}

async function favoritePlaying() {
  const id = currentAnim(focus);
  const item = catalogItem(id);
  if (!item) return;
  await toggleHeart(item);
}

document.addEventListener("pointerdown", onDocPointerDown, true);
document.addEventListener("pointermove", onDocPointerMove, true);
document.addEventListener("pointerup", onDocPointerUp, true);
document.addEventListener("pointercancel", onDocPointerUp, true);
document.addEventListener("mousemove", onDocPointerMove, true);
document.addEventListener("mouseup", onDocPointerUp, true);
leftBezel.addEventListener("contextmenu", (event) => event.preventDefault());
rightBezel.addEventListener("contextmenu", (event) => event.preventDefault());

// Keys a game or utility on the focused well consumes. Arrows and Space are
// prevented so the page never scrolls under a game; letters pass through to
// the server but keep their default so browser shortcuts still work.
function isGameKey(code) {
  return code === "Space" || code.startsWith("Arrow") || code === "Escape" || code === "Delete" || code === "Backspace";
}

// One global router. Order matters: text fields keep everything; the help sheet
// only owns Esc / ?; a focused button or card only owns Enter and Space; the
// handful of app shortcuts (1 2 F ?) never use a key a game needs — Simon's
// digits are forwarded — and everything else goes to the focused well.
window.addEventListener("keydown", (event) => {
  const target = event.target;
  const inField = target && (["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable);
  if (inField) {
    return;
  }
  const modified = event.ctrlKey || event.metaKey || event.altKey;
  if (helpOpen()) {
    if (event.code === "Escape" || event.key === "?") {
      event.preventDefault();
      closeHelp();
      return;
    }
    // The sheet lists the keys; let people try them on the well while it is open.
    if (modified || CONTROL_KEYS.has(event.code) || IGNORE_KEYS.has(event.code)) return;
    if (isGameKey(event.code)) event.preventDefault();
    sendKey(focus, event.code);
    return;
  }
  if (event.key === "?" && !modified) {
    event.preventDefault();
    openHelp();
    return;
  }
  const onControl = !!(target && target.closest && target.closest(".card, button, a, [role='button'], .group-bubble, .sheet-scrim"));
  // A focused button or card keeps Enter / Space (activation) and any modifier
  // combo (Alt+←/→ reorders groups). Arrows, WASD and the rest still reach the game.
  if (onControl && (CONTROL_KEYS.has(event.code) || modified)) {
    return;
  }
  if (event.code === "Escape" && selectionGroup) {
    event.preventDefault();
    exitSelectionMode();
    return;
  }
  if (event.code === "Escape" && confirmDeleteGroup) {
    event.preventDefault();
    confirmDeleteGroup = "";
    lastGroupUiKey = "";
    maybeRenderGroups();
    return;
  }
  if (event.code === "Escape" && confirmDeleteScene) {
    event.preventDefault();
    confirmDeleteScene = "";
    lastSceneUiKey = "";
    maybeRenderScenes(true);
    return;
  }
  if (modified) {
    // Ctrl/Alt/Meta combos belong to the browser (reload, tabs, menus); never a game key.
    return;
  }
  // 1 / 2 pick the key target — unless the focused well is Simon, which plays on digits.
  const digitFocus = (event.code === "Digit1" || event.code === "Digit2") && currentAnim(focus) !== "simon";
  if (digitFocus) {
    event.preventDefault();
    setFocus(event.code === "Digit1" ? "left" : "right");
    toast(`Keys → ${sideLabel(focus)}`);
    return;
  }
  if (event.code === "KeyF" && !event.shiftKey) {
    event.preventDefault();
    favoritePlaying();
    return;
  }
  if (IGNORE_KEYS.has(event.code)) return;
  if (isGameKey(event.code)) event.preventDefault();
  sendKey(focus, event.code);
});

brightnessEl.addEventListener("input", () => {
  updateMeterLabels();
  post("/api/brightness", { value: Number(brightnessEl.value) });
});
brightnessEl.addEventListener("dblclick", () => {
  brightnessEl.value = DEFAULT_BRIGHTNESS;
  updateMeterLabels();
  post("/api/brightness", { value: DEFAULT_BRIGHTNESS });
  toast(`Brightness reset to ${DEFAULT_BRIGHTNESS}`);
});

speedEl.addEventListener("input", () => {
  updateMeterLabels();
  post("/api/speed", { value: Number(speedEl.value) / 100 });
});
speedEl.addEventListener("dblclick", () => {
  speedEl.value = DEFAULT_SPEED;
  updateMeterLabels();
  post("/api/speed", { value: DEFAULT_SPEED / 100 });
  toast("Speed reset to 1.0×");
});

randomBtn.addEventListener("click", () => {
  const on = !randomBtn.classList.contains("on");
  randomBtn.classList.toggle("on", on);
  randomBtn.textContent = on ? "Random · on" : "Random";
  randomBtn.setAttribute("aria-pressed", on ? "true" : "false");
  randomGroup = null;
  lastGroupUiKey = "";
  post("/api/random", { enabled: on });
  toast(on ? "Shuffling the whole catalog" : "Shuffle off");
  maybeRenderGroups();
});

if (idleBtn) {
  idleBtn.addEventListener("click", async () => {
    const enabled = !idleState.enabled;
    const data = await postJson("/api/idle", { enabled, minutes: Number(idleMinutesEl ? idleMinutesEl.value : idleState.minutes) || idleState.minutes });
    if (data && data.idle) {
      applyIdle(data.idle);
      toast(enabled ? `Idle dim after ${data.idle.minutes} min` : "Idle dim off");
    }
  });
}
if (idleMinutesEl) {
  const commit = async () => {
    const minutes = Math.max(1, Math.min(240, Math.round(Number(idleMinutesEl.value) || idleState.minutes)));
    idleMinutesEl.value = String(minutes);
    if (minutes === idleState.minutes) return;
    const data = await postJson("/api/idle", { minutes });
    if (data && data.idle) {
      applyIdle(data.idle);
      toast(`Idle dim after ${data.idle.minutes} min`);
    }
  };
  idleMinutesEl.addEventListener("change", commit);
  idleMinutesEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      idleMinutesEl.blur();
    }
  });
}
if (helpBtn) helpBtn.addEventListener("click", toggleHelp);
if (helpClose) helpClose.addEventListener("click", closeHelp);
if (helpSheet) {
  helpSheet.addEventListener("click", (event) => {
    if (event.target === helpSheet) closeHelp();
  });
}
if (hintDismiss) hintDismiss.addEventListener("click", dismissHint);

searchEl.addEventListener("input", () => {
  searchQuery = searchEl.value;
  lastLibKey = "";
  updateSearchChrome();
  maybeRenderLibrary();
});

searchEl.addEventListener("keydown", (event) => {
  if (event.key === "Tab") {
    if (bestMatch()) {
      event.preventDefault();
      acceptSearch(false);
    }
    return;
  }
  if (event.key === "Enter") {
    event.preventDefault();
    acceptSearch(true);
    return;
  }
  if (event.key === "ArrowRight" && searchEl.selectionStart === searchEl.value.length) {
    if (bestMatch() && searchGhost.textContent) {
      event.preventDefault();
      acceptSearch(false);
    }
    return;
  }
  if (event.key === "Escape") {
    searchEl.value = "";
    searchQuery = "";
    lastLibKey = "";
    updateSearchChrome();
    maybeRenderLibrary();
    searchEl.blur();
  }
});

searchFill.addEventListener("click", () => acceptSearch(false));

function setKindFilter(kind) {
  kindFilter = kind || "";
  if (typeFilters) {
    typeFilters.querySelectorAll(".type-filter").forEach((btn) => {
      const selected = (btn.dataset.kind || "") === kindFilter;
      btn.classList.toggle("on", selected);
      btn.setAttribute("aria-pressed", selected ? "true" : "false");
    });
  }
  lastLibKey = "";
  updateSearchChrome();
  maybeRenderLibrary();
}

if (typeFilters) {
  typeFilters.addEventListener("click", (event) => {
    const btn = event.target && event.target.closest && event.target.closest(".type-filter");
    if (!btn) return;
    setKindFilter(btn.dataset.kind || "");
  });
}

function bindText(input, side) {
  const send = () => post("/api/text", { side, text: input.value });
  input.addEventListener("input", send);
  input.addEventListener("change", send);
}
bindText(leftText, "left");
bindText(rightText, "right");

function onNarrowChange(event) {
  narrow = event.matches;
  updateRailLabels();
  lastLibKey = "";
  maybeRenderLibrary();
}

document.querySelectorAll(".library-col").forEach((col) => {
  col.addEventListener("scroll", scheduleWindows, { passive: true });
});
window.addEventListener("scroll", scheduleWindows, { passive: true });
window.addEventListener("resize", () => {
  lastLibKey = "";
  maybeRenderLibrary();
  scheduleWindows();
});
bindDropTargets();
if (typeof narrowQuery.addEventListener === "function") narrowQuery.addEventListener("change", onNarrowChange);
else if (typeof narrowQuery.addListener === "function") narrowQuery.addListener(onNarrowChange);

setFocus("left");
updateMeterLabels();
showHintIfFirstRun();
const newGroupBtn = document.getElementById("new-group");
if (newGroupBtn) newGroupBtn.addEventListener("click", beginNewGroup);
const newSceneBtn = document.getElementById("new-scene");
if (newSceneBtn) newSceneBtn.addEventListener("click", beginNewScene);
loadCatalog("");
loadLibrary();
refreshTheme(true);
setInterval(() => refreshTheme(false), 3000);

function loop() {
  tick().finally(() => setTimeout(loop, 50));
}

loop();
