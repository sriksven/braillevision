const imageInput = document.querySelector("#imageInput");
const upload = document.querySelector(".upload");
const preview = document.querySelector("#preview");
const speakBtn = document.querySelector("#speakBtn");
const finalText = document.querySelector("#finalText");
const finalConfidence = document.querySelector("#finalConfidence");
const agreementBadge = document.querySelector("#agreementBadge");

const PIPELINES = ["a", "b", "c", "d"];

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
    document.querySelector(`#conf-label-${p}`).textContent = "-";
    document.querySelector(`#lat-${p}`).textContent =
      p === "c" ? "thinking..." : "running...";
    const col = document.querySelector(`#col-${p}`);
    col.classList.add("pending");
    col.classList.remove("errored");
  });
  finalText.textContent = "Waiting for pipelines...";
  finalConfidence.textContent = "-";
  agreementBadge.textContent = "-";
  agreementBadge.className = "agreement-badge agreement-none";
}

function applyFinal(data) {
  finalText.textContent = data.final_text || "(no consensus)";
  finalConfidence.textContent = `${Math.round((data.final_confidence || 0) * 100)}% confidence`;
  agreementBadge.textContent =
    `Agreement: ${data.agreement} - Winner: ${data.winner === "none" ? "-" : "Pipeline " + data.winner}`;
  agreementBadge.className = `agreement-badge agreement-${data.agreement}`;
}

function handleEvent(event) {
  if (event.phase === "fast") {
    setColumn("a", event.pipeline_a);
    setColumn("b", event.pipeline_b);
    setColumn("d", event.pipeline_d);
  } else if (event.phase === "final") {
    setColumn("a", event.pipeline_a);
    setColumn("b", event.pipeline_b);
    setColumn("c", event.pipeline_c);
    setColumn("d", event.pipeline_d);
    applyFinal(event);
  } else if (event.phase === "error") {
    finalText.textContent = `Error: ${event.error}`;
  }
}

async function uploadEnsemble(file) {
  resetColumns();
  if (preview) {
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
  }

  const form = new FormData();
  form.append("image", file);

  let response;
  try {
    response = await fetch("/upload_ensemble", { method: "POST", body: form });
  } catch (err) {
    console.error("Fetch failed:", err);
    finalText.textContent = "Upload failed - network error";
    return;
  }

  if (!response.ok) {
    console.error("Response not ok:", response.status, response.statusText);
    finalText.textContent = "Upload failed";
    return;
  }

  if (!response.body) {
    // Fallback: read entire response as text (for proxied environments)
    const text = await response.text();
    const lines = text.split("\n").filter((l) => l.trim());
    for (const line of lines) {
      try {
        handleEvent(JSON.parse(line));
      } catch {
        // ignore
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
          // ignore partial / malformed lines
        }
      }
    }
  }
}

speakBtn.addEventListener("click", () => {
  const text = finalText.textContent.trim();
  if (!text || text === "Upload an image to begin" || text === "Waiting for pipelines...") return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.9;
  speakBtn.textContent = "Speaking...";
  utterance.onend = () => {
    speakBtn.textContent = "Speak Aloud";
  };
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
});

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (file) uploadEnsemble(file);
});

upload.addEventListener("dragover", (event) => {
  event.preventDefault();
});

upload.addEventListener("drop", (event) => {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (file) uploadEnsemble(file);
});
