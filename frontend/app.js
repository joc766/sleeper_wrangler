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
const events = new EventSource("/events");
let hasResults = false;

events.onopen = () => {
  connection.textContent = "Connected · Live updates";
};

events.onerror = () => {
  connection.textContent = hasResults
    ? "Connection lost · Reconnecting… Showing last received results."
    : "Unable to connect · Retrying automatically…";
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
      cell.append(name, probability);
      row.append(rank, cell);
      rows.append(row);
    }

    users.replaceChildren(rows);
    const loserDecided = entries.length === 1 && entries[0][1] === 100;
    loserName.textContent = loserDecided ? entries[0][0] : "";
    loserLabel.textContent = loserDecided ? `Week ${update.week} Loser` : "";
    loserCard.hidden = !loserDecided;
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
    connection.textContent = "Connected · Live updates";
  } catch {
    notice.hidden = false;
    notice.textContent = hasResults
      ? "Could not read the latest update. Showing last received results."
      : "Could not read the latest update. Waiting for valid simulation results…";
  }
};
