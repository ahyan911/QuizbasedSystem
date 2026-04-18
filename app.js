/* ==============================================
   app.js — PyQuiz browser logic
   Drives all onclick="App..." handlers in index.html
   ============================================== */

const App = (() => {
  /* ---------- STATE ---------- */
  const state = {
    allQuestions: [],
    activeQuestions: [],
    currentIndex: 0,
    score: 0,
    correct: 0,
    wrong: 0,
    skipped: 0,
    penalty: 0,
    playerName: "",
    difficulty: "easy",
    negativeMarking: false,
    timeLeft: 30,
    timerId: null,
    answered: false,
    history: [],
  };

  const HISTORY_KEY = "pyquiz_history";
  const QUESTION_TIME = 30;
  const OPTION_LABELS = ["A", "B", "C", "D"];

  /* ---------- HELPERS ---------- */
  const $ = (id) => document.getElementById(id);

  const shuffle = (arr) => {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };

  const loadHistory = () => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      state.history = raw ? JSON.parse(raw) : [];
    } catch (_) {
      state.history = [];
    }
  };

  const saveHistory = () => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(state.history));
    } catch (_) {
      /* storage may be disabled — fail silently */
    }
  };

  /* ---------- SCREEN ROUTING ---------- */
  function showScreen(id) {
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    const target = $(id);
    if (target) target.classList.add("active");

    // Always stop any running timer when leaving the quiz screen
    if (id !== "screen-quiz") stopTimer();

    if (id === "screen-menu") renderLastScore();
    if (id === "screen-setup") resetSetupForm();
    if (id === "screen-history") renderHistory();
    if (id === "screen-analysis") renderAnalysis();

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* ---------- MENU: LAST SCORE BANNER ---------- */
  function renderLastScore() {
    const banner = $("last-score-banner");
    const content = $("last-score-content");
    if (!banner || !content) return;

    if (!state.history.length) {
      banner.style.display = "none";
      return;
    }
    const last = state.history[state.history.length - 1];
    banner.style.display = "block";
    content.innerHTML = `
      <p style="margin:4px 0;"><strong>${escapeHtml(last.name)}</strong> — ${last.score.toFixed(2)} / ${last.total}
      (${last.percentage}%) · <span class="rank-badge rank-${last.rank.toLowerCase()}">${last.rank}</span></p>
      <p class="text-muted" style="margin:4px 0;font-size:12px;">${last.date} · ${last.difficulty.toUpperCase()}</p>
    `;
  }

  /* ---------- SETUP ---------- */
  function resetSetupForm() {
    const nameEl = $("player-name");
    if (nameEl) nameEl.value = state.playerName || "";
    const err = $("name-error");
    if (err) err.style.display = "none";
    const neg = $("negative-marking");
    if (neg) neg.checked = state.negativeMarking;
    selectDifficulty(state.difficulty || "easy");
  }

  function selectDifficulty(diff) {
    state.difficulty = diff;
    document.querySelectorAll(".diff-btn").forEach((btn) => {
      btn.classList.toggle("selected", btn.dataset.diff === diff);
    });
  }

  /* ---------- QUIZ FLOW ---------- */
  function startQuiz() {
    const nameEl = $("player-name");
    const errEl = $("name-error");
    const name = nameEl ? nameEl.value.trim() : "";

    if (!name) {
      if (errEl) errEl.style.display = "block";
      if (nameEl) nameEl.focus();
      return;
    }
    if (errEl) errEl.style.display = "none";

    state.playerName = name;
    state.negativeMarking = !!$("negative-marking")?.checked;

    // Pick question pool
    let pool;
    if (state.difficulty === "mixed") {
      pool = shuffle(state.allQuestions).slice(0, 10);
    } else {
      pool = shuffle(state.allQuestions.filter((q) => q.difficulty === state.difficulty)).slice(0, 5);
    }

    if (!pool.length) {
      alert("No questions available for this difficulty.");
      return;
    }

    state.activeQuestions = pool;
    state.currentIndex = 0;
    state.score = 0;
    state.correct = 0;
    state.wrong = 0;
    state.skipped = 0;
    state.penalty = 0;

    $("q-total").textContent = state.activeQuestions.length;
    showScreen("screen-quiz");
    loadQuestion();
  }

  function loadQuestion() {
    const q = state.activeQuestions[state.currentIndex];
    state.answered = false;

    // Top bar
    $("q-current").textContent = state.currentIndex + 1;
    $("live-score").textContent = state.score.toFixed(2).replace(/\.00$/, "");
    $("progress-fill").style.width =
      `${(state.currentIndex / state.activeQuestions.length) * 100}%`;

    // Difficulty badge
    const badge = $("q-difficulty-badge");
    badge.className = `difficulty-badge badge-${q.difficulty}`;
    badge.textContent = `${cap(q.difficulty)} · ${q.category}`;

    // Question text (preserve line breaks from JSON)
    $("question-text").textContent = q.question;

    // Options
    const container = $("options-container");
    container.innerHTML = "";
    q.options.forEach((opt, i) => {
      const btn = document.createElement("button");
      btn.className = "option-btn";
      btn.innerHTML = `<span class="option-label">${OPTION_LABELS[i]}</span><span class="option-text"></span>`;
      btn.querySelector(".option-text").textContent = opt;
      btn.addEventListener("click", () => submitAnswer(i));
      container.appendChild(btn);
    });

    // Reset feedback + next button
    const fb = $("feedback-box");
    fb.className = "feedback-box";
    fb.innerHTML = "";
    $("next-btn").style.display = "none";

    startTimer();
  }

  function startTimer() {
    stopTimer();
    state.timeLeft = QUESTION_TIME;
    $("timer").textContent = state.timeLeft;
    $("timer").style.color = "";

    state.timerId = setInterval(() => {
      state.timeLeft--;
      $("timer").textContent = state.timeLeft;
      if (state.timeLeft <= 5) $("timer").style.color = "var(--danger)";
      if (state.timeLeft <= 0) {
        stopTimer();
        handleTimeout();
      }
    }, 1000);
  }

  function stopTimer() {
    if (state.timerId) {
      clearInterval(state.timerId);
      state.timerId = null;
    }
  }

  function submitAnswer(selectedIdx) {
    if (state.answered) return;
    state.answered = true;
    stopTimer();

    const q = state.activeQuestions[state.currentIndex];
    const correctIdx = q.answer;
    const buttons = document.querySelectorAll("#options-container .option-btn");

    buttons.forEach((b, i) => {
      b.disabled = true;
      if (i === correctIdx) b.classList.add("correct");
      if (i === selectedIdx && selectedIdx !== correctIdx) b.classList.add("wrong");
    });

    const fb = $("feedback-box");
    if (selectedIdx === correctIdx) {
      state.correct++;
      state.score += 1;
      fb.className = "feedback-box correct";
      fb.innerHTML = `<strong>✅ Correct!</strong> +1 mark<br><span style="opacity:.85">${escapeHtml(q.explanation)}</span>`;
    } else {
      state.wrong++;
      let penaltyText = "";
      if (state.negativeMarking) {
        state.score -= 0.25;
        state.penalty += 0.25;
        penaltyText = " <span style='opacity:.75'>(-0.25)</span>";
      }
      fb.className = "feedback-box wrong";
      fb.innerHTML = `<strong>❌ Wrong${penaltyText}.</strong> Correct answer: ${OPTION_LABELS[correctIdx]}. ${escapeHtml(q.options[correctIdx])}<br><span style="opacity:.85">${escapeHtml(q.explanation)}</span>`;
    }

    $("live-score").textContent = state.score.toFixed(2).replace(/\.00$/, "");
    $("next-btn").style.display = "inline-flex";
  }

  function handleTimeout() {
    if (state.answered) return;
    state.answered = true;

    const q = state.activeQuestions[state.currentIndex];
    state.skipped++;

    document.querySelectorAll("#options-container .option-btn").forEach((b, i) => {
      b.disabled = true;
      if (i === q.answer) b.classList.add("correct");
    });

    const fb = $("feedback-box");
    fb.className = "feedback-box timeout";
    fb.innerHTML = `<strong>⏰ Time's up!</strong> Correct answer: ${OPTION_LABELS[q.answer]}. ${escapeHtml(q.options[q.answer])}<br><span style="opacity:.85">${escapeHtml(q.explanation)}</span>`;

    $("next-btn").style.display = "inline-flex";
  }

  function nextQuestion() {
    state.currentIndex++;
    if (state.currentIndex >= state.activeQuestions.length) {
      endQuiz();
    } else {
      loadQuestion();
    }
  }

  /* ---------- RESULTS ---------- */
  function endQuiz() {
    stopTimer();
    const total = state.activeQuestions.length;
    const percentage = Math.max(0, (state.score / total) * 100);

    let rank, emoji, title, subtitle, feedback;
    if (percentage >= 90) {
      rank = "Expert"; emoji = "🏆"; title = "Outstanding!";
      subtitle = "You've mastered Python at this level.";
      feedback = `Phenomenal work, ${state.playerName}. Keep pushing deeper.`;
    } else if (percentage >= 70) {
      rank = "Advanced"; emoji = "🌟"; title = "Great Work!";
      subtitle = "Strong Python knowledge — polish the weak spots.";
      feedback = `Solid performance, ${state.playerName}. Review missed topics.`;
    } else if (percentage >= 45) {
      rank = "Intermediate"; emoji = "📚"; title = "Good Effort!";
      subtitle = "You're on the right track — keep practicing.";
      feedback = `Nice try, ${state.playerName}. Focus on loops, functions, and data structures.`;
    } else {
      rank = "Beginner"; emoji = "🌱"; title = "Keep Going!";
      subtitle = "Every expert was once a beginner.";
      feedback = `Don't give up, ${state.playerName}. Review the basics and try again.`;
    }

    $("results-emoji").textContent = emoji;
    $("results-title").textContent = title;
    $("results-subtitle").textContent = subtitle;
    $("final-score-num").textContent = state.score.toFixed(2).replace(/\.00$/, "");
    $("final-score-total").textContent = `out of ${total}`;
    $("stat-correct").textContent = state.correct;
    $("stat-wrong").textContent = state.wrong;
    $("stat-skipped").textContent = state.skipped;

    const rankBadge = $("rank-badge");
    rankBadge.className = `rank-badge rank-${rank.toLowerCase()}`;
    rankBadge.textContent = rank;
    $("rank-feedback").textContent = feedback;

    const penInfo = $("penalty-info");
    if (state.negativeMarking && state.penalty > 0) {
      penInfo.style.display = "block";
      $("penalty-amount").textContent = `-${state.penalty.toFixed(2)}`;
    } else {
      penInfo.style.display = "none";
    }

    // Save result
    const result = {
      name: state.playerName,
      score: state.score,
      total,
      percentage: Math.round(percentage * 10) / 10,
      correct: state.correct,
      wrong: state.wrong,
      skipped: state.skipped,
      difficulty: state.difficulty,
      rank,
      negative: state.negativeMarking,
      penalty: state.penalty,
      date: new Date().toLocaleString(),
    };
    state.history.push(result);
    saveHistory();

    showScreen("screen-results");
  }

  /* ---------- HISTORY SCREEN ---------- */
  function renderHistory() {
    const wrap = $("history-list-container");
    if (!wrap) return;
    if (!state.history.length) {
      wrap.innerHTML = `<p class="text-muted text-center mt-8">📋 No quiz attempts yet. Play your first quiz to see history here!</p>`;
      return;
    }
    const rows = state.history
      .slice()
      .reverse()
      .map((r, i) => `
        <div class="history-row">
          <div>
            <strong>${escapeHtml(r.name)}</strong>
            <span class="text-muted" style="font-size:12px;"> · ${r.date}</span>
          </div>
          <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
            <span class="difficulty-badge badge-${r.difficulty === 'mixed' ? 'easy' : r.difficulty}">${r.difficulty.toUpperCase()}</span>
            <span class="rank-badge rank-${r.rank.toLowerCase()}">${r.rank}</span>
            <strong>${r.score.toFixed(2)}/${r.total}</strong>
            <span class="text-muted">(${r.percentage}%)</span>
            ${r.negative ? '<span style="color:var(--warning);font-size:12px;">⚠️ Neg</span>' : ''}
          </div>
        </div>
      `).join("");
    wrap.innerHTML = rows;
  }

  /* ---------- ANALYSIS SCREEN ---------- */
  function renderAnalysis() {
    const wrap = $("analysis-content");
    if (!wrap) return;
    if (!state.history.length) {
      wrap.innerHTML = `<p class="text-muted text-center mt-8">📈 No data yet. Complete at least one quiz to see analysis!</p>`;
      return;
    }

    let totalCorrect = 0, totalWrong = 0, totalSkipped = 0;
    let totalScore = 0, totalPossible = 0;
    const rankCounts = { Beginner: 0, Intermediate: 0, Advanced: 0, Expert: 0 };

    state.history.forEach((r) => {
      totalCorrect += r.correct;
      totalWrong += r.wrong;
      totalSkipped += r.skipped;
      totalScore += r.score;
      totalPossible += r.total;
      if (rankCounts[r.rank] !== undefined) rankCounts[r.rank]++;
    });

    const answered = totalCorrect + totalWrong + totalSkipped;
    const accuracy = answered ? Math.round((totalCorrect / answered) * 100) : 0;
    const avgScore = totalScore / state.history.length;
    let bestRank = "Beginner";
    if (rankCounts.Expert) bestRank = "Expert";
    else if (rankCounts.Advanced) bestRank = "Advanced";
    else if (rankCounts.Intermediate) bestRank = "Intermediate";

    const pct = (n) => (answered ? Math.round((n / answered) * 100) : 0);

    wrap.innerHTML = `
      <div class="stats-row">
        <div class="stat-box"><div class="stat-val">${state.history.length}</div><div class="stat-lbl">Attempts</div></div>
        <div class="stat-box"><div class="stat-val">${avgScore.toFixed(2)}</div><div class="stat-lbl">Avg Score</div></div>
        <div class="stat-box correct"><div class="stat-val">${accuracy}%</div><div class="stat-lbl">Accuracy</div></div>
      </div>

      <div class="divider"></div>
      <p class="card-title">Answer Breakdown</p>
      ${barRow("✅ Correct", totalCorrect, pct(totalCorrect), "var(--success)")}
      ${barRow("❌ Wrong", totalWrong, pct(totalWrong), "var(--danger)")}
      ${barRow("⏭️ Skipped", totalSkipped, pct(totalSkipped), "var(--warning)")}

      <div class="divider"></div>
      <p class="card-title">Rank Distribution</p>
      <div style="display:flex;flex-direction:column;gap:8px;">
        ${Object.entries(rankCounts).map(([r, c]) =>
          `<div style="display:flex;justify-content:space-between;align-items:center;">
             <span class="rank-badge rank-${r.toLowerCase()}">${r}</span>
             <span class="text-muted">${c} ${c === 1 ? "time" : "times"}</span>
           </div>`
        ).join("")}
      </div>

      <div class="divider"></div>
      <p class="card-title">Best Rank Achieved</p>
      <div class="text-center"><span class="rank-badge rank-${bestRank.toLowerCase()}" style="font-size:16px;padding:8px 16px;">${bestRank}</span></div>
    `;
  }

  function barRow(label, count, pct, color) {
    return `
      <div style="margin:10px 0;">
        <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
          <span>${label}</span><span class="text-muted">${count} (${pct}%)</span>
        </div>
        <div class="progress-bar-wrap" style="height:8px;">
          <div class="progress-bar-fill" style="width:${pct}%;background:${color};"></div>
        </div>
      </div>
    `;
  }

  /* ---------- EXIT / RESET ---------- */
  function exitApp() {
    if (!confirm("⚠️ This will delete ALL saved history. Continue?")) return;
    state.history = [];
    try { localStorage.removeItem(HISTORY_KEY); } catch (_) {}
    alert("✅ All data cleared. Starting fresh.");
    renderLastScore();
    showScreen("screen-menu");
  }

  /* ---------- UTILS ---------- */
  function cap(s) { return s ? s[0].toUpperCase() + s.slice(1) : s; }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  /* ---------- INIT ---------- */
  async function init() {
    loadHistory();
    try {
      const res = await fetch("questions.json");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      state.allQuestions = await res.json();
    } catch (err) {
      console.error("Failed to load questions.json:", err);
      alert("❌ Could not load questions.json. Make sure it is in the same folder and you are serving this page over http(s), not file://.");
      return;
    }
    renderLastScore();
    selectDifficulty("easy");
  }

  document.addEventListener("DOMContentLoaded", init);

  /* ---------- PUBLIC API ---------- */
  return {
    showScreen,
    selectDifficulty,
    startQuiz,
    nextQuestion,
    exitApp,
  };
})();
