/**
 * app.js  –  QR Kod Okuyucu  Arayüz Mantığı
 * =============================================
 * - Kamerayı açar (getUserMedia), her 200ms'de bir frame yakalar
 * - Frame'i base64 olarak Flask /api/decode endpoint'ine gönderir
 * - Gelen QR sonuçlarını listeler, URL ise tıklanabilir yapar
 * - Canvas üzerine yeşil tespit kutuları çizer
 * - Geçmiş tablosunu /api/history'den çeker
 */

"use strict";

/* ── Elementler ───────────────────────────────────── */
const video         = document.getElementById("video");
const overlay       = document.getElementById("overlay");
const ctx           = overlay.getContext("2d");
const btnStart      = document.getElementById("btnStart");
const btnStop       = document.getElementById("btnStop");
const btnFlip       = document.getElementById("btnFlip");
const btnHistory    = document.getElementById("btnHistory");
const cameraSelect  = document.getElementById("cameraSelect");
const resultList    = document.getElementById("resultList");
const badge         = document.getElementById("badge");
const historyTable  = document.getElementById("historyTable");

/* ── Durum ────────────────────────────────────────── */
let stream        = null;
let loopId        = null;
let facingMode    = "environment";   // mobil arka kamera varsayılanı
let knownData     = new Set();       // bu oturumda görülenler (UI de-dup)

const INTERVAL_MS = 200;            // kaç ms'de bir frame gönderilir

/* ── Kamera cihazlarını doldur ───────────────────── */
async function populateCameras() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cams = devices.filter(d => d.kind === "videoinput");
    cameraSelect.innerHTML = "";
    cams.forEach((cam, i) => {
      const opt = document.createElement("option");
      opt.value = cam.deviceId;
      opt.textContent = cam.label || `Kamera ${i + 1}`;
      cameraSelect.appendChild(opt);
    });
  } catch (_) { /* izin verilmemiş, sessizce geç */ }
}

/* ── Kamerayı başlat ─────────────────────────────── */
async function startCamera() {
  const deviceId = cameraSelect.value;
  const constraints = {
    video: deviceId
      ? { deviceId: { exact: deviceId } }
      : { facingMode },
    audio: false,
  };

  try {
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = stream;
    await video.play();

    btnStart.disabled = true;
    btnStop.disabled  = false;

    await populateCameras();
    loopId = setInterval(captureAndDecode, INTERVAL_MS);
  } catch (err) {
    alert("Kamera açılamadı: " + err.message);
  }
}

/* ── Kamerayı durdur ─────────────────────────────── */
function stopCamera() {
  clearInterval(loopId);
  loopId = null;
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  video.srcObject = null;
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  btnStart.disabled = false;
  btnStop.disabled  = true;
}

/* ── Kamera değiştir (mobil) ─────────────────────── */
async function flipCamera() {
  facingMode = facingMode === "environment" ? "user" : "environment";
  stopCamera();
  await startCamera();
}

/* ── Frame yakala ve API'ye gönder ──────────────────── */
const tmpCanvas = document.createElement("canvas");
const tmpCtx    = tmpCanvas.getContext("2d");

async function captureAndDecode() {
  if (!video.videoWidth) return;

  tmpCanvas.width  = video.videoWidth;
  tmpCanvas.height = video.videoHeight;
  tmpCtx.drawImage(video, 0, 0);

  // Kalite 0.8 – bant genişliği / hız dengesi
  const b64 = tmpCanvas.toDataURL("image/jpeg", 0.8);

  let data;
  try {
    const res = await fetch("/api/decode", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ image: b64 }),
    });
    data = await res.json();
  } catch (_) { return; }

  renderOverlay(data.results || []);
  renderResults(data.results || []);
}

/* ── Canvas üzerine kutu çiz ─────────────────────── */
function renderOverlay(results) {
  overlay.width  = video.videoWidth;
  overlay.height = video.videoHeight;
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  results.forEach(r => {
    // Sadece tip ve kısa veri yaz (koordinat backend'den gelmiyor,
    // merkez konuma metin yaz)
    ctx.strokeStyle = "#22c55e";
    ctx.lineWidth   = 3;
    ctx.font        = "bold 14px monospace";
    ctx.fillStyle   = "#22c55e";

    // Backend polygon koordinatı yok (base64 gönderiminde), sadece metin
    const label = `[${r.type}] ${r.data.substring(0, 40)}${r.data.length > 40 ? "…" : ""}`;
    ctx.fillText(label, 12, 28 + results.indexOf(r) * 26);
  });
}

/* ── Sonuç listesini güncelle ────────────────────── */
function renderResults(results) {
  const newItems = results.filter(r => !knownData.has(r.data));
  if (!newItems.length) return;

  // "Taratın…" ipucunu kaldır
  const hint = resultList.querySelector(".empty-hint");
  if (hint) hint.remove();

  newItems.forEach(r => {
    knownData.add(r.data);
    const li  = document.createElement("li");
    li.className = "result-item";

    const isURL = /^https?:\/\//i.test(r.data);
    const dataEl = document.createElement("div");
    dataEl.className = "data";
    dataEl.innerHTML = isURL
      ? `<a href="${escapeHtml(r.data)}" target="_blank" rel="noopener noreferrer">${escapeHtml(r.data)}</a>`
      : escapeHtml(r.data);

    const metaEl = document.createElement("div");
    metaEl.className = "meta";
    metaEl.textContent = `${r.type}  ·  ${r.timestamp}`;

    li.appendChild(dataEl);
    li.appendChild(metaEl);
    resultList.prepend(li);
  });

  badge.textContent = knownData.size;
}

/* ── Geçmiş tablosunu çek ────────────────────────── */
async function loadHistory() {
  try {
    const res  = await fetch("/api/history");
    const data = await res.json();
    renderHistory(data.history || []);
  } catch (_) {
    historyTable.innerHTML = "<p class='empty-hint'>Sunucuya ulaşılamadı.</p>";
  }
}

function renderHistory(rows) {
  if (!rows.length) {
    historyTable.innerHTML = "<p class='empty-hint'>Henüz kayıt yok.</p>";
    return;
  }
  historyTable.innerHTML = `
    <table>
      <thead><tr>
        <th>Zaman</th><th>Tür</th><th>İçerik</th>
      </tr></thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td>${escapeHtml(r.timestamp)}</td>
            <td>${escapeHtml(r.type)}</td>
            <td>${escapeHtml(r.data)}</td>
          </tr>`).join("")}
      </tbody>
    </table>`;
}

/* ── XSS önlemi ──────────────────────────────────── */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ── Event listener'lar ──────────────────────────── */
btnStart.addEventListener("click", startCamera);
btnStop.addEventListener("click", stopCamera);
btnFlip.addEventListener("click", flipCamera);
btnHistory.addEventListener("click", loadHistory);

/* ── Sayfa açılışında ────────────────────────────── */
(async () => {
  await populateCameras();
  loadHistory();
})();
