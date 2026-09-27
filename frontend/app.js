"use strict";

const connection = document.getElementById("connection");
const lastReceived = document.getElementById("last-received");
const notice = document.getElementById("notice");
const results = document.getElementById("results");
const users = document.getElementById("users");
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
    if (update === null || typeof update !== "object" || Array.isArray(update)) {
      throw new Error("Expected username-to-percentage data");
    }

    const entries = Object.entries(update);
    if (entries.some(([, value]) =>
      typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 100
    )) {
      throw new Error("Invalid percentage");
    }
    entries.sort(([nameA, a], [nameB, b]) => b - a || nameA.localeCompare(nameB));

    const rows = document.createDocumentFragment();
    for (const [username, value] of entries) {
      const row = document.createElement("tr");
      const name = document.createElement("th");
      name.scope = "row";
      name.textContent = username;

      const cell = document.createElement("td");
      const probability = document.createElement("div");
      probability.className = "probability";
      const percentage = document.createElement("span");
      percentage.className = "percentage";
      percentage.textContent = `${value.toFixed(2)}%`;

      const bar = document.createElement("progress");
      bar.max = 100;
      bar.value = value;
      bar.setAttribute("aria-label", `${username}: chance of lowest score`);
      bar.setAttribute("aria-valuetext", percentage.textContent);
      probability.append(percentage, bar);
      cell.append(probability);
      row.append(name, cell);
      rows.append(row);
    }

    users.replaceChildren(rows);
    hasResults = entries.length > 0;
    results.hidden = !hasResults;
    notice.hidden = hasResults;
    notice.textContent = hasResults ? "" : "No probabilities available yet. Waiting for the next simulation…";
    const now = new Date();
    lastReceived.dateTime = now.toISOString();
    lastReceived.textContent = now.toLocaleString();
    connection.textContent = "Connected · Live updates";
  } catch {
    notice.hidden = false;
    notice.textContent = hasResults
      ? "Could not read the latest update. Showing last received results."
      : "Could not read the latest update. Waiting for valid simulation results…";
  }
};
