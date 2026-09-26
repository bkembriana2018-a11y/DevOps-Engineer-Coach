const $ = (sel) => document.querySelector(sel);

const uploadForm = $("#uploadForm");
const fileInput = $("#fileInput");
const titleInput = $("#titleInput");
const uploadBtn = $("#uploadBtn");
const uploadMsg = $("#uploadMsg");
const lectureList = $("#lectureList");
const emptyState = $("#emptyState");
const llmStatus = $("#llmStatus");
const guideSection = $("#guideSection");
const guideTitle = $("#guideTitle");
const guideMeta = $("#guideMeta");
const guideOut = $("#guideOut");
const downloadGuideBtn = $("#downloadGuideBtn");
const closeGuideBtn = $("#closeGuideBtn");

let currentGuideLectureId = null;

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

// ---------- tiny markdown renderer ----------
// Handles the subset the study-guide prompt asks the model for: #/##/### headers,
// **bold**, -/* bullets, 1. numbered lists, and plain paragraphs.
function renderMarkdown(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let listType = null; // "ul" | "ol" | null

  const closeList = () => {
    if (listType) {
      html += listType === "ul" ? "</ul>" : "</ol>";
      listType = null;
    }
  };

  const inline = (text) =>
    text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, "<code>$1</code>");

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      closeList();
      continue;
    }
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      closeList();
      const level = h[1].length;
      html += `<h${level}>${inline(h[2])}</h${level}>`;
      continue;
    }
    const bullet = line.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      if (listType !== "ul") {
        closeList();
        html += "<ul>";
        listType = "ul";
      }
      html += `<li>${inline(bullet[1])}</li>`;
      continue;
    }
    const numbered = line.match(/^\d+[.)]\s+(.*)$/);
    if (numbered) {
      if (listType !== "ol") {
        closeList();
        html += "<ol>";
        listType = "ol";
      }
      html += `<li>${inline(numbered[1])}</li>`;
      continue;
    }
    closeList();
    html += `<p>${inline(line)}</p>`;
  }
  closeList();
  return html;
}

function fmtDate(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function statusBadge(lecture) {
  if (!lecture.study_guide_ready) return `<span class="badge none">No guide yet</span>`;
  if (lecture.generated_by === "ollama") return `<span class="badge ready">Generated (${lecture.model || "AI"})</span>`;
  return `<span class="badge fallback">Offline outline</span>`;
}

async function refreshHealth() {
  try {
    const health = await api("/api/health");
    if (health.ollama.ok) {
      llmStatus.textContent = "Ollama connected";
      llmStatus.className = "status-ok";
    } else {
      llmStatus.textContent = "Ollama offline — study guides will be raw outlines";
      llmStatus.className = "status-bad";
    }
  } catch {
    llmStatus.textContent = "Can't reach server";
    llmStatus.className = "status-bad";
  }
}

async function refreshLectures() {
  const { lectures } = await api("/api/lectures");
  emptyState.hidden = lectures.length > 0;
  lectureList.innerHTML = "";
  for (const lec of lectures) {
    const card = document.createElement("div");
    card.className = "lec-card";
    card.innerHTML = `
      <div>
        <h4>${escapeHtml(lec.title)} ${statusBadge(lec)}</h4>
        <div class="meta">${lec.slide_count} slides · uploaded ${fmtDate(lec.uploaded_at)}</div>
      </div>
      <div class="actions">
        <button class="ghost small" data-action="generate" data-id="${lec.id}">
          ${lec.study_guide_ready ? "Regenerate" : "Generate study guide"}
        </button>
        ${lec.study_guide_ready ? `<button class="ghost small" data-action="view" data-id="${lec.id}">View</button>` : ""}
        <button class="ghost small" data-action="delete" data-id="${lec.id}">Delete</button>
      </div>
    `;
    lectureList.appendChild(card);
  }
}

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

lectureList.addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const id = btn.dataset.id;
  const action = btn.dataset.action;

  if (action === "delete") {
    if (!confirm("Delete this lecture and its study guide?")) return;
    await api(`/api/lectures/${id}`, { method: "DELETE" });
    if (currentGuideLectureId === id) guideSection.hidden = true;
    await refreshLectures();
    return;
  }

  if (action === "generate") {
    btn.disabled = true;
    const original = btn.textContent;
    btn.textContent = "Generating…";
    try {
      const result = await api(`/api/lectures/${id}/study-guide`, { method: "POST" });
      await refreshLectures();
      showGuide(id, result.title, result.content, result);
    } catch (err) {
      alert(`Couldn't generate a study guide: ${err.message}`);
    } finally {
      btn.disabled = false;
      btn.textContent = original;
    }
    return;
  }

  if (action === "view") {
    const lecture = await api(`/api/lectures/${id}`);
    const guide = await api(`/api/lectures/${id}/study-guide`);
    showGuide(id, lecture.title, guide.content, lecture);
  }
});

function showGuide(id, title, content, meta) {
  currentGuideLectureId = id;
  guideTitle.textContent = title;
  guideOut.innerHTML = renderMarkdown(content);
  const via = meta.generated_by === "ollama" ? `via Ollama (${meta.model})` : "offline outline — Ollama wasn't available";
  guideMeta.textContent = meta.generated_at ? `Generated ${fmtDate(meta.generated_at)} ${via}` : "";
  guideSection.hidden = false;
  guideSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

closeGuideBtn.addEventListener("click", () => {
  guideSection.hidden = true;
  currentGuideLectureId = null;
});

downloadGuideBtn.addEventListener("click", () => {
  if (!currentGuideLectureId) return;
  window.location.href = `/api/lectures/${currentGuideLectureId}/study-guide/download`;
});

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  if (titleInput.value.trim()) form.append("title", titleInput.value.trim());

  uploadBtn.disabled = true;
  uploadMsg.textContent = "Uploading and reading slides…";
  try {
    await api("/api/lectures", { method: "POST", body: form });
    uploadMsg.textContent = "Uploaded. Click “Generate study guide” below.";
    uploadForm.reset();
    await refreshLectures();
  } catch (err) {
    uploadMsg.textContent = `Upload failed: ${err.message}`;
  } finally {
    uploadBtn.disabled = false;
  }
});

refreshHealth();
refreshLectures();
setInterval(refreshHealth, 15000);
