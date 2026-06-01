/* ── DOM References ────────────────────────────────────────────── */
const imageInput = document.querySelector("#imageInput");
const uploadLabel = document.querySelector("#uploadLabel");
const preview = document.querySelector("#preview");
const previewPlaceholder = document.querySelector("#previewPlaceholder");
const previewContainer = document.querySelector("#previewContainer");
const speakBtn = document.querySelector("#speakBtn");
const finalText = document.querySelector("#finalText");
const finalConfidence = document.querySelector("#finalConfidence");
const agreementBadge = document.querySelector("#agreementBadge");
const resultCard = document.querySelector("#finalResult");

/* Webcam elements */
const cameraBtn = document.querySelector("#cameraBtn");
const webcamOverlay = document.querySelector("#webcamOverlay");
const webcamClose = document.querySelector("#webcamClose");
const webcamVideo = document.querySelector("#webcamVideo");
const webcamCanvas = document.querySelector("#webcamCanvas");
const captureBtn = document.querySelector("#captureBtn");

const PIPELINES = ["a", "b", "c"];
let currentStream = null;

/* ── Theme Toggle ─────────────────────────────────────────────── */
const themeToggle = document.querySelector("#themeToggle");

function applyTheme(theme) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

/* Load saved preference or default to light */
const savedTheme = localStorage.getItem("bv-theme") || "light";
applyTheme(savedTheme);

themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  localStorage.setItem("bv-theme", next);
});

/* ── Pipeline Column Rendering ────────────────────────────────── */
function setColumn(p, data) {
  const textEl = document.querySelector(`#text-${p}`);
  const fillEl = document.querySelector(`#conf-${p}`);
  const confLabel = document.querySelector(`#conf-label-${p}`);
  const latEl = document.querySelector(`#lat-${p}`);
  const col = document.querySelector(`#col-${p}`);

  col.classList.remove("pending");
  if (data.error) {
    textEl.textContent = "error";
    textEl.title = data.error;
    col.classList.add("errored");
  } else {
    textEl.textContent = data.text || "(no output)";
    textEl.title = "";
    col.classList.remove("errored");
  }

  const conf = Math.round((data.confidence || 0) * 100);
  fillEl.style.width = `${conf}%`;
  confLabel.textContent = `${conf}%`;
  latEl.textContent = `${data.latency_ms ?? 0}ms`;
}

function resetColumns() {
  PIPELINES.forEach((p) => {
    document.querySelector(`#text-${p}`).textContent = "Processing...";
    document.querySelector(`#conf-${p}`).style.width = "0%";
    document.querySelector(`#conf-label-${p}`).textContent = "";
    document.querySelector(`#lat-${p}`).textContent =
      p === "c" ? "thinking..." : "running...";
    const col = document.querySelector(`#col-${p}`);
    col.classList.add("pending");
    col.classList.remove("errored", "winner");
  });
  resultCard.classList.remove("has-result");
  finalText.textContent = "Running all three pipelines...";
  finalConfidence.textContent = "";
  agreementBadge.textContent = "";
  agreementBadge.className = "badge badge-none";
}

function applyFinal(data) {
  finalText.textContent = data.final_text || "(no consensus)";
  finalConfidence.textContent = `${Math.round((data.final_confidence || 0) * 100)}% confidence`;

  const label =
    `Agreement: ${data.agreement}` +
    (data.winner && data.winner !== "none"
      ? ` • Winner: Pipeline ${data.winner}`
      : "");
  agreementBadge.textContent = label;
  agreementBadge.className = `badge badge-${data.agreement}`;

  resultCard.classList.add("has-result");

  /* Highlight the winning pipeline card */
  if (data.winner && data.winner !== "none") {
    const winCol = document.querySelector(`#col-${data.winner.toLowerCase()}`);
    if (winCol) winCol.classList.add("winner");
  }
}

function handleEvent(event) {
  if (event.phase === "fast") {
    setColumn("a", event.pipeline_a);
    setColumn("b", event.pipeline_b);
  } else if (event.phase === "final") {
    setColumn("a", event.pipeline_a);
    setColumn("b", event.pipeline_b);
    setColumn("c", event.pipeline_c);
    applyFinal(event);
  } else if (event.phase === "error") {
    finalText.textContent = `Error: ${event.error}`;
  }
}

/* ── Upload Logic ─────────────────────────────────────────────── */
async function uploadEnsemble(file) {
  resetColumns();
  if (preview) {
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
    if (previewPlaceholder) previewPlaceholder.hidden = true;
  }

  const form = new FormData();
  form.append("image", file);

  let response;
  try {
    response = await fetch("/upload_ensemble", { method: "POST", body: form });
  } catch (err) {
    console.error("Fetch failed:", err);
    finalText.textContent = "Upload failed -- network error";
    return;
  }

  if (!response.ok) {
    console.error("Response not ok:", response.status, response.statusText);
    finalText.textContent = "Upload failed";
    return;
  }

  if (!response.body) {
    /* Fallback: read entire response as text (for proxied environments like HF) */
    const text = await response.text();
    const lines = text.split("\n").filter((l) => l.trim());
    for (const line of lines) {
      try {
        handleEvent(JSON.parse(line));
      } catch {
        /* ignore */
      }
    }
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newline;
    while ((newline = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (line) {
        try {
          handleEvent(JSON.parse(line));
        } catch {
          /* ignore partial / malformed lines */
        }
      }
    }
  }
}

/* ── Webcam Logic ─────────────────────────────────────────────── */
async function openCamera() {
  webcamOverlay.hidden = false;
  try {
    currentStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 960 } },
      audio: false,
    });
    webcamVideo.srcObject = currentStream;
  } catch (err) {
    console.error("Camera access denied:", err);
    alert("Camera access was denied. Please allow camera access and try again.");
    closeCamera();
  }
}

function closeCamera() {
  if (currentStream) {
    currentStream.getTracks().forEach((t) => t.stop());
    currentStream = null;
  }
  webcamVideo.srcObject = null;
  webcamOverlay.hidden = true;
}

function captureFrame() {
  const video = webcamVideo;
  const canvas = webcamCanvas;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0);
  canvas.toBlob(
    (blob) => {
      if (!blob) return;
      const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
      closeCamera();
      uploadEnsemble(file);
    },
    "image/jpeg",
    0.92
  );
}

/* ── Speak Aloud ──────────────────────────────────────────────── */
speakBtn.addEventListener("click", () => {
  const text = finalText.textContent.trim();
  if (
    !text ||
    text.startsWith("Upload") ||
    text.startsWith("Running") ||
    text.startsWith("Waiting")
  )
    return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.9;
  speakBtn.querySelector("span")
    ? (speakBtn.innerHTML =
        '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 5.5h2l4-3v11l-4-3H2a1 1 0 01-1-1v-3a1 1 0 011-1z" fill="currentColor"/><path d="M11 4.5a4 4 0 010 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M13 2.5a7 7 0 010 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> Speaking...')
    : null;
  utterance.onend = () => {
    speakBtn.innerHTML =
      '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 5.5h2l4-3v11l-4-3H2a1 1 0 01-1-1v-3a1 1 0 011-1z" fill="currentColor"/><path d="M11 4.5a4 4 0 010 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M13 2.5a7 7 0 010 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> Speak Aloud';
  };
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
});

/* ── Event Listeners ──────────────────────────────────────────── */
imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (file) uploadEnsemble(file);
});

uploadLabel.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadLabel.style.borderColor = "var(--accent)";
});

uploadLabel.addEventListener("dragleave", () => {
  uploadLabel.style.borderColor = "";
});

uploadLabel.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadLabel.style.borderColor = "";
  const file = event.dataTransfer.files[0];
  if (file) uploadEnsemble(file);
});

cameraBtn.addEventListener("click", openCamera);
webcamClose.addEventListener("click", closeCamera);
captureBtn.addEventListener("click", captureFrame);

/* Close webcam on Escape */
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !webcamOverlay.hidden) closeCamera();
});

/* Close webcam on overlay click */
webcamOverlay.addEventListener("click", (e) => {
  if (e.target === webcamOverlay) closeCamera();
});

/* ── Global Drag and Drop ─────────────────────────────────────── */
const globalDropzone = document.getElementById("globalDropzone");
let dragCounter = 0;

window.addEventListener("dragenter", (e) => {
  e.preventDefault();
  dragCounter++;
  if (dragCounter === 1) {
    globalDropzone.classList.add("active");
  }
});

window.addEventListener("dragleave", (e) => {
  e.preventDefault();
  dragCounter--;
  if (dragCounter === 0) {
    globalDropzone.classList.remove("active");
  }
});

window.addEventListener("dragover", (e) => {
  e.preventDefault();
});

window.addEventListener("drop", (e) => {
  e.preventDefault();
  dragCounter = 0;
  globalDropzone.classList.remove("active");
  
  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    const file = e.dataTransfer.files[0];
    if (file.type.startsWith("image/")) {
      uploadEnsemble(file);
    }
  }
});

