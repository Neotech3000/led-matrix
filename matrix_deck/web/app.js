const WIDTH = 9;
const HEIGHT = 34;
const leftCanvas = document.getElementById("left");
const rightCanvas = document.getElementById("right");
const scoreEl = document.getElementById("score");
const bestEl = document.getElementById("best");
const pilotEl = document.getElementById("pilot");
const leftPill = document.getElementById("left-pill");
const rightPill = document.getElementById("right-pill");
const brightnessEl = document.getElementById("brightness");

const leftCtx = leftCanvas.getContext("2d");
const rightCtx = rightCanvas.getContext("2d");

(function buildKeys() {
  const root = document.getElementById("keys");
  if (!root) return;
  const rows = [
    { n: 15, cls: "fn" },
    { n: 14, extra: [0, 13] },
    { n: 14, extra: [0, 13] },
    { n: 13, extra: [0, 12] },
    { n: 12, extra: [0, 11] },
  ];
  for (const row of rows) {
    const el = document.createElement("div");
    el.className = "key-row";
    for (let i = 0; i < row.n; i++) {
      const key = document.createElement("span");
      key.className = "key";
      if (row.cls) key.classList.add(row.cls);
      if (row.extra && row.extra.includes(i)) key.classList.add(i === row.extra[0] ? "wide" : "wider");
      el.appendChild(key);
    }
    root.appendChild(el);
  }
})();

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
  const live = value && value !== "simulated" && value !== "disconnected" && value !== "error";
  el.classList.toggle("live", !!live);
  const short = String(value || "simulated").replace(/^.*\//, "");
  el.textContent = `${side} · ${short}`;
}

async function tick() {
  try {
    const res = await fetch("/api/frame", { cache: "no-store" });
    if (!res.ok) throw new Error("frame");
    const data = await res.json();
    drawMatrix(leftCtx, leftCanvas, data.left);
    drawMatrix(rightCtx, rightCanvas, data.right);
    scoreEl.textContent = data.score;
    bestEl.textContent = data.best;
    pilotEl.textContent = data.alive ? (data.auto ? "AUTO" : "YOU") : "CRASH";
    pill(leftPill, "Left", data.hardware.left);
    pill(rightPill, "Right", data.hardware.right);
    if (document.activeElement !== brightnessEl) {
      brightnessEl.value = data.brightness;
    }
  } catch (err) {
    leftPill.textContent = "Left · offline";
    rightPill.textContent = "Right · offline";
  }
}

async function flap() {
  await fetch("/api/flap", { method: "POST" });
}

document.getElementById("flap-target").addEventListener("pointerdown", (event) => {
  event.preventDefault();
  flap();
});

window.addEventListener("keydown", (event) => {
  if (event.code === "Space" || event.key === " ") {
    event.preventDefault();
    flap();
  }
});

brightnessEl.addEventListener("change", async () => {
  await fetch("/api/brightness", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value: Number(brightnessEl.value) }),
  });
});

function loop() {
  tick().finally(() => setTimeout(loop, 50));
}

loop();
