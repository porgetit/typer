const STATUS_LABELS = {
  no_text: "Sin texto",
  ready: "Listo",
  running: "En curso",
  completed: "Completado",
};

class TypingUI {
  constructor() {
    this.api = null;
    this.tickerId = null;
    this.payload = null;
    this.targetText = "";

    this.ui = {
      textRender: document.getElementById("textRender"),
      input: document.getElementById("input"),
      typingBox: document.getElementById("typingBox"),
      progress: document.getElementById("progress"),
      menuView: document.getElementById("menuView"),
      gameView: document.getElementById("gameView"),
      resultView: document.getElementById("resultView"),
      summaryView: document.getElementById("summaryView"),
      mTime: document.getElementById("mTime"),
      mWpm: document.getElementById("mWpm"),
      mAcc: document.getElementById("mAcc"),
      mErr: document.getElementById("mErr"),
      resultProgress: document.getElementById("resultProgress"),
      summaryList: document.getElementById("summaryList"),
      repeatBtn: document.getElementById("repeatBtn"),
      nextBtn: document.getElementById("nextBtn"),
      startBtn: document.getElementById("startBtn"),
      exitBtn: document.getElementById("exitBtn"),
      restartBtn: document.getElementById("restartBtn"),
      backToMenuBtn: document.getElementById("backToMenuBtn"),
    };
  }

  async init() {
    this.bindEvents();
    this.api = await this.waitForApi();

    if (!this.api) {
      return;
    }

    await this.api.current(); // initialize state
    this.setView("menu");
    this.ui.progress.textContent = "";
  }

  bindEvents() {
    this.ui.typingBox.addEventListener("click", () => this.focusInput());

    document.addEventListener("keydown", () => {
      // If the input loses focus (e.g., user clicked outside), reclaim focus on first key press.
      if (document.activeElement !== this.ui.input) {
        this.focusInput();
      }
    });
    document.addEventListener("keydown", (e) => {
      if (this.ui.resultView.classList.contains("active") && e.key === "Enter") {
        e.preventDefault();
        this.next().catch((err) => console.error(err));
      }
    });
    this.ui.startBtn.addEventListener("click", () =>
      this.startGame().catch((err) => console.error(err))
    );
    this.ui.exitBtn.addEventListener("click", () =>
      this.exitApp().catch((err) => console.error(err))
    );
    this.ui.restartBtn.addEventListener("click", () =>
      this.startGame().catch((err) => console.error(err))
    );
    this.ui.backToMenuBtn.addEventListener("click", () => this.setView("menu"));

    this.ui.input.addEventListener("focus", () => this.setFocusState(true));
    this.ui.input.addEventListener("blur", () => this.setFocusState(false));
    this.ui.input.addEventListener("input", () => this.handleInput());

    this.ui.repeatBtn.addEventListener("click", () =>
      this.repeat().catch((err) => console.error(err))
    );
    this.ui.nextBtn.addEventListener("click", () =>
      this.next().catch((err) => console.error(err))
    );
  }

  setView(name) {
    const views = ["menu", "game", "result", "summary"];
    const map = {
      menu: this.ui.menuView,
      game: this.ui.gameView,
      result: this.ui.resultView,
      summary: this.ui.summaryView,
    };
    views.forEach((v) => {
      map[v].classList.toggle("active", v === name);
    });
  }

  async startGame() {
    if (!this.api) return;
    const payload = await this.api.restart_progress();
    this.setView("game");
    this.ui.progress.textContent = payload?.bank_progress?.position || 0;
    this.applyPayload(payload, { resetInput: true, focus: true });
  }

  async exitApp() {
    try {
      if (this.api?.exit_app) {
        await this.api.exit_app();
      }
    } catch (err) {
      console.error(err);
    } finally {
      // fallback in case the bridge fails
      window.close();
    }
  }

  waitForApi() {
    if (window.pywebview?.api) return Promise.resolve(window.pywebview.api);

    return new Promise((resolve) => {
      const timeout = setTimeout(() => resolve(null), 3000);
      window.addEventListener("pywebviewready", () => {
        clearTimeout(timeout);
        resolve(window.pywebview.api);
      });
    });
  }

  focusInput() {
    this.ui.input.focus({ preventScroll: true });
  }

  setFocusState(isFocused) {
    this.ui.textRender.classList.toggle("blurred", !isFocused);
  }

  async handleInput() {
    if (!this.api) return;
    const typed = this.ui.input.value;
    const payload = await this.api.submit_input(typed);
    this.applyPayload(payload);
    const metrics = payload?.metrics;
    if (metrics?.finished) {
      this.stopTicker();
      this.showResult(payload);
    } else if (metrics?.started) {
      this.hideResult();
      this.startTicker();
    }
  }

  startTicker() {
    if (this.tickerId || !this.api) return;
    this.tickerId = window.setInterval(async () => {
      const payload = await this.api.tick();
      this.applyPayload(payload);
      if (payload?.metrics?.finished) {
        this.stopTicker();
        this.showResult(payload);
      }
    }, 150);
  }

  stopTicker() {
    if (this.tickerId) {
      clearInterval(this.tickerId);
      this.tickerId = null;
    }
  }

  applyPayload(payload, options = {}) {
    if (!payload) return;
    const { target_text: targetText, typed_text: acceptedText, metrics, bank_progress: bank } = payload;
    this.payload = payload;

    if (typeof targetText === "string") {
      this.targetText = targetText;
      if (options.resetInput) {
        this.ui.input.value = "";
      }
      this.ui.input.maxLength = targetText.length || "";
      if (options.focus) {
        this.focusInput();
      }
    }

    if (typeof acceptedText === "string") {
      this.ui.input.value = acceptedText;
    }

    if (bank) {
      this.ui.progress.textContent = bank.position || "";
      this.ui.nextBtn.disabled = !bank.has_next;
      this.ui.nextBtn.textContent = bank.has_next ? "Continuar" : "Resumen";
    }

    if (this.targetText) {
      const typedValue =
        typeof acceptedText === "string" ? acceptedText : this.ui.input.value;
      this.renderText(this.targetText, typedValue);
    }
  }

  renderText(target, typed) {
    const container = this.ui.textRender;
    container.innerHTML = "";
    const typedLength = typed.length;
    const targetLength = target.length;

    for (let i = 0; i < targetLength; i++) {
      const ch = target[i];
      const span = document.createElement("span");
      span.classList.add("char");
      // Render spaces as middle dots for visibility; keep other UTF-8 as-is.
      span.textContent = ch === " " ? "·" : ch;

      if (i < typedLength) {
        const correct = typed[i] === ch;
        span.classList.add(correct ? "correct" : "incorrect");
      }

      if (i === typedLength && typedLength < targetLength) {
        span.classList.add("cursor");
      }

      container.appendChild(span);
    }

    if (typedLength === targetLength && targetLength > 0) {
      // Add a cursor marker at the end to show completion.
      const endCursor = document.createElement("span");
      endCursor.classList.add("char", "cursor");
      endCursor.textContent = " ";
      container.appendChild(endCursor);
    }
  }

  showResult(payload) {
    if (!payload?.metrics) return;
    const { metrics, bank_progress: bank } = payload;
    this.ui.mTime.textContent = `${Number(metrics.elapsed_seconds).toFixed(2)}s`;
    this.ui.mWpm.textContent = String(metrics.wpm);
    this.ui.mAcc.textContent = `${Number(metrics.accuracy).toFixed(0)}%`;
    this.ui.mErr.textContent = String(metrics.errors);
    const bankText =
      bank && bank.total
        ? `${bank.position} / ${bank.total}`
        : "";
    this.ui.resultProgress.textContent = bankText;
    if (bank && !bank.has_next) {
      this.showSummary();
      return;
    }
    this.setView("result");
  }

  hideResult() {
    this.setView("game");
  }

  async repeat() {
    if (!this.api) return;
    this.stopTicker();
    const payload = await this.api.repeat_current();
    this.hideResult();
    this.applyPayload(payload, { resetInput: true, focus: true });
  }

  async next() {
    if (!this.api) return;
    this.stopTicker();
    const payload = await this.api.next_text();
    this.hideResult();
    this.applyPayload(payload, { resetInput: true, focus: true });
  }

  async showSummary() {
    if (!this.api) return;
    const data = await this.api.summary();
    const list = Array.isArray(data?.results) ? data.results : [];
    const avg = data?.averages || {};
    this.ui.summaryList.innerHTML = "";

    // Header row
    const header = document.createElement("div");
    header.classList.add("summary-row", "summary-header");
    header.innerHTML = `
      <div>#</div>
      <div>WPM</div>
      <div>Precisión</div>
      <div>Errores</div>
      <div>Tiempo</div>
    `;
    this.ui.summaryList.appendChild(header);

    list.forEach((item) => {
      const row = document.createElement("div");
      row.classList.add("summary-row");
      row.innerHTML = `
        <div>#${item.index}</div>
        <div>${item.wpm}</div>
        <div>${Math.round(item.accuracy)}%</div>
        <div>${item.errors}</div>
        <div>${Number(item.time).toFixed(2)}s</div>
      `;
      this.ui.summaryList.appendChild(row);
    });

    // Averages row
    const avgRow = document.createElement("div");
    avgRow.classList.add("summary-row", "summary-footer");
    avgRow.innerHTML = `
      <div>Promedio</div>
      <div>${Math.round(avg.wpm || 0)}</div>
      <div>${Math.round(avg.accuracy || 0)}%</div>
      <div>${Math.round(avg.errors || 0)}</div>
      <div>-</div>
    `;
    this.ui.summaryList.appendChild(avgRow);

    this.setView("summary");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const app = new TypingUI();
  app.init().catch((err) => console.error(err));
});
