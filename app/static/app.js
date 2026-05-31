const detectedText = document.querySelector("#detectedText");
const dotCount = document.querySelector("#dotCount");
const cellCount = document.querySelector("#cellCount");
const spacing = document.querySelector("#spacing");
const confidence = document.querySelector("#confidence");
const speakBtn = document.querySelector("#speakBtn");
const copyBtn = document.querySelector("#copyBtn");
const imageInput = document.querySelector("#imageInput");
const upload = document.querySelector(".upload");
const feed = document.querySelector("#feed");
const historyEl = document.querySelector("#history");

let lastText = "";
const history = [];

function addHistory(text) {
  if (!text || history.some((item) => item.text === text)) return;
  history.unshift({ text, time: new Date().toLocaleTimeString() });
  history.splice(10);
  historyEl.innerHTML = history.map((item) => `<li><strong>${item.text}</strong><br><small>${item.time}</small></li>`).join("");
}

function updateResult(data) {
  const text = data.text || "";
  detectedText.textContent = text || "No Braille detected";
  dotCount.textContent = data.dot_count ?? 0;
  cellCount.textContent = data.cell_count ?? 0;
  spacing.textContent = data.spacing ?? 0;
  confidence.textContent = `${Math.round((data.confidence || 0) * 100)}%`;
  if (text && text !== lastText) {
    lastText = text;
    addHistory(text);
  }
}

async function pollResult() {
  try {
    const response = await fetch("/result");
    updateResult(await response.json());
  } catch {
    // Keep the last visible result when a transient request fails.
  }
}

speakBtn.addEventListener("click", () => {
  const text = detectedText.textContent.trim();
  if (!text || text === "No Braille detected") return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.9;
  speakBtn.textContent = "Speaking...";
  utterance.onend = () => {
    speakBtn.textContent = "Speak";
  };
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
});

copyBtn.addEventListener("click", async () => {
  await navigator.clipboard.writeText(detectedText.textContent.trim());
  copyBtn.textContent = "Copied";
  setTimeout(() => {
    copyBtn.textContent = "Copy";
  }, 900);
});

async function uploadImage(file) {
  const form = new FormData();
  form.append("image", file);
  const response = await fetch("/upload", { method: "POST", body: form });
  const data = await response.json();
  if (data.annotated_image_b64) {
    feed.src = data.annotated_image_b64;
  }
  updateResult(data);
}

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (file) uploadImage(file);
});

upload.addEventListener("dragover", (event) => {
  event.preventDefault();
});

upload.addEventListener("drop", (event) => {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (file) uploadImage(file);
});

setInterval(pollResult, 500);
pollResult();

