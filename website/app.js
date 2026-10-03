const angle = document.getElementById("angle");
const angleValue = document.getElementById("angleValue");
const mode = document.getElementById("mode");
const statusBox = document.getElementById("status");
const details = document.getElementById("details");

angle.addEventListener("input", () => {
  angleValue.textContent = angle.value + "°";
});

document.getElementById("loadBtn").addEventListener("click", loadResult);
mode.addEventListener("change", loadResult);
window.addEventListener("load", loadResult);

async function loadResult() {
  const a = Number(angle.value);
  const m = mode.value;

  statusBox.textContent = `Loading ${a}°...`;

  try {
    const response = await fetch(`/api/result?mode=${encodeURIComponent(m)}&angle=${a}`);

    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error("The server did not return JSON. Did you start server.py?");
    }

    if (!response.ok) {
      throw new Error(
        (data.error || "Could not load result") +
        (data.expected_file ? `\nExpected file: ${data.expected_file}` : "")
      );
    }

    updateDashboard(data);
    statusBox.textContent = `Loaded: ${a}°`;
  } catch (err) {
    statusBox.textContent = "Error";
    details.textContent =
      "Could not load the result.\n\n" +
      err.message +
      "\n\nSTEP 1: Open PowerShell in your LEO project folder.\n" +
      "STEP 2: Run: python website/server.py\n" +
      "STEP 3: Open: http://127.0.0.1:8000\n\n" +
      "Also check that your results folder contains the JSON files.";
  }
}

function average(arr) {
  if (!Array.isArray(arr) || !arr.length) return 0;
  return arr.reduce((a, b) => a + Number(b), 0) / arr.length;
}

function uniqueCount(arr) {
  return Array.isArray(arr) ? new Set(arr).size : 0;
}

function updateDashboard(d) {
  window.lastDashboardData = d;
  const snr = Array.isArray(d.snr) ? d.snr : [];
  const sinr = Array.isArray(d.sinr) ? d.sinr : [];
  const beams = Array.isArray(d.beam_index) ? d.beam_index : [];

  document.getElementById("requested").textContent =
    `${d.requested_elevation_angle ?? "--"}°`;

  document.getElementById("actual").textContent =
    `${Number(d.elevation_angle ?? 0).toFixed(2)}°`;

  document.getElementById("users").textContent =
    d.n_user ?? snr.length;

  document.getElementById("avgSnr").textContent =
    `${average(snr).toFixed(2)} dB`;

  document.getElementById("avgSinr").textContent =
    `${average(sinr).toFixed(2)} dB`;

  document.getElementById("beams").textContent =
    uniqueCount(beams);

  drawDistribution("snrChart", snr, "SNR (dB)");
  drawDistribution("sinrChart", sinr, "SINR (dB)");
  drawMap("mapChart", d);
  drawDistribution(
    "gainChart",
    d.center_beam_gain_dB || [],
    "Beam Gain (dB)"
  );

  details.textContent = JSON.stringify({
    requested_elevation_angle: d.requested_elevation_angle,
    actual_elevation_angle: d.elevation_angle,
    frame_index: d.frame_index,
    users: d.n_user,
    footprint_m: d.r_footprint,
    satellite_position: d.satellite_position,
    number_of_beam_centers: d.beam_centers?.length
  }, null, 2);
}

function prepareCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(300, Math.floor(rect.width));
  const height = Math.max(280, Math.floor(rect.height));

  // IMPORTANT:
  // Setting canvas.width/height clears the canvas, so do it BEFORE drawing.
  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext("2d");
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  return ctx;
}

function drawDistribution(id, values, xLabel) {
  const c = document.getElementById(id);
  const ctx = prepareCanvas(c);

  ctx.clearRect(0, 0, c.width, c.height);

  if (!values || !values.length) {
    ctx.fillStyle = "#68738a";
    ctx.font = "14px Arial";
    ctx.fillText("No data available", 30, 40);
    return;
  }

  const sorted = values.map(Number).sort((a, b) => a - b);

  const pad = { l: 55, r: 25, t: 30, b: 50 };
  const w = c.width - pad.l - pad.r;
  const h = c.height - pad.t - pad.b;

  const min = Math.min(...sorted);
  const max = Math.max(...sorted);
  const span = (max - min) || 1;

  // Axes
  ctx.strokeStyle = "#ccd3df";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad.l, pad.t);
  ctx.lineTo(pad.l, pad.t + h);
  ctx.lineTo(pad.l + w, pad.t + h);
  ctx.stroke();

  // ECDF curve
  ctx.beginPath();

  sorted.forEach((v, i) => {
    const x = pad.l + ((v - min) / span) * w;
    const y = pad.t + h - (i / (sorted.length - 1 || 1)) * h;

    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });

  ctx.strokeStyle = "#14213d";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.fillStyle = "#68738a";
  ctx.font = "12px Arial";

  ctx.fillText(min.toFixed(1), pad.l, pad.t + h + 22);
  ctx.fillText(max.toFixed(1), pad.l + w - 35, pad.t + h + 22);

  ctx.fillText("Cumulative probability", pad.l, 18);
  ctx.fillText(xLabel, pad.l + w / 2 - 35, c.height - 10);
}

function drawMap(id, d) {
  const c = document.getElementById(id);
  const ctx = prepareCanvas(c);

  const pos = d.user_positions || [[], [], []];
  const xs = pos[0] || [];
  const ys = pos[1] || [];

  const n = Math.min(xs.length, ys.length, 1500);

  if (!n) {
    ctx.fillStyle = "#68738a";
    ctx.font = "14px Arial";
    ctx.fillText("No user position data available", 30, 40);
    return;
  }

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const sx = (maxX - minX) || 1;
  const sy = (maxY - minY) || 1;

  const p = 45;
  const w = c.width - 2 * p;
  const h = c.height - 2 * p;

  // Map boundary
  ctx.strokeStyle = "#d9dee8";
  ctx.lineWidth = 1;
  ctx.strokeRect(p, p, w, h);

  // Users
  ctx.fillStyle = "#14213d";

  for (let i = 0; i < n; i++) {
    const x = p + ((xs[i] - minX) / sx) * w;
    const y = p + (1 - (ys[i] - minY) / sy) * h;

    ctx.beginPath();
    ctx.arc(x, y, 2.2, 0, Math.PI * 2);
    ctx.fill();
  }

  // Beam centers
  const bc = d.beam_centers || [];

  ctx.strokeStyle = "#fca311";
  ctx.lineWidth = 1.5;

  for (const b of bc) {
    if (!Array.isArray(b) || b.length < 2) continue;

    const x = p + ((b[0] - minX) / sx) * w;
    const y = p + (1 - (b[1] - minY) / sy) * h;

    ctx.beginPath();
    ctx.arc(x, y, 7, 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.fillStyle = "#68738a";
  ctx.font = "12px Arial";
  ctx.fillText("Users = dots | Beam centers = circles", p, 22);
}

// Redraw correctly when browser window changes size.
window.addEventListener("resize", () => {
  if (window.lastDashboardData) {
    updateDashboard(window.lastDashboardData);
  }
});
