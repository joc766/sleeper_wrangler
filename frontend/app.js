"use strict";

const connection = document.getElementById("connection");
const createdAt = document.getElementById("created-at");
const weekNumber = document.getElementById("week-number");
const notice = document.getElementById("notice");
const results = document.getElementById("results");
const users = document.getElementById("users");
const loserCard = document.getElementById("loser-card");
const loserName = document.getElementById("loser-name");
const loserLabel = document.getElementById("loser-label");
const loserHistory = document.getElementById("loser-history");
const loserLossNumber = document.getElementById("loser-loss-number");
const loserLastLoss = document.getElementById("loser-last-loss");
let historyKey = null;
let historyRequest;
const events = new EventSource("/events");
let hasResults = false;

function lossHistory(records, username, season, week) {
  const previous = new Map();
  for (const record of records) {
    if (record.Username !== username) continue;
    const year = Number(record.Season);
    if (!Number.isInteger(year) || !Number.isInteger(record.Week)) continue;
    if (year < season || (year === season && record.Week < week)) {
      previous.set(`${year}-${record.Week}`, { season: year, week: record.Week });
    }
  }
  const losses = [...previous.values()].sort((a, b) => b.season - a.season || b.week - a.week);
  const count = losses.length + 1;
  const suffix = count % 100 >= 11 && count % 100 <= 13
    ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[count % 10] ?? "th");
  return {
    number: count === 1 ? "First loss" : `${count}${suffix} loss`,
    last: losses.length ? `Last loss: Week ${losses[0].week}, ${losses[0].season}` : "",
  };
}

async function updateLoserHistory(username, season, week) {
  const key = username && /^\d{4}$/.test(String(season))
    ? JSON.stringify([username, season, week]) : null;
  if (key === historyKey) return;
  historyRequest?.abort();
  historyKey = key;
  loserHistory.hidden = true;
  if (!key) return;
  const request = new AbortController();
  historyRequest = request;
  try {
    const response = await fetch("/loserCounts", { signal: request.signal });
    if (!response.ok) throw new Error("Could not fetch loss history");
    const records = (await response.json()) ?? [];
    if (!Array.isArray(records)) throw new Error("Invalid loss history");
    const history = lossHistory(records, username, Number(season), week);
    if (request.signal.aborted || historyKey !== key) return;
    loserLossNumber.textContent = history.number;
    loserLastLoss.textContent = history.last;
    loserLastLoss.hidden = !history.last;
    loserHistory.hidden = false;
  } catch {
    if (!request.signal.aborted && historyKey === key) historyKey = null;
  }
}

function showConnectionSpinner() {
  const spinner = document.createElement("span");
  spinner.className = "connection-spinner";
  spinner.setAttribute("aria-hidden", "true");
  connection.replaceChildren(spinner);
}

events.onopen = () => {
  connection.textContent = "Connected";
  connection.setAttribute("aria-label", "Connected · Live updates");
  connection.title = "Connected · Live updates";
};

events.onerror = () => {
  showConnectionSpinner();
  connection.setAttribute("aria-label", "Reconnecting to live updates");
  connection.title = "Reconnecting to live updates";
};

events.onmessage = (event) => {
  try {
    const update = JSON.parse(event.data);
    if (
      update === null ||
      typeof update !== "object" ||
      Array.isArray(update)
    ) {
      throw new Error("Expected projection response");
    }

    if (
      update.projections === null ||
      typeof update.projections !== "object" ||
      Array.isArray(update.projections)
    ) {
      throw new Error("Expected username-to-percentage data");
    }
    if (typeof update.created_at !== "string" || !update.created_at.trim()) {
      throw new Error("Missing creation time");
    }
    if (!Number.isInteger(update.week) || update.week < 1) {
      throw new Error("Invalid week number");
    }
    // SQLite CURRENT_TIMESTAMP is UTC, but does not include a timezone.
    const timestamp = update.created_at.trim();
    const normalizedTimestamp =
      /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d+)?$/.test(timestamp)
        ? `${timestamp.replace(" ", "T")}Z`
        : timestamp;
    const created = new Date(normalizedTimestamp);
    if (Number.isNaN(created.getTime())) {
      throw new Error("Invalid creation time");
    }

    const entries = Object.entries(update.projections);
    const avatars = update.avatars ?? {};
    const currentScores = update.current_scores ?? {};
    const weeklyProjections = update.weekly_projections ?? {};
    if (
      avatars === null || typeof avatars !== "object" || Array.isArray(avatars) ||
      currentScores === null || typeof currentScores !== "object" || Array.isArray(currentScores) ||
      weeklyProjections === null || typeof weeklyProjections !== "object" || Array.isArray(weeklyProjections)
    ) {
      throw new Error("Invalid user metadata");
    }
    if (
      entries.some(
        ([, value]) =>
          typeof value !== "number" ||
          !Number.isFinite(value) ||
          value < 0 ||
          value > 100,
      )
    ) {
      throw new Error("Invalid percentage");
    }
    entries.sort(
      ([nameA, a], [nameB, b]) => b - a || nameA.localeCompare(nameB),
    );

    const rows = document.createDocumentFragment();
    for (const [index, [username, value]] of entries.entries()) {
      const row = document.createElement("li");
      row.className = "manager-card";
      const rank = document.createElement("span");
      rank.className = "rank";
      rank.textContent = String(index + 1).padStart(2, "0");
      rank.setAttribute("aria-hidden", "true");
      const name = document.createElement("h3");
      name.className = "manager-name";
      name.textContent = username;

      const identity = document.createElement("div");
      identity.className = "manager-identity";
      const avatarValue = avatars[username];
      if (typeof avatarValue === "string" && avatarValue.trim()) {
        const avatar = document.createElement("img");
        avatar.className = "manager-avatar";
        const avatarIdOrUrl = avatarValue.trim();
        avatar.src = /^https?:\/\//i.test(avatarIdOrUrl)
          ? avatarIdOrUrl
          : `https://sleepercdn.com/avatars/${encodeURIComponent(avatarIdOrUrl)}`;
        avatar.alt = "";
        avatar.loading = "lazy";
        avatar.addEventListener("error", () => avatar.remove(), { once: true });
        identity.append(avatar);
      }
      identity.append(name);

      const projection = weeklyProjections[username];
      if (projection !== undefined && (typeof projection !== "number" || !Number.isFinite(projection))) {
        throw new Error("Invalid weekly projection");
      }
      const currentScore = currentScores[username];
      if (currentScore !== undefined && (typeof currentScore !== "number" || !Number.isFinite(currentScore))) {
        throw new Error("Invalid current score");
      }
      const projectedPoints = document.createElement("span");
      projectedPoints.className = "projected-points";
      const formattedProjection =
        typeof projection === "number"
          ? projection.toFixed(2).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1")
          : "—";
      const formattedCurrentScore =
        typeof currentScore === "number"
          ? currentScore.toFixed(2).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1")
          : "—";
      projectedPoints.textContent = `${formattedCurrentScore} pts · ${formattedProjection} proj`;
      projectedPoints.title = `${formattedCurrentScore} current points · ${formattedProjection} projected points`;

      const cell = document.createElement("div");
      cell.className = "manager-detail";
      const probability = document.createElement("div");
      probability.className = "probability";
      const percentage = document.createElement("span");
      percentage.className = "percentage";
      percentage.textContent = `${value.toFixed()}%`;

      const bar = document.createElement("div");
      bar.className = "bar-track";
      bar.setAttribute("aria-hidden", "true");
      const fill = document.createElement("div");
      fill.className = "bar-fill";
      fill.style.width = `${value}%`;
      bar.append(fill);
      const description = document.createElement("span");
      description.className = "visually-hidden";
      description.textContent = " chance of lowest score";
      percentage.append(description);
      probability.append(bar, percentage);
      const managerHeader = document.createElement("div");
      managerHeader.className = "manager-header";
      managerHeader.append(identity, projectedPoints);
      cell.append(managerHeader, probability);
      row.append(rank, cell);
      rows.append(row);
    }

    users.replaceChildren(rows);
    const loserDecided = entries.length > 0 && entries[0][1] === 100
      && entries.slice(1).every(([, probability]) => probability === 0);
    loserName.textContent = loserDecided ? entries[0][0] : "";
    loserLabel.textContent = loserDecided ? `Week ${update.week} Loser` : "";
    loserCard.hidden = !loserDecided;
    updateLoserHistory(loserDecided ? entries[0][0] : null, update.season, update.week);
    users.hidden = loserDecided;
    weekNumber.textContent = `Week ${update.week}`;
    weekNumber.hidden = loserDecided;
    createdAt.dateTime = created.toISOString();
    createdAt.textContent = created.toLocaleString();
    hasResults = entries.length > 0;
    results.hidden = !hasResults;
    notice.hidden = hasResults;
    notice.textContent = hasResults
      ? ""
      : "No probabilities available yet. Waiting for the next simulation…";
    connection.textContent = "Connected";
    connection.setAttribute("aria-label", "Connected · Live updates");
    connection.title = "Connected · Live updates";
  } catch {
    notice.hidden = false;
    notice.textContent = hasResults
      ? "Could not read the latest update. Showing last received results."
      : "Could not read the latest update. Waiting for valid simulation results…";
  }
};
