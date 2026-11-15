import Chart from "chart.js/auto";

const notice = document.getElementById("chart-notice");
const results = document.getElementById("chart-results");
const users = document.getElementById("chart-users");
let chart;
let loading = false;
let successfulWeekKey = null;
let currentWeekKey = null;
let historyViewActive = false;
let trackerScrollTop = 0;
let heightMeasurementFrame;

function measureTrackerHeight() {
  const tracker = document.getElementById("users");
  const content = document.querySelector(".view-content");
  const rows = [...tracker.children].slice(0, 10);
  if (!rows.length) return;

  // Measure a collapsed copy even when Tracker is hidden or players are expanded.
  const styles = getComputedStyle(content);
  const availableWidth = content.clientWidth - parseFloat(styles.paddingLeft) - parseFloat(styles.paddingRight);
  const maxWidth = parseFloat(getComputedStyle(document.getElementById("projections-view")).maxWidth);
  const probe = tracker.cloneNode(false);
  probe.removeAttribute("id");
  probe.classList.add("tracker-height-probe");
  probe.style.width = `${Math.min(availableWidth, maxWidth || availableWidth)}px`;
  probe.setAttribute("aria-hidden", "true");
  for (const row of rows) {
    const copy = row.cloneNode(true);
    copy.querySelector(".active-player-list")?.remove();
    copy.removeAttribute("id");
    for (const element of copy.querySelectorAll("[id]")) element.removeAttribute("id");
    probe.append(copy);
  }
  document.body.append(probe);
  // The probe contains exactly the visible ten-row table (or fewer if the
  // tracker has fewer managers), including the leaderboard's outer border.
  const targetHeight = probe.getBoundingClientRect().height;
  content.style.setProperty("--tracker-table-height", `${Math.ceil(targetHeight)}px`);
  probe.remove();
}

function scheduleTrackerMeasurement() {
  cancelAnimationFrame(heightMeasurementFrame);
  heightMeasurementFrame = requestAnimationFrame(measureTrackerHeight);
}

function chartTheme() {
  const styles = getComputedStyle(document.documentElement);
  return {
    text: styles.getPropertyValue("--text-strong").trim(),
    muted: styles.getPropertyValue("--text-muted").trim(),
    grid: styles.getPropertyValue("--divider").trim(),
    bars: Array.from({ length: 6 }, (_, index) =>
      styles.getPropertyValue(`--chart-bar-${index + 1}`).trim()),
  };
}

function refreshChartTheme() {
  if (!chart) return;
  const theme = chartTheme();
  chart.options.color = theme.text;
  chart.options.scales.x.ticks.color = theme.muted;
  chart.options.scales.x.grid.color = theme.grid;
  chart.options.scales.x.title.color = theme.muted;
  chart.options.scales.y.ticks.color = theme.text;
  chart.options.plugins.legend.labels.color = theme.text;
  chart.data.datasets.forEach((dataset, index) => {
    dataset.backgroundColor = theme.bars[index % theme.bars.length];
  });
  // Chart.js 4.4 keeps shared bar colors in "none" mode. Normal updates refresh
  // those colors; animation is already disabled in the chart configuration.
  chart.update();
}

let themeRefreshFrame;
function scheduleChartThemeRefresh() {
  cancelAnimationFrame(themeRefreshFrame);
  themeRefreshFrame = requestAnimationFrame(refreshChartTheme);
}

document.addEventListener("theme-change", scheduleChartThemeRefresh);
window.addEventListener("pageshow", scheduleChartThemeRefresh);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) scheduleChartThemeRefresh();
});

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
    const colors = chartTheme().bars;
    const rows = document.createDocumentFragment();
    for (const [username, player] of entries) {
      const row = document.createElement("li");
      row.textContent = `${username}: ${player.total} total losses. ${orderedSeasons.map((season) => `${season}: ${player.seasons.get(season) ?? 0} losses${player.weeks.has(season) ? ` (weeks ${player.weeks.get(season).join(", ")})` : ""}`).join("; ")}.`;
      rows.append(row);
    }
    users.replaceChildren(rows);
    // summary.textContent = `${records.length} recorded losing ${records.length === 1 ? "week" : "weeks"} · ${entries.length} ${entries.length === 1 ? "manager" : "managers"}`;
    const canvas = document.getElementById("losses-chart");
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
        color: chartTheme().text,
        font: { family: getComputedStyle(document.body).fontFamily },
        animation: false,
        scales: {
          x: {
            stacked: true,
            beginAtZero: true,
            // max: Math.ceil(entries[0][1].total * 1.2),
            max: entries[0][1].total,
            ticks: { precision: 0, color: chartTheme().muted },
            grid: { color: chartTheme().grid },
            title: { display: true, text: "Total losses", color: chartTheme().muted },
          },
          y: {
            stacked: true,
            grid: { display: false },
            ticks: {
              color: chartTheme().text,
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
              color: chartTheme().text,
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
  scheduleTrackerMeasurement();
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
  const content = document.querySelector(".view-content");
  if (showHistory && !wasHistoryActive) trackerScrollTop = content.scrollTop;
  if (showHistory) measureTrackerHeight();
  historyViewActive = showHistory;
  const projectionsView = document.getElementById("projections-view");
  const historyView = document.getElementById("history-view");
  projectionsView.hidden = showHistory;
  historyView.hidden = !showHistory;
  content.classList.toggle("is-chart", showHistory);
  if (showHistory !== wasHistoryActive) {
    content.scrollTop = showHistory ? 0 : trackerScrollTop;
  }
  projectionsToggle.setAttribute("aria-pressed", String(!showHistory));
  historyToggle.setAttribute("aria-pressed", String(showHistory));
  projectionsToggle.setAttribute("aria-selected", String(!showHistory));
  historyToggle.setAttribute("aria-selected", String(showHistory));
  projectionsToggle.tabIndex = showHistory ? -1 : 0;
  historyToggle.tabIndex = showHistory ? 0 : -1;
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
    scheduleChartThemeRefresh();
    loadCounts(!successfulWeekKey);
  }
}

projectionsToggle.addEventListener("click", () => switchView(false));
historyToggle.addEventListener("click", () => switchView(true));

document.addEventListener("keydown", (event) => {
  if (document.querySelector("dialog[open]")) return;
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
  const target = event.target;
  if (
    target instanceof HTMLElement &&
    (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName))
  ) return;

  event.preventDefault();
  const toggle = event.key === "ArrowRight" ? historyToggle : projectionsToggle;
  if (document.activeElement === projectionsToggle || document.activeElement === historyToggle) {
    document.activeElement.blur();
  }
  toggle.click();
});

const views = document.querySelector("main");
new ResizeObserver(scheduleTrackerMeasurement).observe(document.querySelector(".view-content"));
document.fonts.ready.then(scheduleTrackerMeasurement);
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
