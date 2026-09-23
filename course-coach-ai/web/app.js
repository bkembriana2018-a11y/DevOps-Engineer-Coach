const $ = (s) => document.querySelector(s);

const state = {
  courseId: localStorage.getItem("courseCoach.courseId") || null,
  course: null,
  quiz: null,
  startedAt: null,
  chat: [],
  flash: { cards: [], idx: 0, topic: "" },
};

async function api(path, opts) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail || msg; } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

document.querySelectorAll(".tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((b) => b.classList.remove("on"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("on"));
    btn.classList.add("on");
    $("#tab-" + btn.dataset.tab).classList.add("on");
  });
});

const BAND_LABELS = { ready: "Ready!", borderline: "Almost there", weak: "Keep practicing", untested: "Not started yet" };
function bandEl(band) {
  return `<span class="band ${band}">${BAND_LABELS[band] || band}</span>`;
}

function mdInline(s) {
  s = s.replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`);
  s = s.replace(/\*\*([^*]+)\*\*/g, (_, b) => `<strong>${b}</strong>`);
  s = s.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, (_, pre, i) => `${pre}<em>${i}</em>`);
  return s;
}
function renderMarkdown(src) {
  const lines = escapeHtml(src).split("\n");
  let html = "", para = [];
  const flush = () => { if (para.length) { html += `<p>${mdInline(para.join(" "))}</p>`; para = []; } };
  for (const line of lines) {
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    const ul = line.match(/^\s*[-*]\s+(.*)$/);
    if (!line.trim()) { flush(); continue; }
    if (h) { flush(); html += `<h${h[1].length}>${mdInline(h[2])}</h${h[1].length}>`; continue; }
    if (ul) { flush(); html += `<ul><li>${mdInline(ul[1])}</li></ul>`; continue; }
    para.push(line.trim());
  }
  flush();
  return html;
}
function escapeHtml(s) { return s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

const WaitGame = (() => {
  let container = null, intervalId = null, score = 0;
  const colors = ["var(--accent)", "var(--gold)", "var(--go)", "var(--warn)"];
  function spawnBubble(field) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "wait-bubble"; b.setAttribute("aria-label", "Pop");
    const size = 34 + Math.random() * 30;
    b.style.width = `${size}px`; b.style.height = `${size}px`;
    b.style.left = `${Math.random() * 82}%`;
    b.style.background = colors[Math.floor(Math.random() * colors.length)];
    b.style.animationDuration = `${2.4 + Math.random() * 1.4}s`;
    const pop = () => { score += 1; updateScore(); b.remove(); };
    b.addEventListener("click", pop);
    b.addEventListener("animationend", () => b.remove());
    field.appendChild(b);
  }
  function updateScore() { const el = container?.querySelector(".wait-game-score"); if (el) el.textContent = `Popped: ${score}`; }
  function setStatus(text) { const el = container?.querySelector(".wait-game-time"); if (el) el.textContent = text; }
  function mount(target, label) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return false;
    score = 0; target.innerHTML = "";
    container = document.createElement("div");
    container.className = "wait-game";
    container.innerHTML = `<div class="wait-game-head"><span class="wait-game-label">${label || "While you wait…"}</span><span class="wait-game-meta"><span class="wait-game-time"></span> · <span class="wait-game-score">Popped: 0</span></span></div><div class="wait-game-field"></div>`;
    target.appendChild(container);
    const field = container.querySelector(".wait-game-field");
    spawnBubble(field);
    intervalId = setInterval(() => spawnBubble(field), 550);
    return true;
  }
  function unmount() { if (intervalId) clearInterval(intervalId); intervalId = null; container = null; }
  return { mount, unmount, setStatus };
})();

function tickingLabel(base, onTick) {
  const started = Date.now();
  onTick(`${base} (0s)`);
  const id = setInterval(() => {
    const s = Math.round((Date.now() - started) / 1000);
    onTick(`${base} (${s}s)${s > 20 ? " — local CPU inference, can take a couple minutes" : ""}`);
  }, 1000);
  return () => clearInterval(id);
}

async function refreshHealth() {
  const el = $("#llmStatus");
  try {
    const h = await api("/api/health");
    el.classList.remove("status-ok", "status-warn", "status-bad");
    if (h.ollama?.ok) {
      el.textContent = "Ollama: " + ((h.ollama.models || []).join(", ") || "model ready");
      el.classList.add("status-ok");
    } else {
      el.textContent = "Ollama offline — post lectures, but AI generation is paused";
      el.classList.add("status-warn");
    }
  } catch {
    el.textContent = "API down"; el.classList.add("status-bad");
  }
}

// ---------- courses ----------

async function loadCourses() {
  const { courses } = await api("/api/courses");
  const sel = $("#courseSelect");
  sel.innerHTML = courses.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
  if (!courses.length) {
    $("#emptyState").hidden = false;
    state.courseId = null;
    return;
  }
  $("#emptyState").hidden = true;
  if (!state.courseId || !courses.find((c) => c.id === state.courseId)) {
    state.courseId = courses[0].id;
  }
  sel.value = state.courseId;
  await loadCourseData();
}

$("#courseSelect").addEventListener("change", async (e) => {
  state.courseId = e.target.value;
  localStorage.setItem("courseCoach.courseId", state.courseId);
  await loadCourseData();
});

$("#newCourseBtn").addEventListener("click", () => { $("#newCourseForm").hidden = false; $("#newCourseName").focus(); });
$("#cancelCourseBtn").addEventListener("click", () => { $("#newCourseForm").hidden = true; });
$("#saveCourseBtn").addEventListener("click", async () => {
  const name = $("#newCourseName").value.trim();
  if (!name) return;
  const code = $("#newCourseCode").value.trim();
  const course = await api("/api/courses", { method: "POST", body: JSON.stringify({ name, code }) });
  $("#newCourseForm").hidden = true;
  $("#newCourseName").value = ""; $("#newCourseCode").value = "";
  state.courseId = course.id;
  localStorage.setItem("courseCoach.courseId", course.id);
  await loadCourses();
});

async function loadCourseData() {
  if (!state.courseId) return;
  state.course = await api("/api/courses/" + state.courseId);
  fillTopicSelects();
  await refreshReadiness();
  await loadLectures();
  await loadFlashcards();
  try { await loadStudyPack(); } catch {}
}

function fillTopicSelects() {
  const topics = state.course.topics || [];
  const opts = topics.map((t) => `<option value="${t.id}">${escapeHtml(t.label)}</option>`).join("");
  $("#lecTopic").innerHTML = `<option value="">No specific topic</option>` + opts;
  $("#lecFilterTopic").innerHTML = `<option value="">All topics</option>` + opts;
  $("#studyTopic").innerHTML = opts || `<option value="">Add a topic first</option>`;
  $("#cardTopic").innerHTML = `<option value="">All topics</option>` + opts;
  $("#quizTopic").innerHTML = `<option value="">Mixed (all topics)</option>` + opts;
  $("#coachSub").innerHTML = `<option value="">General</option>` + opts;
}

$("#addTopicBtn").addEventListener("click", async () => {
  const label = $("#newTopicLabel").value.trim();
  if (!label) return;
  await api(`/api/courses/${state.courseId}/topics`, { method: "POST", body: JSON.stringify({ label }) });
  $("#newTopicLabel").value = "";
  await loadCourseData();
});

$("#addExamBtn").addEventListener("click", async () => {
  const label = $("#newExamLabel").value.trim();
  const date = $("#newExamDate").value;
  if (!label || !date) return;
  await api(`/api/courses/${state.courseId}/exams`, { method: "POST", body: JSON.stringify({ label, date, topic_ids: [] }) });
  $("#newExamLabel").value = ""; $("#newExamDate").value = "";
  await refreshReadiness();
});

async function refreshReadiness() {
  const r = await api(`/api/courses/${state.courseId}/readiness`);
  $("#disclaimer").textContent = r.disclaimer;

  const banner = $("#examBanner");
  if (r.next_exam) {
    const days = r.next_exam.days_away;
    const urgency = days <= 7 ? " soon" : "";
    banner.className = "exam-banner" + (days <= 7 ? " soon" : "");
    banner.hidden = false;
    banner.innerHTML = `<strong>${escapeHtml(r.next_exam.label)}</strong> is in <strong>${days}</strong> day${days === 1 ? "" : "s"} (${r.next_exam.date}).`;
  } else {
    banner.hidden = true;
  }

  const overallPct = r.overall_percent == null ? "—" : r.overall_percent + "% practice";
  $("#overallCard").innerHTML = `<div class="card"><h3>${escapeHtml(r.course_name)} — overall</h3>${bandEl(r.overall_band)}<div>${overallPct}</div><div class="muted">${Object.keys(r.topics).length} topic(s) tracked</div></div>`;

  $("#actions").innerHTML = (r.next_actions || []).map((a) => `<li>${escapeHtml(a)}</li>`).join("");

  const rows = Object.values(r.topics)
    .map((t) => {
      const pct = t.percent == null ? "—" : t.percent + "%";
      return `<tr><td>${escapeHtml(t.label)}</td><td>${t.lecture_count}</td><td>${t.attempts}</td><td>${pct}</td><td>${bandEl(t.band)}</td><td>${(t.top_miss_topics || []).join(", ")}</td></tr>`;
    })
    .join("");
  $("#topicsTable").innerHTML = rows
    ? `<table><thead><tr><th>Topic</th><th>Lectures</th><th>Attempts</th><th>Acc</th><th>Band</th><th>Miss tags</th></tr></thead><tbody>${rows}</tbody></table>`
    : `<p class="muted">Add a topic above to start tracking.</p>`;
}

// ---------- lectures ----------

$("#saveLectureBtn").addEventListener("click", async () => {
  const title = $("#lecTitle").value.trim();
  const content = $("#lecContent").value.trim();
  if (!title || !content) { $("#lecSaveMsg").textContent = "Title and content are both required."; return; }
  const topic_id = $("#lecTopic").value || null;
  const week = $("#lecWeek").value ? Number($("#lecWeek").value) : null;
  $("#lecSaveMsg").textContent = "Saving…";
  const lecture = await api(`/api/courses/${state.courseId}/lectures`, { method: "POST", body: JSON.stringify({ title, topic_id, week, content }) });
  $("#lecSaveMsg").textContent = "Saved.";
  $("#lecTitle").value = ""; $("#lecContent").value = ""; $("#lecWeek").value = "";

  const genFlash = $("#genFlashOnSave").checked;
  const genQuiz = $("#genQuizOnSave").checked;
  if (genFlash || genQuiz) {
    const genBox = $("#genResult");
    const gameOn = WaitGame.mount(genBox, "Generating from your lecture ✨");
    const stop = tickingLabel("Working…", (l) => { if (gameOn) WaitGame.setStatus(l); else genBox.textContent = l; });
    try {
      const res = await api(`/api/courses/${state.courseId}/lectures/${lecture.id}/generate`, {
        method: "POST",
        body: JSON.stringify({ n_questions: genQuiz ? 5 : 0, n_flashcards: genFlash ? 8 : 0 }),
      });
      genBox.textContent = `Added ${res.flashcards_added} flashcard(s).` + (genQuiz ? ` Previewed ${res.questions_previewed} question(s) — head to Practice to actually take a quiz on this topic.` : "");
    } catch (err) {
      genBox.textContent = "Generation failed: " + err.message;
    } finally {
      stop(); WaitGame.unmount();
    }
  }
  await loadCourseData();
});

$("#lecFilterTopic").addEventListener("change", () => loadLectures());

async function loadLectures() {
  const topicId = $("#lecFilterTopic").value;
  const { lectures } = await api(`/api/courses/${state.courseId}/lectures` + (topicId ? `?topic_id=${topicId}` : ""));
  const topicLabel = (id) => (state.course.topics.find((t) => t.id === id) || {}).label || "No topic";
  $("#lectureList").innerHTML = lectures.length
    ? lectures
        .slice()
        .reverse()
        .map(
          (l) => `<div class="lecture-item"><h4>${escapeHtml(l.title)}</h4><div class="muted">${escapeHtml(topicLabel(l.topic_id))}${l.week ? " · week " + l.week : ""}</div><details><summary>View content</summary><pre>${escapeHtml(l.content)}</pre></details></div>`
        )
        .join("")
    : `<p class="muted">No lectures posted yet.</p>`;
}

// ---------- learn ----------

$("#studyTopic").addEventListener("change", loadStudyPack);

async function loadStudyPack() {
  const topicId = $("#studyTopic").value;
  const out = $("#studyOut");
  if (!topicId) { out.textContent = "Add a topic first, then post a lecture for it."; return; }
  out.textContent = "Loading…";
  const { content } = await api(`/api/courses/${state.courseId}/context?topic_id=${topicId}`);
  out.textContent = content || "No lectures posted for this topic yet.";
}

$("#studyAsk").addEventListener("click", async () => {
  const topicId = $("#studyTopic").value;
  const out = $("#studyOut");
  if (!topicId) return;
  const gameOn = WaitGame.mount(out, "Pop a few bubbles while I put this together ✨");
  const stop = tickingLabel("Coaching…", (l) => { if (gameOn) WaitGame.setStatus(l); else out.textContent = l; });
  const messages = [{ role: "user", content: "Teach this topic as a compact study brief grounded in the lecture material: key points, one worked example if applicable, and 3 check questions with answers at the bottom." }];
  try {
    const res = await api(`/api/courses/${state.courseId}/chat`, { method: "POST", body: JSON.stringify({ messages, topic_id: topicId }) });
    const prefix = res.provider === "fallback" ? "[offline excerpt]\n\n" : "";
    out.innerHTML = renderMarkdown(prefix + res.content);
  } catch (err) {
    out.textContent = "Request failed: " + err.message;
  } finally {
    stop(); WaitGame.unmount();
  }
});

// ---------- flashcards ----------

$("#cardTopic").addEventListener("change", () => loadFlashcards());
$("#shuffleCards").addEventListener("click", () => renderFlashcard(true));

async function loadFlashcards() {
  const topicId = $("#cardTopic").value;
  const { cards } = await api(`/api/courses/${state.courseId}/flashcards` + (topicId ? `?topic_id=${topicId}` : ""));
  state.flash.cards = cards;
  state.flash.idx = 0;
  renderFlashcard();
}

function shuffleArray(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}

function renderFlashcard(shuffle) {
  if (shuffle) state.flash.cards = shuffleArray(state.flash.cards);
  const cards = state.flash.cards;
  const card = $("#flashcard");
  card.classList.remove("flipped");
  if (!cards.length) {
    $("#cardMeta").textContent = "No cards yet — add one manually or generate from a topic's lectures.";
    $("#cardFront").textContent = ""; $("#cardBack").textContent = "";
    return;
  }
  const c = cards[state.flash.idx];
  $("#cardMeta").textContent = `Card ${state.flash.idx + 1} of ${cards.length}`;
  $("#cardFront").textContent = c.front;
  $("#cardBack").textContent = c.back;
}
function flipCard() { $("#flashcard").classList.toggle("flipped"); }
function nextCard() { if (!state.flash.cards.length) return; state.flash.idx = (state.flash.idx + 1) % state.flash.cards.length; renderFlashcard(); }
function prevCard() { if (!state.flash.cards.length) return; state.flash.idx = (state.flash.idx - 1 + state.flash.cards.length) % state.flash.cards.length; renderFlashcard(); }
$("#cardFlip").addEventListener("click", flipCard);
$("#cardNext").addEventListener("click", nextCard);
$("#cardPrev").addEventListener("click", prevCard);
$("#flashcard").addEventListener("click", flipCard);
$("#cardDelete").addEventListener("click", async () => {
  const c = state.flash.cards[state.flash.idx];
  if (!c) return;
  await api(`/api/courses/${state.courseId}/flashcards/${c.id}`, { method: "DELETE" });
  await loadFlashcards();
});
$("#addCardBtn").addEventListener("click", async () => {
  const front = $("#manualFront").value.trim();
  const back = $("#manualBack").value.trim();
  if (!front || !back) return;
  const topic_id = $("#cardTopic").value || null;
  await api(`/api/courses/${state.courseId}/flashcards`, { method: "POST", body: JSON.stringify({ topic_id, front, back }) });
  $("#manualFront").value = ""; $("#manualBack").value = "";
  await loadFlashcards();
});
$("#genCardsBtn").addEventListener("click", async () => {
  const topicId = $("#cardTopic").value;
  if (!topicId) { alert("Pick a specific topic first (not ‘All topics’) to generate cards for it."); return; }
  const box = $("#flashcard");
  const gameOn = WaitGame.mount(box, "Generating flashcards ✨");
  const stop = tickingLabel("Working…", (l) => { if (gameOn) WaitGame.setStatus(l); });
  try {
    await api(`/api/courses/${state.courseId}/flashcards/generate`, { method: "POST", body: JSON.stringify({ topic_id: topicId, n: 8 }) });
  } catch (err) {
    alert("Generation failed: " + err.message);
  } finally {
    stop(); WaitGame.unmount();
    await loadFlashcards();
  }
});

// ---------- quiz ----------

$("#startQuiz").addEventListener("click", startQuiz);

async function startQuiz() {
  const topic_id = $("#quizTopic").value || null;
  const body = { topic_id, n: Number($("#quizN").value), difficulty: $("#quizDiff").value };
  const quizBox = $("#quizBox");
  const gameOn = WaitGame.mount(quizBox, "Generating your quiz ✨");
  const stop = tickingLabel("Building quiz…", (l) => { if (gameOn) WaitGame.setStatus(l); else quizBox.textContent = l; });
  let quiz;
  try {
    quiz = await api(`/api/courses/${state.courseId}/quiz`, { method: "POST", body: JSON.stringify(body) });
  } finally {
    stop(); WaitGame.unmount();
  }
  state.quiz = quiz;
  state.startedAt = Date.now();
  const noteLine = quiz.note ? `<div class="quiz-note">${escapeHtml(quiz.note)}</div>` : "";
  $("#quizMeta").innerHTML = `${quiz.items.length} item(s) on ${escapeHtml(quiz.topic_label)}` + noteLine;
  if (!quiz.items.length) { $("#quizBox").innerHTML = ""; return; }
  $("#quizBox").innerHTML =
    quiz.items
      .map((item, idx) => {
        const choices = (item.choices || []).map((c) => `<label class="choice"><input type="radio" name="q${idx}" value="${c.trim()[0]}" /> ${escapeHtml(c)}</label>`).join("");
        return `<div class="q" data-id="${item.id}" data-idx="${idx}"><div class="stem">${idx + 1}. ${escapeHtml(item.stem)}</div>${choices}</div>`;
      })
      .join("") + `<button id="submitQuiz">See my score</button>`;
  $("#submitQuiz").addEventListener("click", submitQuiz);
}

async function submitQuiz() {
  if (!state.quiz) return;
  const responses = state.quiz.items.map((item, idx) => {
    const picked = document.querySelector(`input[name="q${idx}"]:checked`);
    return { id: item.id, selected: picked ? picked.value : "" };
  });
  const elapsed = (Date.now() - state.startedAt) / 1000;
  const out = await api(`/api/courses/${state.courseId}/grade`, { method: "POST", body: JSON.stringify({ quiz_id: state.quiz.quiz_id, elapsed_sec: elapsed, responses }) });
  const g = out.graded;
  $("#quizMeta").innerHTML = `Score ${g.correct}/${g.total} (${g.percent}%). ${elapsed.toFixed(0)}s elapsed.`;
  document.querySelectorAll(".q").forEach((box) => {
    const row = g.results.find((r) => r.id === box.dataset.id);
    if (!row) return;
    box.querySelectorAll(".choice").forEach((lab) => {
      const val = lab.querySelector("input").value;
      if (val === row.answer) lab.classList.add("right");
      if (val === row.selected && !row.correct) lab.classList.add("wrong");
    });
    const note = document.createElement("div");
    note.className = "muted";
    note.textContent = (row.correct ? "Correct. " : `Answer ${row.answer}. `) + row.explanation;
    box.appendChild(note);
  });
  $("#submitQuiz")?.remove();
  await refreshReadiness();
}

// ---------- coach ----------

$("#chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = $("#chatInput").value.trim();
  if (!text) return;
  $("#chatInput").value = "";
  const outgoing = state.chat.slice();
  outgoing.push({ role: "user", content: text });
  state.chat.push({ role: "user", content: text });
  renderChat();

  const waitEl = $("#chatWait");
  waitEl.hidden = false;
  const gameOn = WaitGame.mount(waitEl, "Pop a few bubbles while I think ✨");
  const stop = tickingLabel("Thinking…", (l) => { if (gameOn) WaitGame.setStatus(l); else waitEl.textContent = l; });
  try {
    const res = await api(`/api/courses/${state.courseId}/chat`, { method: "POST", body: JSON.stringify({ messages: outgoing, topic_id: $("#coachSub").value || null }) });
    state.chat.push({ role: "assistant", content: res.content });
  } catch (err) {
    state.chat.push({ role: "assistant", content: "Request failed: " + err.message });
  } finally {
    stop(); WaitGame.unmount(); waitEl.hidden = true; waitEl.innerHTML = "";
    renderChat();
  }
});

function renderChat() {
  $("#chatLog").innerHTML = state.chat.map((m) => `<div class="bubble ${m.role === "user" ? "user" : "bot"}">${m.role === "user" ? escapeHtml(m.content) : renderMarkdown(m.content)}</div>`).join("");
  $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
}

(async function init() {
  await refreshHealth();
  await loadCourses();
})();
