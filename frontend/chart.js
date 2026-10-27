"use strict";

const notice = document.getElementById("chart-notice");
const results = document.getElementById("chart-results");
const users = document.getElementById("chart-users");
const summary = document.getElementById("chart-summary");
let chart;
let loading = false;

async function loadCounts() {
  if (loading) return;
  loading = true;
  try {
    const response = await fetch("/loserCounts");
    if (!response.ok) throw new Error("Could not fetch loser counts");
    const records = (await response.json()) ?? [];
    if (!Array.isArray(records)) throw new Error("Invalid loser records");

    const counts = new Map();
    const seasons = new Set();
    for (const record of records) {
      if (!record || typeof record.Username !== "string" || !record.Username.trim()) {
        throw new Error("Invalid manager name");
      }
      const season = String(record.Season ?? "");
      if (!/^\d{4}$/.test(season)) throw new Error("Invalid season");
      seasons.add(season);
      const player = counts.get(record.Username) ?? { total: 0, seasons: new Map(), weeks: new Map() };
      player.total += 1;
      player.seasons.set(season, (player.seasons.get(season) ?? 0) + 1);
      const weeks = player.weeks.get(season) ?? [];
      weeks.push(record.Week);
      player.weeks.set(season, weeks);
      counts.set(record.Username, player);
    }
    const entries = [...counts].sort(
      ([nameA, a], [nameB, b]) => b.total - a.total || nameA.localeCompare(nameB),
    );
    if (!entries.length) {
      notice.textContent = "No loser records available yet.";
      return;
    }

    const orderedSeasons = [...seasons].sort((a, b) => Number(a) - Number(b));
    const latestSeason = orderedSeasons.at(-1);
    const latestWeek = Math.max(...records.filter((record) => String(record.Season) === latestSeason).map((record) => record.Week));
    document.getElementById("chart-heading").textContent = `🍺 Loser Stats · Thru ${latestSeason}, Week ${latestWeek}`;
    for (const [, player] of entries) {
      for (const weeks of player.weeks.values()) weeks.sort((a, b) => a - b);
    }
    const colors = ["#243f65", "#6685a8", "#e99b24", "#ffe096", "#367f78", "#9a719c"];
    const rows = document.createDocumentFragment();
    for (const [username, player] of entries) {
      const row = document.createElement("li");
      row.textContent = `${username}: ${player.total} total losses. ${orderedSeasons.map((season) => `${season}: ${player.seasons.get(season) ?? 0} losses${player.weeks.has(season) ? ` (weeks ${player.weeks.get(season).join(", ")})` : ""}`).join("; ")}.`;
      rows.append(row);
    }
    users.replaceChildren(rows);
    // summary.textContent = `${records.length} recorded losing ${records.length === 1 ? "week" : "weeks"} · ${entries.length} ${entries.length === 1 ? "manager" : "managers"}`;
    notice.hidden = true;
    results.hidden = false;
    const canvas = document.getElementById("losses-chart");
    canvas.parentElement.style.height = `${Math.max(320, entries.length * 48 + 100)}px`;
    chart?.destroy();
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
        animation: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? false : undefined,
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
          y: { stacked: true, grid: { display: false }, ticks: { color: "#182b45", autoSkip: false } },
        },
        plugins: {
          legend: { position: "bottom", onClick: () => {} },
          tooltip: {
            callbacks: {
              title: ([context]) => `${entries[context.dataIndex][0]} — ${context.dataset.label}`,
              label: (context) => `${context.parsed.x} ${context.parsed.x === 1 ? "loss" : "losses"}`,
              afterLabel: (context) => {
                const weeks = entries[context.dataIndex][1].weeks.get(context.dataset.label) ?? [];
                return `${weeks.length === 1 ? "Week" : "Weeks"} ${weeks.join(", ")}`;
              },
            },
          },
        },
      },
    });
  } catch {
    results.hidden = true;
    notice.hidden = false;
    notice.textContent = "Could not load loser counts. Refresh the page to try again.";
  } finally {
    loading = false;
  }
}

const projectionsToggle = document.getElementById("projections-toggle");
const historyToggle = document.getElementById("history-toggle");

function switchView(showHistory) {
  document.getElementById("projections-view").hidden = showHistory;
  document.getElementById("history-view").hidden = !showHistory;
  document.querySelector("main").classList.toggle("counts-chart", showHistory);
  projectionsToggle.setAttribute("aria-pressed", String(!showHistory));
  historyToggle.setAttribute("aria-pressed", String(showHistory));
  if (showHistory) {
    chart?.resize();
    loadCounts();
  }
}

projectionsToggle.addEventListener("click", () => switchView(false));
historyToggle.addEventListener("click", () => switchView(true));
