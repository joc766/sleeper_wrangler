import Chart from "chart.js/auto";

const notice = document.getElementById("chart-notice");
const results = document.getElementById("chart-results");
const users = document.getElementById("chart-users");
let chart;
let loading = false;
let successfulWeekKey = null;
let currentWeekKey = null;
let historyViewActive = false;

async function loadCounts(force = false) {
  if (!currentWeekKey) {
    notice.hidden = false;
    notice.textContent = "Waiting for the current week status…";
    return;
  }
  if (
    loading ||
    (!force && currentWeekKey && successfulWeekKey === currentWeekKey)
  )
    return;
  const requestedWeekKey = currentWeekKey;
  loading = true;
  try {
    const response = await fetch("/loserCounts");
    if (!response.ok) throw new Error("Could not fetch loser counts");
    const records = (await response.json()) ?? [];
    if (!Array.isArray(records)) throw new Error("Invalid loser records");

    const counts = new Map();
    const seasons = new Set();
    for (const record of records) {
      if (
        !record ||
        typeof record.Username !== "string" ||
        !record.Username.trim()
      ) {
        throw new Error("Invalid manager name");
      }
      const season = String(record.Season ?? "");
      if (!/^\d{4}$/.test(season)) throw new Error("Invalid season");
      seasons.add(season);
      const player = counts.get(record.Username) ?? {
        total: 0,
        seasons: new Map(),
        weeks: new Map(),
      };
      player.total += 1;
      player.seasons.set(season, (player.seasons.get(season) ?? 0) + 1);
      const weeks = player.weeks.get(season) ?? [];
      weeks.push(record.Week);
      player.weeks.set(season, weeks);
      counts.set(record.Username, player);
    }
    const entries = [...counts].sort(
      ([nameA, a], [nameB, b]) =>
        b.total - a.total || nameA.localeCompare(nameB),
    );
    if (!entries.length) {
      notice.textContent = "No loser records available yet.";
      notice.hidden = false;
      if (!chart) results.hidden = true;
      successfulWeekKey = requestedWeekKey;
      return;
    }

    const orderedSeasons = [...seasons].sort((a, b) => Number(a) - Number(b));
    const latestSeason = orderedSeasons.at(-1);
    const latestWeek = Math.max(
      ...records
        .filter((record) => String(record.Season) === latestSeason)
        .map((record) => record.Week),
    );
    document.getElementById("chart-week").textContent =
      `Through Week ${latestWeek}`;
    for (const [, player] of entries) {
      for (const weeks of player.weeks.values()) weeks.sort((a, b) => a - b);
    }
    const colors = [
      "#243f65",
      "#6685a8",
      "#e99b24",
      "#ffe096",
      "#367f78",
      "#9a719c",
    ];
    const rows = document.createDocumentFragment();
    for (const [username, player] of entries) {
      const row = document.createElement("li");
      row.textContent = `${username}: ${player.total} total losses. ${orderedSeasons.map((season) => `${season}: ${player.seasons.get(season) ?? 0} losses${player.weeks.has(season) ? ` (weeks ${player.weeks.get(season).join(", ")})` : ""}`).join("; ")}.`;
      rows.append(row);
    }
    users.replaceChildren(rows);
    // summary.textContent = `${records.length} recorded losing ${records.length === 1 ? "week" : "weeks"} · ${entries.length} ${entries.length === 1 ? "manager" : "managers"}`;
    const canvas = document.getElementById("losses-chart");
    canvas.parentElement.style.height = `${Math.max(320, entries.length * 48 + 100)}px`;
    chart?.destroy();
    const compactLegend = window.matchMedia("(max-width: 40rem)").matches;
    chart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: entries.map(([name, player]) => `${name} (${player.total})`),
        datasets: orderedSeasons.map((season, index) => ({
          label: season,
          data: entries.map(([, player]) => player.seasons.get(season) ?? 0),
          backgroundColor: colors[index % colors.length],
          maxBarThickness: 28,
        })),
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        color: "#182b45",
        font: { family: getComputedStyle(document.body).fontFamily },
        animation: false,
        scales: {
          x: {
            stacked: true,
            beginAtZero: true,
            // max: Math.ceil(entries[0][1].total * 1.2),
            max: entries[0][1].total,
            ticks: { precision: 0, color: "#58677a" },
            grid: { color: "#e7ebf1" },
            title: { display: true, text: "Total losses", color: "#58677a" },
          },
          y: {
            stacked: true,
            grid: { display: false },
            ticks: {
              color: "#182b45",
              autoSkip: false,
              font: { size: compactLegend ? 10 : 12 },
            },
          },
        },
        plugins: {
          legend: {
            position: "bottom",
            onClick: () => {},
            labels: {
              boxWidth: compactLegend ? 12 : 40,
              boxHeight: compactLegend ? 10 : 12,
              padding: compactLegend ? 6 : 10,
              font: { size: compactLegend ? 10 : 12 },
            },
          },
          tooltip: {
            callbacks: {
              title: ([context]) =>
                `${entries[context.dataIndex][0]} — ${context.dataset.label}`,
              label: (context) =>
                `${context.parsed.x} ${context.parsed.x === 1 ? "loss" : "losses"}`,
              afterLabel: (context) => {
                const weeks =
                  entries[context.dataIndex][1].weeks.get(
                    context.dataset.label,
                  ) ?? [];
                return `${weeks.length === 1 ? "Week" : "Weeks"} ${weeks.join(", ")}`;
              },
            },
          },
        },
      },
    });
    successfulWeekKey = requestedWeekKey;
    notice.hidden = true;
    results.hidden = false;
  } catch {
    if (!chart) results.hidden = true;
    notice.hidden = false;
    notice.textContent = chart
      ? "Could not refresh loser counts. Showing the last loaded chart."
      : "Could not load loser counts. Open the Chart tab to try again.";
  } finally {
    loading = false;
    if (
      historyViewActive &&
      currentWeekKey &&
      requestedWeekKey !== currentWeekKey &&
      successfulWeekKey !== currentWeekKey
    ) {
      loadCounts();
    }
  }
}

function calculatedWeekKey(update) {
  if (
    !/^\d{4}$/.test(String(update.season)) ||
    !Number.isInteger(update.week) ||
    update.week < 1
  ) {
    return null;
  }
  return JSON.stringify([
    String(update.season),
    update.week + (update.is_complete ? 1 : 0),
  ]);
}

function handleProjectionUpdate(update) {
  currentWeekKey = calculatedWeekKey(update);
  if (historyViewActive) loadCounts();
}

document.addEventListener("projection-update", (event) =>
  handleProjectionUpdate(event.detail),
);
if (window.latestProjectionUpdate)
  handleProjectionUpdate(window.latestProjectionUpdate);

const projectionsToggle = document.getElementById("projections-toggle");
const historyToggle = document.getElementById("history-toggle");

function switchView(showHistory) {
  const wasHistoryActive = historyViewActive;
  historyViewActive = showHistory;
  const projectionsView = document.getElementById("projections-view");
  const historyView = document.getElementById("history-view");
  projectionsView.hidden = showHistory;
  historyView.hidden = !showHistory;
  document.querySelector("main").classList.toggle("counts-chart", showHistory);
  projectionsToggle.setAttribute("aria-pressed", String(!showHistory));
  historyToggle.setAttribute("aria-pressed", String(showHistory));
  projectionsToggle.setAttribute("aria-selected", String(!showHistory));
  historyToggle.setAttribute("aria-selected", String(showHistory));
  if (showHistory !== wasHistoryActive && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const enteringView = showHistory ? historyView : projectionsView;
    const direction = showHistory ? 1 : -1;
    enteringView.animate(
      [
        { opacity: 0.75, transform: `translateX(${direction * 28}px)` },
        { opacity: 1, transform: "translateX(0)" },
      ],
      { duration: 220, easing: "ease-out" },
    );
  }
  if (showHistory) {
    chart?.resize();
    loadCounts(!successfulWeekKey);
  }
}

projectionsToggle.addEventListener("click", () => switchView(false));
historyToggle.addEventListener("click", () => switchView(true));

const views = document.querySelector("main");
let touchStart;

views.addEventListener(
  "touchstart",
  (event) => {
    if (event.touches.length !== 1) {
      touchStart = null;
      return;
    }
    touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
  },
  { passive: true },
);

views.addEventListener(
  "touchend",
  (event) => {
    if (!touchStart || event.changedTouches.length !== 1) return;
    const deltaX = event.changedTouches[0].clientX - touchStart.x;
    const deltaY = event.changedTouches[0].clientY - touchStart.y;
    touchStart = null;

    // Ignore taps, vertical scrolling, and swipes outside narrow/mobile layouts.
    if (
      window.matchMedia("(min-width: 48rem)").matches ||
      Math.abs(deltaX) < 60 ||
      Math.abs(deltaX) < Math.abs(deltaY) * 1.25
    )
      return;
    switchView(deltaX < 0);
  },
  { passive: true },
);

views.addEventListener(
  "touchcancel",
  () => {
    touchStart = null;
  },
  { passive: true },
);
