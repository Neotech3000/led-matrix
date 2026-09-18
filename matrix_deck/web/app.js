const WIDTH = 9;
const HEIGHT = 34;
const leftCanvas = document.getElementById("left");
const rightCanvas = document.getElementById("right");
const leftCtx = leftCanvas.getContext("2d");
const rightCtx = rightCanvas.getContext("2d");
const leftPill = document.getElementById("left-pill");
const rightPill = document.getElementById("right-pill");
const leftName = document.getElementById("left-name");
const rightName = document.getElementById("right-name");
const leftHud = document.getElementById("left-hud");
const rightHud = document.getElementById("right-hud");
const brightnessEl = document.getElementById("brightness");
const libraryEl = document.getElementById("library");
const focusLabel = document.getElementById("focus-label");

let catalog = [];
let focus = "left";
let state = {
  left_anim: "flappy",
  right_anim: "fishtank",
  info: { left: {}, right: {} },
};

function drawMatrix(ctx, canvas, pixels) {
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth || 126;
  const cssH = Math.round(cssW * (HEIGHT / WIDTH) * 0.92);
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
    return `Score ${info.score ?? 0} · Best ${info.best ?? 0} · ${pilot} · click or space to flap`;
  }
  if (id === "sketch") return "Click a LED to draw. Hold Shift to erase.";
  return item ? item.description : "";
}

function setFocus(side) {
  focus = side;
  focusLabel.textContent = side;
  document.querySelectorAll(".side-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.focus === side);
  });
  document.querySelectorAll(".module").forEach((mod) => {
    mod.classList.toggle("focused", mod.dataset.side === side);
  });
  lastLibKey = "";
  maybeRenderLibrary();
}

let lastLibKey = "";

function maybeRenderLibrary() {
  const key = `${state.left_anim}|${state.right_anim}|${focus}|${catalog.map((c) => c.id).join(",")}`;
  if (key === lastLibKey) return;
  lastLibKey = key;
  renderLibrary();
}

function renderLibrary() {
  if (!catalog.length) return;
  libraryEl.innerHTML = "";
  for (const item of catalog) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "card";
    const onFocus = state[`${focus}_anim`] === item.id;
    if (onFocus) card.classList.add("active");
    const leftOn = state.left_anim === item.id;
    const rightOn = state.right_anim === item.id;
    card.innerHTML = `
      <h3>${item.name}</h3>
      <p>${item.description}</p>
      <div class="badges">
        <span class="badge ${leftOn ? "on" : ""}">L</span>
        <span class="badge ${rightOn ? "on" : ""}">R</span>
      </div>`;
    card.addEventListener("click", () => choose(item.id));
    libraryEl.appendChild(card);
  }
}

async function choose(id) {
  await fetch("/api/animation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ side: focus, id }),
  });
  state[`${focus}_anim`] = id;
  lastLibKey = "";
  maybeRenderLibrary();
}

function ledFromEvent(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  const pad = 8;
  const gap = 3;
  const usableW = rect.width - pad * 2;
  const usableH = rect.height - pad * 2;
  const cellW = (usableW - gap * (WIDTH - 1)) / WIDTH;
  const cellH = (usableH - gap * (HEIGHT - 1)) / HEIGHT;
  const x = Math.floor((event.clientX - rect.left - pad) / (cellW + gap));
  const y = Math.floor((event.clientY - rect.top - pad) / (cellH + gap));
  return {
    x: Math.max(0, Math.min(WIDTH - 1, x)),
    y: Math.max(0, Math.min(HEIGHT - 1, y)),
  };
}

async function onMatrixPointer(side, event) {
  event.preventDefault();
  setFocus(side);
  const canvas = side === "right" ? rightCanvas : leftCanvas;
  const { x, y } = ledFromEvent(canvas, event);
  await fetch("/api/click", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ side, x, y, erase: event.shiftKey || event.button === 2 }),
  });
}

async function tick() {
  try {
    const res = await fetch("/api/frame", { cache: "no-store" });
    if (!res.ok) throw new Error("frame");
    const data = await res.json();
    if (data.catalog && data.catalog.length) {
      catalog = data.catalog;
    }
    state.left_anim = data.left_anim;
    state.right_anim = data.right_anim;
    state.info = data.info || {};
    drawMatrix(leftCtx, leftCanvas, data.left);
    drawMatrix(rightCtx, rightCanvas, data.right);
    const leftItem = catalog.find((c) => c.id === data.left_anim);
    const rightItem = catalog.find((c) => c.id === data.right_anim);
    leftName.textContent = leftItem ? leftItem.name : data.left_anim;
    rightName.textContent = rightItem ? rightItem.name : data.right_anim;
    leftHud.textContent = hudText("left", data);
    rightHud.textContent = hudText("right", data);
    pill(leftPill, "Left", data.hardware.left);
    pill(rightPill, "Right", data.hardware.right);
    if (document.activeElement !== brightnessEl) brightnessEl.value = data.brightness;
    maybeRenderLibrary();
  } catch (err) {
    leftPill.textContent = "Left · offline";
    rightPill.textContent = "Right · offline";
  }
}

document.querySelectorAll(".side-btn").forEach((btn) => {
  btn.addEventListener("click", () => setFocus(btn.dataset.focus));
});

leftCanvas.addEventListener("pointerdown", (event) => onMatrixPointer("left", event));
rightCanvas.addEventListener("pointerdown", (event) => onMatrixPointer("right", event));
document.getElementById("left-bezel").addEventListener("contextmenu", (e) => e.preventDefault());
document.getElementById("right-bezel").addEventListener("contextmenu", (e) => e.preventDefault());

window.addEventListener("keydown", (event) => {
  if (event.code === "Space" || event.key === " ") {
    event.preventDefault();
    fetch("/api/click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ side: focus }),
    });
  }
});

brightnessEl.addEventListener("input", async () => {
  await fetch("/api/brightness", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value: Number(brightnessEl.value) }),
  });
});

setFocus("left");

function loop() {
  tick().finally(() => setTimeout(loop, 50));
}

loop();
