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
const libraryLeft = document.getElementById("library-left");
const libraryRight = document.getElementById("library-right");
const focusLabel = document.getElementById("focus-label");
const leftPlay = document.getElementById("left-play");
const rightPlay = document.getElementById("right-play");
const leftText = document.getElementById("left-text");
const rightText = document.getElementById("right-text");
const leftMarquee = document.getElementById("left-marquee");
const rightMarquee = document.getElementById("right-marquee");

let catalog = [];
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
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · tap a side of the well, arrows, WASD, or the pad`;
  }
  if (id === "pong") {
    const pilot = info.auto ? "AUTO" : "YOU";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · you are the bright bottom paddle · drag or ← →`;
  }
  if (id === "pong" || id === "breakout" || id === "dodge" || id === "tetris" || id === "invaders") {
    const pilot = info.auto ? "AUTO" : "YOU";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · pad / keys / drag`;
  }
  if (id === "dino") {
    const pilot = info.alive ? (info.auto ? "AUTO" : "YOU") : "HIT";
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · click, Space, or Flap`;
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
    return "Type in the field under this well. Letters fill every column except the two on the sides.";
  }
  if (id === "ecg") {
    return "A scrolling EKG trace — P wave, QRS spike, T wave. No heart icon.";
  }
  if (id === "hearts") {
    return "Hearts falling down the well.";
  }
  return item ? item.description : "";
}

function setFocus(side, { rebuild = true } = {}) {
  focus = side;
  focusLabel.textContent = side;
  document.querySelectorAll(".side-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.focus === side);
  });
  document.querySelectorAll(".module").forEach((mod) => {
    mod.classList.toggle("focused", mod.dataset.side === side);
  });
  if (rebuild) {
    lastLibKey = "";
    maybeRenderLibrary();
  }
}

function maybeRenderLibrary() {
  const key = `${state.left_anim}|${state.right_anim}|${focus}|${catalog.map((c) => c.id).join(",")}`;
  if (key === lastLibKey) return;
  lastLibKey = key;
  renderLibrary();
}

function kindLabel(kind) {
  if (kind === "game") return "Game";
  if (kind === "sketch") return "Draw";
  return "Loop";
}

function renderLibrary() {
  if (!catalog.length) return;
  const mid = Math.ceil(catalog.length / 2);
  fillLibrary(libraryLeft, catalog.slice(0, mid), "left");
  fillLibrary(libraryRight, catalog.slice(mid), "right");
}

function fillLibrary(root, items, clickSide) {
  root.innerHTML = "";
  for (const item of items) {
    const card = document.createElement("article");
    card.className = "card";
    const onThis = state[`${clickSide}_anim`] === item.id;
    if (onThis) card.classList.add("active");
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
    card.addEventListener("click", () => assign(clickSide, item.id));
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
  await post("/api/animation", { side, id });
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
  return paintsInk(id) || ["pong", "snake", "breakout", "tetris", "invaders", "dodge"].includes(id);
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
  if (event.target && event.target.closest && event.target.closest(".play-btn, .card, .badge, input, textarea, .side-btn, .meter")) {
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

function playButtons(id) {
  if (id === "flappy" || id === "dino") return [["Space", "Flap"]];
  if (id === "snake") {
    return [
      ["ArrowLeft", "←"],
      ["ArrowUp", "↑"],
      ["ArrowDown", "↓"],
      ["ArrowRight", "→"],
    ];
  }
  if (id === "pong" || id === "breakout" || id === "dodge") {
    return [
      ["ArrowLeft", "←"],
      ["ArrowRight", "→"],
    ];
  }
  if (id === "tetris") {
    return [
      ["ArrowLeft", "←"],
      ["ArrowUp", "↻"],
      ["ArrowRight", "→"],
      ["ArrowDown", "↓"],
    ];
  }
  if (id === "invaders") {
    return [
      ["ArrowLeft", "←"],
      ["Space", "Fire"],
      ["ArrowRight", "→"],
    ];
  }
  if (id === "life" || id === "langton") return [["KeyR", "Reseed"], ["KeyP", "Pause"]];
  if (id === "sketch" || id === "sand") return [["KeyC", "Clear"]];
  return [];
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

let lastPlay = "";

function bindHold(btn, side, code) {
  let timer = null;
  const fire = () => sendKey(side, code);
  const stop = () => {
    if (timer) clearInterval(timer);
    timer = null;
  };
  btn.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    try {
      btn.setPointerCapture(event.pointerId);
    } catch {
      /* pointerup still fires on the button */
    }
    fire();
    timer = setInterval(fire, 85);
  });
  btn.addEventListener("pointerup", stop);
  btn.addEventListener("pointercancel", stop);
  btn.addEventListener("lostpointercapture", stop);
}

function renderPlaybars() {
  const key = `${state.left_anim}|${state.right_anim}`;
  if (key === lastPlay) return;
  lastPlay = key;
  for (const [side, el] of [
    ["left", leftPlay],
    ["right", rightPlay],
  ]) {
    el.innerHTML = "";
    for (const [code, label] of playButtons(currentAnim(side))) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "play-btn";
      btn.textContent = label;
      bindHold(btn, side, code);
      el.appendChild(btn);
    }
  }
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
    const texts = data.text || {};
    for (const [side, input, field] of [
      ["left", leftText, leftMarquee],
      ["right", rightText, rightMarquee],
    ]) {
      const isMarquee = currentAnim(side) === "marquee";
      field.classList.toggle("hidden", !isMarquee);
      if (isMarquee && document.activeElement !== input && typeof texts[side] === "string") {
        input.value = texts[side];
      }
    }
    maybeRenderLibrary();
    renderPlaybars();
  } catch (err) {
    leftPill.textContent = "Left · offline";
    rightPill.textContent = "Right · offline";
  }
}

document.querySelectorAll(".side-btn").forEach((btn) => {
  btn.addEventListener("click", () => setFocus(btn.dataset.focus));
});

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

function bindText(input, side) {
  const send = () => post("/api/text", { side, text: input.value });
  input.addEventListener("input", send);
  input.addEventListener("change", send);
}
bindText(leftText, "left");
bindText(rightText, "right");

setFocus("left");

function loop() {
  tick().finally(() => setTimeout(loop, 50));
}

loop();
