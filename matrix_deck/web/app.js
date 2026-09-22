const WIDTH = 9;
const HEIGHT = 34;
const PIXELS = WIDTH * HEIGHT;
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
const randomBtn = document.getElementById("random-btn");
const searchEl = document.getElementById("search");
const searchGhost = document.getElementById("search-ghost");
const searchFill = document.getElementById("search-fill");
const typeFilters = document.getElementById("type-filters");
const groupsEl = document.getElementById("groups");
const libraryLeft = document.getElementById("library-left");
const libraryRight = document.getElementById("library-right");
const leftText = document.getElementById("left-text");
const rightText = document.getElementById("right-text");
const leftMarquee = document.getElementById("left-marquee");
const rightMarquee = document.getElementById("right-marquee");

let catalog = [];
let searchQuery = "";
let kindFilter = "";
let favorites = new Set();
let groups = [];
let activeGroup = "";
let selectionGroup = "";
let groupsStatus = "loading";
let randomGroup = null;
let lastGroupUiKey = "";
let focus = "left";
let drawing = null;
let inputQueue = Promise.resolve();
let lastLibKey = "";
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
const overlay = {
  left: new Uint8Array(PIXELS),
  right: new Uint8Array(PIXELS),
};
const overlayOn = {
  left: new Uint8Array(PIXELS),
  right: new Uint8Array(PIXELS),
};

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

function hudText(side, data) {
  const id = data[`${side}_anim`];
  const info = (data.info && data.info[side]) || {};
  const item = catalog.find((c) => c.id === id);
  if (id === "flappy") {
    const pilot = info.alive ? (info.auto ? "AUTO" : "YOU") : "CRASH";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · click, space, or ↑ to flap`;
  }
  if (id === "snake") {
    const pilot = info.alive ? (info.auto ? "AUTO until you steer" : "YOU") : "DEAD";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · tap a side of the well, or arrows / WASD`;
  }
  if (id === "pong") {
    const pilot = info.auto ? "AUTO" : "YOU";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · you are the bright bottom paddle · drag or ← →`;
  }
  if (id === "pong" || id === "breakout" || id === "dodge" || id === "tetris" || id === "invaders") {
    const pilot = info.auto ? "AUTO" : "YOU";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · click, drag, or arrows`;
  }
  if (id === "dino") {
    const pilot = info.alive ? (info.auto ? "AUTO" : "YOU") : "HIT";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · click, Space, or ↑`;
  }
  const GAME_HINTS = {
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
    simon: "click the quadrant that just flashed",
    rhythm: "hit notes on the line · space / click lane",
    cannons: "tap to burst incoming missiles",
    "pinball-game": "drag or space to kick the flipper",
  };
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
  const UTILITY_HINTS = {
    timer: `${info.running ? "RUN" : info.done ? "DONE" : "PAUSE"} ${info.remaining || "01:00"} · click/space start-pause · up/down or +/- add 30s · C/R reset to 60s`,
    pomodoro: `${(info.phase || "work").toUpperCase()} ${info.remaining || ""} · click/space start-pause · C/R reset · 25 then 5`,
    stopwatch: `${info.running ? "RUN" : "PAUSE"} ${info.elapsed || "00:00"} · click/space start-pause · C/R zero`,
    utc: `UTC ${info.time || ""} · same stacked digits as Clock`,
    date: `${info.weekday || ""} ${info.date || ""}`,
    "week-number": `ISO week ${info.week ?? ""} · ${info.year ?? ""}`,
    "fuzzy-clock": info.words ? `${info.words} · ${info.time || ""}` : "Time in words, nearest five minutes",
    "binary-clock": `Binary ${info.time || ""} · H M S as bit columns`,
    "seconds-bar": `Second ${info.second ?? ""} · column fills through the minute`,
    alarm: `${info.time || ""} · flashes at :00 of each minute`,
    "tap-tempo": `${info.bpm || 0} BPM · tap or space · C resets`,
    "battery-bar": `${info.percent ?? "?"} percent${info.live ? "" : " (simulated)"}`,
    "cpu-pulse": `Load ${info.load ?? "sim"} · nine bars`,
    "moon-phase": `${info.phase || ""} · real synodic phase`,
    dice: `Rolled ${info.value ?? 6} · click or space to roll`,
    "coin-flip": `${info.side || "heads"} · click or space to toss`,
    progress: `${info.percent ?? 0} percent · click +5 · ↑↓ · C zeros`,
    "chess-clock": `${info.white || "05:00"} / ${info.black || "05:00"} · ${info.active || "white"} · click/space punch · C/R reset`,
    "breath-pacer": `${info.phase || "IN"} · box breathing 4-4-4-4 on the wall clock`,
    "water-reminder": info.due ? "SIP · click when you drank" : `${info.remaining || ""} until a sip · click logged it · ↑↓ interval`,
    "focus-bar": `${info.running ? "RUN" : "PAUSE"} ${info.remaining || ""} of ${info.duration_min ?? 50} min · click start · ↑↓ length · C/R reset`,
  };
  if (UTILITY_HINTS[id]) return UTILITY_HINTS[id];
  return item ? item.description : "";
}

function setFocus(side, { rebuild = true } = {}) {
  focus = side;
  document.querySelectorAll(".module").forEach((mod) => {
    mod.classList.toggle("focused", mod.dataset.side === side);
  });
  if (rebuild) {
    lastLibKey = "";
    maybeRenderLibrary();
  }
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
}

function maybeRenderLibrary() {
  const favKey = [...favorites].sort().join(",");
  const groupKey = groups.map((group) => `${group.id}:${group.name}:${(group.ids || []).join("+")}`).join(";");
  const key = `${state.left_anim}|${state.right_anim}|${focus}|${searchQuery}|${kindFilter}|${activeGroup}|${selectionGroup}|${favKey}|${groupKey}|${groupsStatus}|${catalog.map((c) => c.id).join(",")}`;
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
  // Viewing a group filters to its ids. Selection mode does not — adding to an
  // empty group does not require a library filter; keep All/type/search.
  if (activeGroup && !selectionGroup) {
    const group = activeGroupRecord();
    const ids = groupIds(group);
    if (group) {
      const want = new Set(ids);
      items = items.filter((item) => want.has(item.id));
    }
  }
  return items;
}

function emptyLibraryMessage() {
  if (kindFilter === "favorites" && favorites.size === 0 && !activeGroup) {
    return "No favorites yet. Tap the heart on a card.";
  }
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

function renderLibrary() {
  if (!catalog.length) return;
  const q = searchQuery.trim();
  if (!q) {
    const items = visibleCatalog();
    const mid = Math.ceil(items.length / 2);
    fillLibrary(libraryLeft, items.slice(0, mid), "left");
    fillLibrary(libraryRight, items.slice(mid), "right");
    return;
  }
  const items = rankedCatalog().map((row) => row.item);
  fillLibrary(libraryLeft, items, "left", true);
  fillLibrary(libraryRight, items, "right", true);
}

function fillLibrary(root, items, clickSide, searching = false) {
  root.innerHTML = "";
  if (!items.length) {
    if (clickSide === "right" && !searching) return;
    const empty = document.createElement("p");
    empty.className = "empty-search";
    empty.textContent = emptyLibraryMessage();
    root.appendChild(empty);
    return;
  }
  const topId = searching && items[0] ? items[0].id : null;
  for (const item of items) {
    const card = document.createElement("article");
    card.className = "card";
    const onThis = state[`${clickSide}_anim`] === item.id;
    if (onThis) card.classList.add("active");
    if (topId && item.id === topId) card.classList.add("suggest");
    const leftOn = state.left_anim === item.id;
    const rightOn = state.right_anim === item.id;

    const title = document.createElement("h3");
    title.textContent = item.name;
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
      badge.addEventListener("click", (event) => {
        event.stopPropagation();
        assign(side, item.id);
      });
      badges.appendChild(badge);
    }

    card.append(title, blurb, badges);
    card.addEventListener("click", () => {
      if (selectionGroup) {
        const group = selectionGroupRecord();
        const inGroup = groupIds(group).includes(item.id);
        toggleGroupItem(item, !inGroup);
        return;
      }
      assign(clickSide, item.id);
    });
    root.appendChild(card);
  }
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
    if (!res.ok) throw new Error("post");
    return await res.json();
  } catch {
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
  return group ? `Adding to ${group.name} — tap cards to add` : "";
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
  if (selectionGroup) {
    setGroupMembership(selectionGroupRecord(), item.id, on);
  }
  lastLibKey = "";
  maybeRenderLibrary();
  const fav = await postJson("/api/favorite", { id: item.id, on });
  if (fav) applyLibrary(fav);
  if (selectionGroup) {
    const filed = await postJson("/api/groups/item", { groupId: selectionGroup, animId: item.id, on });
    if (filed) applyLibrary(filed);
  }
  lastLibKey = "";
  maybeRenderLibrary();
}

async function toggleGroupItem(item, on) {
  if (!selectionGroup) return;
  setGroupMembership(selectionGroupRecord(), item.id, on);
  lastLibKey = "";
  maybeRenderLibrary();
  const filed = await postJson("/api/groups/item", { groupId: selectionGroup, animId: item.id, on });
  if (filed) applyLibrary(filed);
  lastLibKey = "";
  maybeRenderLibrary();
}

function maybeRenderGroups(force = false) {
  if (!force && document.querySelector(".group-composer")) return;
  const key = `${groupsStatus}|${activeGroup}|${selectionGroup}|${randomGroup || ""}|${groups.map((group) => `${group.id}:${group.name}:${(group.ids || []).join("+")}`).join(",")}`;
  if (!force && key === lastGroupUiKey) return;
  lastGroupUiKey = key;
  renderGroups();
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

    const select = document.createElement("button");
    select.type = "button";
    select.className = "group-select";
    select.textContent = `${group.name} · ${(group.ids || []).length}`;
    select.title = `Show ${group.name}`;
    select.addEventListener("click", () => {
      openGroupView(group.id);
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
      } else {
        randomGroup = enabled ? group.id : null;
      }
      lastGroupUiKey = "";
      maybeRenderGroups();
    });

    const del = document.createElement("button");
    del.type = "button";
    del.className = "group-delete";
    del.textContent = "×";
    del.setAttribute("aria-label", `Delete ${group.name}`);
    del.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (!window.confirm(`Delete ${group.name}?`)) return;
      const data = await postJson("/api/groups/delete", { id: group.id });
      if (data && Array.isArray(data.groups)) groups = data.groups;
      else groups = groups.filter((row) => row.id !== group.id);
      if (activeGroup === group.id) activeGroup = "";
      if (selectionGroup === group.id) selectionGroup = "";
      if (randomGroup === group.id) randomGroup = null;
      lastLibKey = "";
      lastGroupUiKey = "";
      maybeRenderLibrary();
    });

    bubble.append(select, add, rand, del);
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
    } else if (!data) {
      groupsStatus = "error";
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
  for (const [side, input, field] of [
    ["left", leftText, leftMarquee],
    ["right", rightText, rightMarquee],
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
  const item = catalog.find((c) => c.id === id);
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
  if (event.target && event.target.closest && event.target.closest(".card, .badge, .heart, .card-add, .group-add, .selection-done, .selection-bar, .filing-banner, input, textarea, .meter, .random-btn, .search-wrap, .search-fill, .type-filter, .type-filters, .stage-tools, .groups, .group-bubble, .group-new, .group-random, .group-delete, .group-composer, .group-select")) {
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

async function tick() {
  try {
    const res = await fetch("/api/frame", { cache: "no-store" });
    if (!res.ok) throw new Error("frame");
    const data = await res.json();
    if (data.catalog && data.catalog.length) {
      catalog = data.catalog;
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
    const leftItem = catalog.find((c) => c.id === data.left_anim);
    const rightItem = catalog.find((c) => c.id === data.right_anim);
    leftName.textContent = leftItem ? leftItem.name : data.left_anim;
    rightName.textContent = rightItem ? rightItem.name : data.right_anim;
    leftHud.textContent = hudText("left", data);
    rightHud.textContent = hudText("right", data);
    pill(leftPill, "Left", data.hardware.left);
    pill(rightPill, "Right", data.hardware.right);
    if (document.activeElement !== brightnessEl) brightnessEl.value = data.brightness;
    if (document.activeElement !== speedEl && typeof data.speed === "number") {
      speedEl.value = Math.round(data.speed * 100);
    }
    if (Array.isArray(data.favorites)) favorites = new Set(data.favorites);
    if (Array.isArray(data.groups)) {
      mergeGroups(data.groups);
    }
    if ("randomGroup" in data) randomGroup = data.randomGroup || null;
    if (randomBtn) {
      const globalOn = !!data.random && !data.randomGroup;
      randomBtn.classList.toggle("on", globalOn);
      randomBtn.textContent = globalOn ? "Random · on" : "Random";
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
  } catch (err) {
    leftPill.textContent = "Left · offline";
    rightPill.textContent = "Right · offline";
  }
}

document.addEventListener("pointerdown", onDocPointerDown, true);
document.addEventListener("pointermove", onDocPointerMove, true);
document.addEventListener("pointerup", onDocPointerUp, true);
document.addEventListener("pointercancel", onDocPointerUp, true);
document.addEventListener("mousemove", onDocPointerMove, true);
document.addEventListener("mouseup", onDocPointerUp, true);
leftBezel.addEventListener("contextmenu", (event) => event.preventDefault());
rightBezel.addEventListener("contextmenu", (event) => event.preventDefault());

window.addEventListener("keydown", (event) => {
  if (event.target && ["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) {
    return;
  }
  if (event.code === "Escape" && selectionGroup) {
    event.preventDefault();
    exitSelectionMode();
    return;
  }
  if (IGNORE_KEYS.has(event.code)) return;
  if (
    event.code === "Space" ||
    event.code.startsWith("Arrow") ||
    event.code === "Escape" ||
    event.code === "Delete" ||
    event.code === "Backspace"
  ) {
    event.preventDefault();
  }
  sendKey(focus, event.code);
});

brightnessEl.addEventListener("input", () => {
  post("/api/brightness", { value: Number(brightnessEl.value) });
});

speedEl.addEventListener("input", () => {
  post("/api/speed", { value: Number(speedEl.value) / 100 });
});

randomBtn.addEventListener("click", () => {
  const on = !randomBtn.classList.contains("on");
  randomBtn.classList.toggle("on", on);
  randomBtn.textContent = on ? "Random · on" : "Random";
  randomGroup = null;
  lastGroupUiKey = "";
  post("/api/random", { enabled: on });
  maybeRenderGroups();
});

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
  typeFilters.addEventListener("pointerdown", (event) => {
    if (event.target && event.target.closest && event.target.closest(".type-filter")) {
      event.preventDefault();
    }
  });
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

setFocus("left");
const newGroupBtn = document.getElementById("new-group");
if (newGroupBtn) newGroupBtn.addEventListener("click", beginNewGroup);
loadLibrary();

function loop() {
  tick().finally(() => setTimeout(loop, 50));
}

loop();
