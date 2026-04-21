const PAGE_SIZE_KB = 4;
const SPEED_DELAYS = { Slow: 900, Normal: 520, Fast: 220 };

const state = {
  result: null,
  comparison: null,
  animationTimer: null,
  currentStep: -1,
  charts: {
    faults: null,
    hits: null,
    rates: null,
  },
  pageUsageMap: new Map(),
  currentWorkloadType: "Custom",
};

const el = {
  loader: document.getElementById("loader"),
  scrollProgress: document.getElementById("scrollProgress"),
  framesInput: document.getElementById("framesInput"),
  pagesInput: document.getElementById("pagesInput"),
  algorithmSelect: document.getElementById("algorithmSelect"),
  speedSelect: document.getElementById("speedSelect"),
  workloadType: document.getElementById("workloadType"),
  maxPageInput: document.getElementById("maxPageInput"),
  requestCountInput: document.getElementById("requestCountInput"),
  timelineTableBody: document.querySelector("#timelineTable tbody"),
  framesGrid: document.getElementById("framesGrid"),
  comparisonBody: document.querySelector("#comparisonTable tbody"),
  analysisPanel: document.getElementById("analysisPanel"),

  heroRequests: document.getElementById("heroRequests"),
  heroFaults: document.getElementById("heroFaults"),
  heroHits: document.getElementById("heroHits"),
  heroFaultRate: document.getElementById("heroFaultRate"),
  metricRequests: document.getElementById("metricRequests"),
  metricFaults: document.getElementById("metricFaults"),
  metricHits: document.getElementById("metricHits"),
  metricFaultRate: document.getElementById("metricFaultRate"),
  internalFrag: document.getElementById("internalFrag"),
  externalFrag: document.getElementById("externalFrag"),
  holesCount: document.getElementById("holesCount"),
  usedBar: document.getElementById("usedBar"),
  freeBar: document.getElementById("freeBar"),
  usedMemory: document.getElementById("usedMemory"),
  freeMemory: document.getElementById("freeMemory"),
  utilPercent: document.getElementById("utilPercent"),
  utilProgress: document.getElementById("utilProgress"),
  faultChart: document.getElementById("faultChart"),
  hitChart: document.getElementById("hitChart"),
  rateChart: document.getElementById("rateChart"),
};

function parsePages(raw) {
  const values = raw
    .split(/[\s,]+/)
    .map((v) => v.trim())
    .filter(Boolean)
    .map((v) => Number(v));
  if (!values.length || values.some((v) => Number.isNaN(v) || v < 0)) {
    throw new Error("Page reference string must contain non-negative integers.");
  }
  return values;
}

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function createRipple(event) {
  const btn = event.currentTarget;
  const circle = document.createElement("span");
  const diameter = Math.max(btn.clientWidth, btn.clientHeight);
  const radius = diameter / 2;
  circle.style.width = circle.style.height = `${diameter}px`;
  circle.style.left = `${event.clientX - btn.getBoundingClientRect().left - radius}px`;
  circle.style.top = `${event.clientY - btn.getBoundingClientRect().top - radius}px`;
  circle.classList.add("ripple");
  const existing = btn.getElementsByClassName("ripple")[0];
  if (existing) existing.remove();
  btn.appendChild(circle);
}

function animateCounter(element, target, suffix = "", decimals = 0) {
  const start = Number((element.dataset.value || "0").replace("%", "")) || 0;
  const duration = 500;
  const startTime = performance.now();
  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const value = start + (target - start) * (1 - Math.pow(1 - progress, 3));
    element.textContent = `${value.toFixed(decimals)}${suffix}`;
    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      element.dataset.value = target;
    }
  }
  requestAnimationFrame(step);
}

function newPageUsage(page, usageMap) {
  if (!usageMap.has(page)) usageMap.set(page, randInt(1, PAGE_SIZE_KB));
  return usageMap.get(page);
}

function allocateFromHoles(holes, size) {
  for (let i = 0; i < holes.length; i += 1) {
    if (holes[i].size >= size) {
      holes[i].size -= size;
      holes[i].position += size;
      if (holes[i].size === 0) holes.splice(i, 1);
      return true;
    }
  }
  return false;
}

function simulateAlgorithm(pages, frames, algorithm) {
  if (frames <= 0) throw new Error("Frames must be > 0.");
  if (!pages.length) throw new Error("Page sequence cannot be empty.");

  const memory = [];
  const queue = [];
  const recent = new Map();
  const freq = new Map();
  const lfuBirth = new Map();
  const pageUsage = new Map();
  const holes = [];
  const steps = [];
  let faults = 0;
  let hits = 0;

  for (let i = 0; i < pages.length; i += 1) {
    const page = pages[i];
    const inMemory = memory.includes(page);
    let fault = !inMemory;
    let action = "Hit";
    let insertedPage = null;
    let replacedPage = null;

    if (algorithm === "FIFO") {
      if (fault) {
        faults += 1;
        allocateFromHoles(holes, PAGE_SIZE_KB);
        insertedPage = page;
        if (memory.length < frames) {
          memory.push(page);
          queue.push(page);
          action = `Loaded ${page}`;
        } else {
          const victim = queue.shift();
          replacedPage = victim;
          const idx = memory.indexOf(victim);
          memory[idx] = page;
          queue.push(page);
          holes.push({ position: victim * 100 + i, size: PAGE_SIZE_KB });
          action = `Replaced ${victim}`;
        }
      } else {
        hits += 1;
      }
    } else if (algorithm === "LRU") {
      if (fault) {
        faults += 1;
        allocateFromHoles(holes, PAGE_SIZE_KB);
        insertedPage = page;
        if (memory.length < frames) {
          memory.push(page);
          action = `Loaded ${page}`;
        } else {
          const victim = memory.reduce((acc, p) => {
            const val = recent.get(p) ?? -1;
            const accVal = recent.get(acc) ?? -1;
            return val < accVal ? p : acc;
          }, memory[0]);
          replacedPage = victim;
          memory[memory.indexOf(victim)] = page;
          holes.push({ position: victim * 100 + i, size: PAGE_SIZE_KB });
          action = `Replaced ${victim}`;
        }
      } else {
        hits += 1;
      }
      recent.set(page, i);
    } else if (algorithm === "Optimal") {
      if (fault) {
        faults += 1;
        allocateFromHoles(holes, PAGE_SIZE_KB);
        insertedPage = page;
        if (memory.length < frames) {
          memory.push(page);
          action = `Loaded ${page}`;
        } else {
          const future = pages.slice(i + 1);
          let victim = memory[0];
          let farthest = -1;
          for (const candidate of memory) {
            const next = future.indexOf(candidate);
            if (next === -1) {
              victim = candidate;
              farthest = Infinity;
              break;
            }
            if (next > farthest) {
              farthest = next;
              victim = candidate;
            }
          }
          replacedPage = victim;
          memory[memory.indexOf(victim)] = page;
          holes.push({ position: victim * 100 + i, size: PAGE_SIZE_KB });
          action = `Replaced ${victim}`;
        }
      } else {
        hits += 1;
      }
    } else if (algorithm === "LFU") {
      if (fault) {
        faults += 1;
        allocateFromHoles(holes, PAGE_SIZE_KB);
        insertedPage = page;
        if (memory.length < frames) {
          memory.push(page);
          lfuBirth.set(page, i);
          action = `Loaded ${page}`;
        } else {
          let victim = memory[0];
          for (const candidate of memory) {
            const candFreq = freq.get(candidate) || 0;
            const vicFreq = freq.get(victim) || 0;
            if (candFreq < vicFreq) {
              victim = candidate;
            } else if (candFreq === vicFreq) {
              const candBirth = lfuBirth.get(candidate) ?? Number.MAX_SAFE_INTEGER;
              const vicBirth = lfuBirth.get(victim) ?? Number.MAX_SAFE_INTEGER;
              if (candBirth < vicBirth) victim = candidate;
            }
          }
          replacedPage = victim;
          memory[memory.indexOf(victim)] = page;
          lfuBirth.delete(victim);
          lfuBirth.set(page, i);
          holes.push({ position: victim * 100 + i, size: PAGE_SIZE_KB });
          action = `Replaced ${victim}`;
        }
      } else {
        hits += 1;
      }
    }

    freq.set(page, (freq.get(page) || 0) + 1);

    let internal = 0;
    memory.forEach((p) => {
      const usage = newPageUsage(p, pageUsage);
      internal += PAGE_SIZE_KB - usage;
    });

    const external = holes.reduce((sum, h) => sum + h.size, 0);
    const holesCount = holes.length;

    const totalMem = frames * PAGE_SIZE_KB;
    const usedMem = memory.length * PAGE_SIZE_KB;
    const freeMem = totalMem - usedMem;
    const util = totalMem ? (usedMem / totalMem) * 100 : 0;

    steps.push({
      index: i + 1,
      request: page,
      fault,
      result: fault ? "Fault" : "Hit",
      action,
      frames: [...memory],
      insertedPage,
      replacedPage,
      faults,
      hits,
      faultRate: (faults / (i + 1)) * 100,
      internalFrag: internal,
      externalFrag: external,
      holesCount,
      usedMem,
      freeMem,
      util,
    });
  }

  return {
    algorithm,
    pages,
    frames,
    faults,
    hits,
    faultRate: (faults / pages.length) * 100,
    steps,
  };
}

function generateWorkload(type, maxPage, count) {
  if (type === "Custom") return null;
  const arr = [];
  const m = Math.max(1, maxPage);
  const n = Math.max(1, count);

  if (type === "Random") {
    for (let i = 0; i < n; i += 1) arr.push(randInt(0, m));
  } else if (type === "Locality of Reference") {
    let current = randInt(0, m);
    for (let i = 0; i < n; i += 1) {
      arr.push(current);
      if (Math.random() < 0.72) {
        current = Math.max(0, Math.min(m, current + randInt(-2, 2)));
      } else {
        current = randInt(0, m);
      }
    }
  } else if (type === "Looping Pattern") {
    const loop = [1, 2, 3, 1, 2, 3].map((v) => Math.min(v, m));
    for (let i = 0; i < n; i += 1) arr.push(loop[i % loop.length]);
  } else if (type === "Burst") {
    let i = 0;
    while (i < n) {
      const base = randInt(0, m);
      const burst = randInt(3, 6);
      for (let j = 0; j < burst && i < n; j += 1) {
        arr.push(Math.max(0, Math.min(m, base + randInt(-1, 1))));
        i += 1;
      }
    }
  }

  return arr;
}

function clearAnimation() {
  if (state.animationTimer) {
    clearTimeout(state.animationTimer);
    state.animationTimer = null;
  }
}

function setSummary(result) {
  const last = result.steps[result.steps.length - 1] || null;
  const algorithmInsights = {
    FIFO: "FIFO is simple and deterministic but can evict still-useful pages.",
    LRU: "LRU benefits locality-heavy access patterns by preserving recently used pages.",
    Optimal: "Optimal is theoretical best-case and useful as a lower-bound benchmark.",
    LFU: "LFU favors frequently accessed pages and can outperform under stable frequency patterns.",
  };
  const text = [
    `Algorithm: ${result.algorithm}`,
    `Frames: ${result.frames}`,
    `Total Requests: ${result.pages.length}`,
    `Page Faults: ${result.faults}`,
    `Hits: ${result.hits}`,
    `Fault Rate: ${result.faultRate.toFixed(2)}%`,
    "",
    "Fragmentation",
    `Internal Fragmentation: ${(last?.internalFrag || 0).toFixed(2)} KB`,
    `External Fragmentation: ${(last?.externalFrag || 0).toFixed(2)} KB`,
    `Memory Holes: ${last?.holesCount || 0}`,
    "",
    "Interpretation",
    algorithmInsights[result.algorithm] || "",
    "Frame and timeline animations expose demand paging behavior with hit/fault transitions.",
  ].join("\n");
  el.analysisPanel.textContent = text;
}

function updateMetrics(result, step = null) {
  const req = step ? step.index : result.pages.length;
  const faults = step ? step.faults : result.faults;
  const hits = step ? step.hits : result.hits;
  const rate = req ? (faults / req) * 100 : 0;

  [el.heroRequests, el.metricRequests].forEach((node) => animateCounter(node, req, "", 0));
  [el.heroFaults, el.metricFaults].forEach((node) => animateCounter(node, faults, "", 0));
  [el.heroHits, el.metricHits].forEach((node) => animateCounter(node, hits, "", 0));
  [el.heroFaultRate, el.metricFaultRate].forEach((node) => animateCounter(node, rate, "%", 1));
}

function updateFragmentation(step) {
  const internal = step?.internalFrag || 0;
  const external = step?.externalFrag || 0;
  const holes = step?.holesCount || 0;

  el.internalFrag.textContent = `${internal.toFixed(2)} KB`;
  el.externalFrag.textContent = `${external.toFixed(2)} KB`;
  el.holesCount.textContent = String(holes);

  const total = (step?.usedMem || 0) + (step?.freeMem || 0);
  const usedPct = total ? (step.usedMem / total) * 100 : 0;
  el.usedBar.style.width = `${usedPct}%`;
  el.freeBar.style.width = `${100 - usedPct}%`;
}

function updateUtil(step) {
  const used = step?.usedMem || 0;
  const free = step?.freeMem || 0;
  const util = step?.util || 0;
  el.usedMemory.textContent = `${used.toFixed(0)} KB`;
  el.freeMemory.textContent = `${free.toFixed(0)} KB`;
  el.utilPercent.textContent = `${util.toFixed(1)}%`;
  el.utilProgress.style.width = `${util}%`;
}

function renderFrames(step, framesCount) {
  const curFrames = step?.frames || [];
  const inserted = step?.insertedPage;
  const replaced = step?.replacedPage;
  const isFaultStep = Boolean(step?.fault);
  el.framesGrid.innerHTML = "";
  for (let i = 0; i < framesCount; i += 1) {
    const frameVal = curFrames[i];
    const card = document.createElement("div");
    card.className = "frame-card";
    if (isFaultStep && frameVal === inserted) card.classList.add("inserted");
    if (replaced !== null && replaced !== undefined && isFaultStep && frameVal === inserted) card.classList.add("replaced");
    card.innerHTML = `<div class="f-label">Frame ${i + 1}</div><div class="f-value">${frameVal === undefined ? "-" : frameVal}</div>`;
    el.framesGrid.appendChild(card);
  }
}

function renderTimeline(result) {
  el.timelineTableBody.innerHTML = "";
  result.steps.forEach((s) => {
    const row = document.createElement("tr");
    row.dataset.step = String(s.index);
    row.className = s.fault ? "fault-row" : "hit-row";
    row.innerHTML = `
          <td>${s.index}</td>
          <td>${s.request}</td>
          <td>${s.result}</td>
          <td>[${s.frames.join(", ")}]</td>
        `;
    el.timelineTableBody.appendChild(row);
  });
}

function markActiveTimeline(stepIndex) {
  [...el.timelineTableBody.querySelectorAll("tr")].forEach((r) => r.classList.remove("active-step"));
  const row = el.timelineTableBody.querySelector(`tr[data-step="${stepIndex}"]`);
  if (row) {
    row.classList.add("active-step");
    row.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

function renderCharts(result) {
  const labels = result.steps.map((s) => s.index);
  const faults = result.steps.map((s) => s.faults);
  const hits = result.steps.map((s) => s.hits);
  const rates = result.steps.map((s) => Number(s.faultRate.toFixed(2)));

  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: {
        ticks: { color: "#5f4d32" },
        grid: { color: "rgba(126,98,56,0.2)" },
      },
      y: {
        ticks: { color: "#5f4d32" },
        grid: { color: "rgba(126,98,56,0.2)" },
      },
    },
  };

  ["faults", "hits", "rates"].forEach((k) => {
    if (state.charts[k]) state.charts[k].destroy();
  });

  state.charts.faults = new Chart(el.faultChart, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: faults,
        borderColor: "#d64f4f",
        backgroundColor: "rgba(214,79,79,0.2)",
        fill: true,
        tension: 0.25,
      }],
    },
    options: baseOptions,
  });

  state.charts.hits = new Chart(el.hitChart, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: hits,
        borderColor: "#2f9f60",
        backgroundColor: "rgba(47,159,96,0.22)",
        fill: true,
        tension: 0.25,
      }],
    },
    options: baseOptions,
  });

  state.charts.rates = new Chart(el.rateChart, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data: rates,
        backgroundColor: "rgba(47,120,183,0.8)",
        borderColor: "#2f78b7",
      }],
    },
    options: baseOptions,
  });
}

function runSimulation(animated = true) {
  clearAnimation();
  try {
    const frames = Number(el.framesInput.value);
    const pages = parsePages(el.pagesInput.value);
    const algorithm = el.algorithmSelect.value;
    const result = simulateAlgorithm(pages, frames, algorithm);
    state.result = result;
    state.currentStep = -1;

    renderTimeline(result);
    renderFrames(null, frames);
    renderCharts(result);
    setSummary(result);

    if (!animated) {
      const last = result.steps[result.steps.length - 1];
      updateMetrics(result);
      updateFragmentation(last);
      updateUtil(last);
      renderFrames(last, frames);
      markActiveTimeline(last.index);
      return;
    }

    const delay = SPEED_DELAYS[el.speedSelect.value] || SPEED_DELAYS.Normal;
    const next = () => {
      state.currentStep += 1;
      if (state.currentStep >= result.steps.length) {
        clearAnimation();
        return;
      }
      const step = result.steps[state.currentStep];
      updateMetrics(result, step);
      updateFragmentation(step);
      updateUtil(step);
      renderFrames(step, frames);
      markActiveTimeline(step.index);
      state.animationTimer = setTimeout(next, delay);
    };
    next();
  } catch (err) {
    alert(err.message);
  }
}

function compareAll() {
  try {
    const frames = Number(el.framesInput.value);
    const pages = parsePages(el.pagesInput.value);
    const algorithms = ["FIFO", "LRU", "Optimal"];
    const results = algorithms.map((algo) => simulateAlgorithm(pages, frames, algo));
    state.comparison = results;

    el.comparisonBody.innerHTML = "";
    let best = results[0];
    for (const r of results) if (r.faultRate < best.faultRate) best = r;

    results.forEach((r) => {
      const row = document.createElement("tr");
      if (r.algorithm === best.algorithm) row.classList.add("comparison-best");
      row.innerHTML = `
            <td>${r.algorithm}</td>
            <td>${r.faults}</td>
            <td>${r.hits}</td>
            <td>${r.faultRate.toFixed(2)}%</td>
          `;
      el.comparisonBody.appendChild(row);
    });
  } catch (err) {
    alert(err.message);
  }
}

function generateWorkloadAndApply() {
  const type = el.workloadType.value;
  const maxPage = Number(el.maxPageInput.value);
  const count = Number(el.requestCountInput.value);
  const data = generateWorkload(type, maxPage, count);
  state.currentWorkloadType = type;
  if (data) {
    el.pagesInput.value = data.join(" ");
  }
}

function clearAll() {
  clearAnimation();
  state.result = null;
  state.comparison = null;
  state.currentStep = -1;
  el.timelineTableBody.innerHTML = "";
  el.comparisonBody.innerHTML = "";
  el.framesGrid.innerHTML = "";
  el.analysisPanel.textContent = "Run a simulation to generate analysis.";

  [el.heroRequests, el.heroFaults, el.heroHits, el.metricRequests, el.metricFaults, el.metricHits].forEach((n) => {
    n.textContent = "0";
    n.dataset.value = "0";
  });
  [el.heroFaultRate, el.metricFaultRate].forEach((n) => {
    n.textContent = "0%";
    n.dataset.value = "0";
  });

  el.internalFrag.textContent = "0 KB";
  el.externalFrag.textContent = "0 KB";
  el.holesCount.textContent = "0";
  el.usedBar.style.width = "0%";
  el.freeBar.style.width = "100%";
  el.usedMemory.textContent = "0 KB";
  el.freeMemory.textContent = "0 KB";
  el.utilPercent.textContent = "0%";
  el.utilProgress.style.width = "0%";

  ["faults", "hits", "rates"].forEach((k) => {
    if (state.charts[k]) {
      state.charts[k].destroy();
      state.charts[k] = null;
    }
  });
}

function buildExportPayload() {
  if (!state.result) return null;
  const last = state.result.steps[state.result.steps.length - 1] || {};
  return {
    title: "Virtual Memory Optimization Simulator",
    generatedAt: new Date().toISOString(),
    input: {
      frames: Number(el.framesInput.value),
      algorithm: el.algorithmSelect.value,
      workloadType: state.currentWorkloadType,
      pageSequence: state.result.pages,
      requests: state.result.pages.length,
    },
    output: {
      faults: state.result.faults,
      hits: state.result.hits,
      faultRatePercent: Number(state.result.faultRate.toFixed(2)),
      fragmentation: {
        internalKB: Number((last.internalFrag || 0).toFixed(2)),
        externalKB: Number((last.externalFrag || 0).toFixed(2)),
        holes: last.holesCount || 0,
      },
      utilization: {
        usedKB: last.usedMem || 0,
        freeKB: last.freeMem || 0,
        percent: Number((last.util || 0).toFixed(2)),
      },
    },
    comparison: state.comparison
      ? state.comparison.map((r) => ({
        algorithm: r.algorithm,
        faults: r.faults,
        hits: r.hits,
        faultRatePercent: Number(r.faultRate.toFixed(2)),
      }))
      : null,
  };
}

function downloadJSON() {
  const payload = buildExportPayload();
  if (!payload) {
    alert("Run a simulation before exporting.");
    return;
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `vm_simulator_report_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function downloadPDF() {
  const payload = buildExportPayload();
  if (!payload) {
    alert("Run a simulation before exporting.");
    return;
  }
  const { jsPDF } = window.jspdf || {};
  if (!jsPDF) {
    alert("PDF library unavailable.");
    return;
  }
  const doc = new jsPDF();
  let y = 16;
  doc.setFontSize(16);
  doc.text("Virtual Memory Optimization Simulator Report", 14, y);
  y += 10;

  doc.setFontSize(11);
  const lines = [
    `Generated At: ${payload.generatedAt}`,
    `Algorithm: ${payload.input.algorithm}`,
    `Frames: ${payload.input.frames}`,
    `Requests: ${payload.input.requests}`,
    `Faults: ${payload.output.faults}`,
    `Hits: ${payload.output.hits}`,
    `Fault Rate: ${payload.output.faultRatePercent}%`,
    `Internal Fragmentation: ${payload.output.fragmentation.internalKB} KB`,
    `External Fragmentation: ${payload.output.fragmentation.externalKB} KB`,
    `Memory Holes: ${payload.output.fragmentation.holes}`,
    `Utilization: ${payload.output.utilization.percent}%`,
  ];
  lines.forEach((line) => {
    doc.text(line, 14, y);
    y += 7;
  });

  if (payload.comparison) {
    y += 5;
    doc.setFontSize(12);
    doc.text("Comparison", 14, y);
    y += 8;
    doc.setFontSize(10);
    payload.comparison.forEach((c) => {
      doc.text(`${c.algorithm}: Faults=${c.faults}, Hits=${c.hits}, FaultRate=${c.faultRatePercent}%`, 14, y);
      y += 6;
    });
  }

  doc.save(`vm_simulator_report_${Date.now()}.pdf`);
}

function initFadeSections() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add("visible");
    });
  }, { threshold: 0.14 });
  document.querySelectorAll(".fade-section").forEach((section) => observer.observe(section));
}

function initScrollProgress() {
  const update = () => {
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const pct = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
    el.scrollProgress.style.width = `${pct}%`;
  };
  window.addEventListener("scroll", update);
  update();
}

function initEvents() {
  document.querySelectorAll(".ripple-btn").forEach((btn) => btn.addEventListener("click", createRipple));

  document.getElementById("heroRun").addEventListener("click", () => runSimulation(true));
  document.getElementById("runFromNav").addEventListener("click", () => runSimulation(true));
  document.getElementById("runAnimatedBtn").addEventListener("click", () => runSimulation(true));
  document.getElementById("instantViewBtn").addEventListener("click", () => runSimulation(false));
  document.getElementById("compareAllBtn").addEventListener("click", compareAll);
  document.getElementById("clearBtn").addEventListener("click", clearAll);

  document.getElementById("heroExplore").addEventListener("click", () => {
    document.getElementById("simulator").scrollIntoView({ behavior: "smooth" });
  });

  document.getElementById("generateWorkloadBtn").addEventListener("click", generateWorkloadAndApply);
  document.getElementById("generateWorkloadFromSimulatorBtn").addEventListener("click", () => {
    document.getElementById("workload").scrollIntoView({ behavior: "smooth" });
  });

  document.getElementById("downloadJsonBtn").addEventListener("click", downloadJSON);
  document.getElementById("downloadPdfBtn").addEventListener("click", downloadPDF);

  window.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runSimulation(true);
    if (e.key === "Escape") clearAll();
  });
}

function init() {
  if ("scrollRestoration" in history) {
    history.scrollRestoration = "manual";
  }
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  initFadeSections();
  initScrollProgress();
  initEvents();
  setTimeout(() => el.loader.classList.add("hidden"), 900);
  compareAll();
  runSimulation(false);
}

init();
