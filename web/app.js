const $ = (s) => document.querySelector(s);

const state = {
  meta: null,
  quiz: null,
  startedAt: null,
  timerId: null,
  remaining: 0,
  chat: [],
  flash: { allCards: [], cards: [], idx: 0, deck: "all" },
};

document.querySelectorAll(".tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((b) => b.classList.remove("on"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("on"));
    btn.classList.add("on");
    $("#tab-" + btn.dataset.tab).classList.add("on");
  });
});

async function api(path, opts) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

const COMPOSITE_LABELS = {
  cloud_native: "Cloud Native (overall)",
  aws: "AWS",
  terraform: "Terraform",
  kubernetes: "Kubernetes",
};

const BAND_LABELS = {
  ready: "Ready!",
  borderline: "Almost there",
  weak: "Keep practicing",
  untested: "Not started yet",
};

function bandEl(band) {
  const label = BAND_LABELS[band] || band;
  return `<span class="band ${band}">${label}</span>`;
}

const WaitGame = (() => {
  let container = null;
  let intervalId = null;
  let score = 0;
  const colors = ["var(--accent)", "var(--gold)", "var(--go)", "var(--warn)"];

  function spawnBubble(field) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "wait-bubble";
    b.setAttribute("aria-label", "Pop");
    const size = 34 + Math.random() * 30;
    b.style.width = `${size}px`;
    b.style.height = `${size}px`;
    b.style.left = `${Math.random() * 82}%`;
    b.style.background = colors[Math.floor(Math.random() * colors.length)];
    b.style.animationDuration = `${2.4 + Math.random() * 1.4}s`;
    const pop = () => {
      score += 1;
      updateScore();
      b.remove();
    };
    b.addEventListener("click", pop);
    b.addEventListener("animationend", () => b.remove());
    field.appendChild(b);
  }

  function updateScore() {
    if (!container) return;
    const el = container.querySelector(".wait-game-score");
    if (el) el.textContent = `Popped: ${score}`;
  }

  function setStatus(text) {
    if (!container) return;
    const el = container.querySelector(".wait-game-time");
    if (el) el.textContent = text;
  }

  function mount(target, label) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return false;
    score = 0;
    target.innerHTML = "";
    container = document.createElement("div");
    container.className = "wait-game";
    container.innerHTML = `
      <div class="wait-game-head">
        <span class="wait-game-label">${label || "While you wait, pop a few bubbles ☁"}</span>
        <span class="wait-game-meta"><span class="wait-game-time"></span> · <span class="wait-game-score">Popped: 0</span></span>
      </div>
      <div class="wait-game-field"></div>
    `;
    target.appendChild(container);
    const field = container.querySelector(".wait-game-field");
    spawnBubble(field);
    intervalId = setInterval(() => spawnBubble(field), 550);
    return true;
  }

  function unmount() {
    if (intervalId) clearInterval(intervalId);
    intervalId = null;
    container = null;
  }

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

function mdInline(s) {
  s = s.replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`);
  s = s.replace(/\*\*([^*]+)\*\*/g, (_, b) => `<strong>${b}</strong>`);
  s = s.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, (_, pre, i) => `${pre}<em>${i}</em>`);
  s = s.replace(/\\([\\`*_{}[\]()#+.!>~-])/g, "$1");
  return s;
}

function splitTableRow(line) {
  const cells = line.split("|");
  if (cells[0].trim() === "") cells.shift();
  if (cells.length && cells[cells.length - 1].trim() === "") cells.pop();
  return cells.map((c) => c.trim());
}

function renderMarkdown(src) {
  const lines = escapeHtml(src).split("\n");
  let html = "";
  let para = [];
  const flushPara = () => {
    if (para.length) {
      html += `<p>${mdInline(para.join(" "))}</p>`;
      para = [];
    }
  };
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    const ul = line.match(/^\s*[-*]\s+(.*)$/);
    const ol = line.match(/^\s*\d+\.\s+(.*)$/);
    const isPipeRow = /^\s*\|.*\|\s*$/.test(line);
    const nextIsSep = isPipeRow && lines[i + 1] && /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i + 1]) && lines[i + 1].includes("-");

    if (!line.trim()) {
      flushPara();
      i++;
      continue;
    }

    if (heading) {
      flushPara();
      const level = heading[1].length;
      html += `<h${level}>${mdInline(heading[2])}</h${level}>`;
      i++;
      continue;
    }

    if (nextIsSep) {
      flushPara();
      const headerCells = splitTableRow(line);
      let j = i + 2;
      const rows = [];
      while (j < lines.length && /^\s*\|.*\|\s*$/.test(lines[j])) {
        rows.push(splitTableRow(lines[j]));
        j++;
      }
      html +=
        "<table><thead><tr>" +
        headerCells.map((c) => `<th>${mdInline(c)}</th>`).join("") +
        "</tr></thead><tbody>" +
        rows.map((r) => "<tr>" + r.map((c) => `<td>${mdInline(c)}</td>`).join("") + "</tr>").join("") +
        "</tbody></table>";
      i = j;
      continue;
    }

    if (ul) {
      flushPara();
      const items = [];
      while (i < lines.length && lines[i].match(/^\s*[-*]\s+(.*)$/)) {
        items.push(lines[i].match(/^\s*[-*]\s+(.*)$/)[1]);
        i++;
      }
      html += "<ul>" + items.map((it) => `<li>${mdInline(it)}</li>`).join("") + "</ul>";
      continue;
    }

    if (ol) {
      flushPara();
      const items = [];
      while (i < lines.length && lines[i].match(/^\s*\d+\.\s+(.*)$/)) {
        items.push(lines[i].match(/^\s*\d+\.\s+(.*)$/)[1]);
        i++;
      }
      html += "<ol>" + items.map((it) => `<li>${mdInline(it)}</li>`).join("") + "</ol>";
      continue;
    }

    para.push(line.trim());
    i++;
  }
  flushPara();
  return html;
}

async function refreshHealth() {
  try {
    const h = await api("/api/health");
    const el = $("#llmStatus");
    el.classList.remove("status-ok", "status-warn", "status-bad");
    if (h.ollama && h.ollama.ok) {
      const models = (h.ollama.models || []).join(", ") || "model ready";
      el.textContent = "Ollama: " + models;
      el.classList.add("status-ok");
    } else {
      el.textContent = "Ollama offline — bank quizzes still work";
      el.classList.add("status-warn");
    }
  } catch {
    const el = $("#llmStatus");
    el.textContent = "API down";
    el.classList.remove("status-ok", "status-warn");
    el.classList.add("status-bad");
  }
}

async function refreshReady() {
  const r = await api("/api/readiness");
  $("#track").value = r.target_track || "full_stack_devops";
  $("#disclaimer").textContent = r.disclaimer;
  const primary = new Set(r.primary_composites || ["cloud_native", "aws", "terraform", "kubernetes"]);
  const order = ["cloud_native", "aws", "terraform", "kubernetes"];
  const names = order.filter((n) => r.composites[n]).concat(Object.keys(r.composites).filter((n) => !order.includes(n)));
  const cards = names
    .map((name) => {
      const c = r.composites[name];
      const pct = c.percent == null ? "—" : c.percent + "% practice";
      const floor = c.floor_percentile != null ? `~${c.floor_percentile}% published passing bar` : "no single published passing bar";
      const comp = c.competitive_percentile != null ? ` · this app's target ${c.competitive_percentile}+` : "";
      const dim = primary.has(name) ? "" : " dim";
      const tag = primary.has(name) ? "" : `<div class="muted">not prioritized by your current track</div>`;
      return `<div class="card${dim}"><h3>${COMPOSITE_LABELS[name] || name.replace("_", " ")}</h3>${bandEl(c.band)}<div>${pct}</div><div class="muted">${c.coverage}<br/>${floor}${comp}</div>${tag}</div>`;
    })
    .join("");
  $("#composites").innerHTML = cards;
  $("#actions").innerHTML = (r.next_actions || []).map((a) => `<li>${a}</li>`).join("");
  const rows = Object.entries(r.subtests)
    .map(([key, s]) => {
      const pct = s.percent == null ? "—" : s.percent + "%";
      return `<tr><td>${s.code}</td><td>${s.label}</td><td>${s.items} @ ~${s.pace}s</td><td>${s.attempts}</td><td>${pct}</td><td>${bandEl(s.band)}</td><td>${(s.top_miss_topics || []).join(", ")}</td></tr>`;
    })
    .join("");
  $("#subtests").innerHTML = `<table><thead><tr><th>ID</th><th>Topic</th><th>Drill size</th><th>Logged</th><th>Acc</th><th>Band</th><th>Miss tags</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function fillSelects(meta) {
  const subs = Object.entries(meta.subtests);
  const quiz = $("#quizSub");
  const coach = $("#coachSub");
  quiz.innerHTML = `<option value="mixed">Mixed</option>` + subs.map(([k, v]) => `<option value="${k}">${v.code} — ${v.label}</option>`).join("");
  coach.innerHTML = `<option value="">General</option>` + subs.map(([k, v]) => `<option value="${k}">${v.label}</option>`).join("");
}

$("#track").addEventListener("change", async (e) => {
  await api("/api/track", { method: "POST", body: JSON.stringify({ target_track: e.target.value }) });
  refreshReady();
});

$("#resetBtn").addEventListener("click", async () => {
  if (!confirm("Clear all your progress? This can't be undone.")) return;
  await api("/api/reset", { method: "POST" });
  refreshReady();
});

async function loadStudyPack() {
  const topic = $("#studyTopic").value;
  $("#studyOut").textContent = "Loading pack…";
  const pack = await api("/api/knowledge?topic=" + encodeURIComponent(topic));
  $("#studyOut").innerHTML = renderMarkdown(pack.content.replace(/^\n+/, ""));
}

$("#studyTopic").addEventListener("change", loadStudyPack);

$("#studyAsk").addEventListener("click", async () => {
  const topic = $("#studyTopic").value;
  const studyOut = $("#studyOut");
  const gameOn = WaitGame.mount(studyOut, "Pop a few bubbles while I put this together ☁");
  const stopTicker = tickingLabel("Coaching…", (label) => {
    if (gameOn) WaitGame.setStatus(label);
    else studyOut.textContent = label;
  });
  const messages = [
    {
      role: "user",
      content:
        "Teach this topic as a compact study brief: key concepts, one or two worked examples with real syntax (Terraform HCL, kubectl, or AWS CLI/IAM as appropriate), and common gotchas. Then give me 3 check questions with answers at the bottom.",
    },
  ];
  try {
    const res = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ messages, subtest: topic }),
    });
    const prefix = res.provider === "fallback" ? "**[offline excerpt]**\n\n" : "";
    studyOut.innerHTML = renderMarkdown(prefix + res.content);
  } catch (err) {
    studyOut.textContent = "Coaching request failed: " + err.message;
  } finally {
    stopTicker();
    WaitGame.unmount();
  }
});

function stopTimer() {
  if (state.timerId) clearInterval(state.timerId);
  state.timerId = null;
}

function tick() {
  state.remaining -= 1;
  const el = $("#timer");
  if (el) el.textContent = formatTime(Math.max(0, state.remaining));
  if (state.remaining <= 0) {
    stopTimer();
    submitQuiz(true);
  }
}

function formatTime(s) {
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
}

$("#startQuiz").addEventListener("click", startQuiz);

async function startQuiz() {
  stopTimer();
  const body = {
    subtest: $("#quizSub").value,
    n: Number($("#quizN").value),
    difficulty: $("#quizDiff").value,
    use_llm: $("#quizLlm").checked,
  };
  const quizBox = $("#quizBox");
  const useLlm = body.use_llm;
  let stopTicker = () => {};
  let gameOn = false;
  if (useLlm) {
    gameOn = WaitGame.mount(quizBox, "Pop a few bubbles while I build your quiz ☁");
    stopTicker = tickingLabel("Building quiz…", (label) => {
      if (gameOn) WaitGame.setStatus(label);
      else quizBox.textContent = label;
    });
  } else {
    quizBox.textContent = "Building quiz…";
  }
  let quiz;
  try {
    quiz = await api("/api/quiz", { method: "POST", body: JSON.stringify(body) });
  } finally {
    stopTicker();
    if (gameOn) WaitGame.unmount();
  }
  state.quiz = quiz;
  state.startedAt = Date.now();
  const timed = $("#quizTimed").checked;
  state.remaining = timed ? quiz.timed_seconds : 0;
  const metaLine = timed
    ? `${quiz.items.length} items · target ${quiz.target_pace_sec_per_item}s each · <span class="timer" id="timer">${formatTime(state.remaining)}</span>`
    : `${quiz.items.length} items · untimed · target ${quiz.target_pace_sec_per_item}s each`;
  const noteLine = quiz.note ? `<div class="quiz-note">${escapeHtml(quiz.note)}</div>` : "";
  $("#quizMeta").innerHTML = metaLine + noteLine;
  $("#quizBox").innerHTML =
    quiz.items
      .map((item, idx) => {
        const choices = (item.choices || [])
          .map((c) => `<label class="choice"><input type="radio" name="q${idx}" value="${c.trim()[0]}" /> ${c}</label>`)
          .join("");
        const vis = item.visual ? `<pre>${item.visual}</pre>` : "";
        const diffTag = item.difficulty ? `<span class="diff-tag ${item.difficulty}">${item.difficulty}</span>` : "";
        return `<div class="q" data-id="${item.id}" data-idx="${idx}"><div class="stem">${idx + 1}. ${item.stem} ${diffTag}</div>${vis}${choices}</div>`;
      })
      .join("") + `<button id="submitQuiz">See my score</button>`;
  $("#submitQuiz").addEventListener("click", () => submitQuiz(false));
  if (timed) state.timerId = setInterval(tick, 1000);
}

async function submitQuiz(auto) {
  if (!state.quiz) return;
  stopTimer();
  const responses = state.quiz.items.map((item, idx) => {
    const picked = document.querySelector(`input[name="q${idx}"]:checked`);
    return { id: item.id, selected: picked ? picked.value : "", time_sec: null };
  });
  const elapsed = (Date.now() - state.startedAt) / 1000;
  const out = await api("/api/grade", {
    method: "POST",
    body: JSON.stringify({
      subtest: state.quiz.subtest,
      quiz_id: state.quiz.quiz_id,
      elapsed_sec: elapsed,
      responses,
    }),
  });
  const g = out.graded;
  $("#quizMeta").innerHTML = `${auto ? "Time. " : ""}Score ${g.correct}/${g.total} (${g.percent}%). ${elapsed.toFixed(0)}s elapsed.`;
  document.querySelectorAll(".q").forEach((box) => {
    const id = box.dataset.id;
    const row = g.results.find((r) => r.id === id);
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
  const btn = $("#submitQuiz");
  if (btn) btn.remove();
  refreshReady();
}

function shuffleArray(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

async function loadFlashcards() {
  const data = await api("/api/flashcards");
  state.flash.allCards = data.cards;
  const sel = $("#cardDeck");
  sel.innerHTML =
    `<option value="all">All decks (${data.cards.length})</option>` +
    data.decks.map((d) => `<option value="${d.id}">${d.label} (${d.count})</option>`).join("");
  pickDeck("all");
}

function pickDeck(deck) {
  const pool = deck === "all" ? state.flash.allCards : state.flash.allCards.filter((c) => c.deck === deck);
  state.flash.deck = deck;
  state.flash.cards = shuffleArray(pool);
  state.flash.idx = 0;
  renderFlashcard();
}

function renderFlashcard() {
  const cards = state.flash.cards;
  const card = document.getElementById("flashcard");
  card.classList.remove("flipped");
  if (!cards.length) {
    $("#cardMeta").textContent = "No cards in this deck yet.";
    $("#cardFront").textContent = "";
    $("#cardBack").textContent = "";
    return;
  }
  const c = cards[state.flash.idx];
  $("#cardMeta").textContent = `Card ${state.flash.idx + 1} of ${cards.length}`;
  $("#cardFront").textContent = c.front;
  $("#cardBack").textContent = c.back;
}

function flipCard() {
  document.getElementById("flashcard").classList.toggle("flipped");
}

function nextCard() {
  if (!state.flash.cards.length) return;
  state.flash.idx = (state.flash.idx + 1) % state.flash.cards.length;
  renderFlashcard();
}

function prevCard() {
  if (!state.flash.cards.length) return;
  state.flash.idx = (state.flash.idx - 1 + state.flash.cards.length) % state.flash.cards.length;
  renderFlashcard();
}

$("#cardDeck").addEventListener("change", (e) => pickDeck(e.target.value));
$("#shuffleCards").addEventListener("click", () => pickDeck(state.flash.deck));
$("#cardFlip").addEventListener("click", flipCard);
$("#cardNext").addEventListener("click", nextCard);
$("#cardPrev").addEventListener("click", prevCard);
$("#flashcard").addEventListener("click", flipCard);
$("#flashcard").addEventListener("keydown", (e) => {
  if (e.key === " " || e.key === "Enter") {
    e.preventDefault();
    flipCard();
  } else if (e.key === "ArrowRight") {
    nextCard();
  } else if (e.key === "ArrowLeft") {
    prevCard();
  }
});

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
  const gameOn = WaitGame.mount(waitEl, "Pop a few bubbles while I think ☁");
  const stopTicker = tickingLabel("Thinking…", (label) => {
    if (gameOn) WaitGame.setStatus(label);
    else waitEl.textContent = label;
  });
  try {
    const res = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ messages: outgoing, subtest: $("#coachSub").value || null }),
    });
    state.chat.push({ role: "assistant", content: res.content });
  } catch (err) {
    state.chat.push({ role: "assistant", content: "Request failed: " + err.message });
  } finally {
    stopTicker();
    WaitGame.unmount();
    waitEl.hidden = true;
    waitEl.innerHTML = "";
    renderChat();
  }
});

function renderChat() {
  $("#chatLog").innerHTML = state.chat
    .map((m) => {
      const body = m.role === "user" ? escapeHtml(m.content) : renderMarkdown(m.content);
      return `<div class="bubble ${m.role === "user" ? "user" : "bot"}">${body}</div>`;
    })
    .join("");
  $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
}

function escapeHtml(s) {
  return s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

(async function init() {
  await refreshHealth();
  state.meta = await api("/api/meta");
  fillSelects(state.meta);
  await refreshReady();
  try { await loadStudyPack(); } catch (e) { /* pack loads when Study tab is used */ }
  try { await loadFlashcards(); } catch (e) { /* flashcards optional on init */ }
})();
