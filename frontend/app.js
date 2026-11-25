"use strict";

import week10Fixture from "./fixtures/week-10-2026.json";
import week10LoserFixture from "./fixtures/week-10-loser.json";
import week10PregameFixture from "./fixtures/week-10-pregame.json";

const connection = document.getElementById("connection");
const connectionMeta = document.querySelector(".connection-meta");
const connectionTooltip = document.getElementById("connection-tooltip");
const weekNumber = document.getElementById("week-number");
const notice = document.getElementById("notice");
const results = document.getElementById("results");
const users = document.getElementById("users");
const trackerScroller = document.querySelector(".view-content");
const scrollToTop = document.getElementById("scroll-to-top");
const trackerView = document.getElementById("projections-view");
const updateScrollToTop = () => {
  scrollToTop.hidden = trackerView.hidden || trackerScroller.scrollTop < 100;
};
trackerScroller.addEventListener("scroll", updateScrollToTop, { passive: true });
new MutationObserver(updateScrollToTop).observe(trackerView, {
  attributes: true, attributeFilter: ["hidden"],
});
scrollToTop.addEventListener("click", () => {
  trackerScroller.focus({ preventScroll: true });
  trackerScroller.scrollTo({
    top: 0,
    behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
  });
});
updateScrollToTop();
let trackerTouchY = null;

trackerScroller.addEventListener("touchstart", (event) => {
  trackerTouchY = event.touches.length === 1 && event.target.closest("#projections-view")
    ? event.touches[0].clientY
    : null;
}, { passive: true });

trackerScroller.addEventListener("touchmove", (event) => {
  if (trackerTouchY === null || event.touches.length !== 1) {
    trackerTouchY = null;
    return;
  }
  const nextY = event.touches[0].clientY;
  const pullingDown = nextY > trackerTouchY;
  trackerTouchY = nextY;
  if (pullingDown && trackerScroller.scrollTop <= 0 && event.cancelable) {
    event.preventDefault();
  }
}, { passive: false });

for (const eventName of ["touchend", "touchcancel"]) {
  trackerScroller.addEventListener(eventName, () => {
    trackerTouchY = null;
  }, { passive: true });
}

const loserCard = document.getElementById("loser-card");
const loserName = document.getElementById("loser-name");
const loserLabel = document.getElementById("loser-label");
const loserHistory = document.getElementById("loser-history");
const loserLossNumber = document.getElementById("loser-loss-number");
const loserLastLoss = document.getElementById("loser-last-loss");
let historyKey = null;
let historyRequest;
let latestUpdateTime = "";
const fixtures = { "week-10-2026": week10Fixture , "week-10-loser": week10LoserFixture, "week-10-pregame": week10PregameFixture };
const searchParams = new URLSearchParams(location.search);
const fixtureParam = searchParams.get("fixture");
const mockMode = import.meta.env.DEV && (searchParams.get("mock") === "1" || fixtureParam !== null);
const selectedFixture = fixtures[fixtureParam] ? fixtureParam : Object.keys(fixtures)[0];
const events = mockMode ? null : new EventSource("/events");
let hasResults = false;
let activeStarters = {};
let gameCompletion = {};
let activePlayerWeek = null;
const playerInfo = new Map();
const requestedPlayerInfo = new Set();
const expandedRows = new Set();
const positionOrder = ["QB", "RB", "WR", "TE", "K", "DEF"];

function renderActivePlayers() {
  for (const row of users.querySelectorAll(".manager-card")) {
    const username = row.dataset.username;
    const players = activeStarters[username] ?? {};
    const playerIDs = Object.keys(players);
    const active = playerIDs.length > 0;
    row.classList.toggle("is-expandable", active);
    row.tabIndex = active ? 0 : -1;
    const live = row.querySelector(".manager-live");
    live.hidden = !active;
    live.textContent = "LIVE";
    live.setAttribute("aria-label", `${playerIDs.length} ${playerIDs.length === 1 ? "player" : "players"} playing live. Activate row to toggle players.`);
    row.setAttribute("aria-expanded", String(active && expandedRows.has(username)));
    const list = row.querySelector(".active-player-list");
    list.replaceChildren();
    if (!active || !expandedRows.has(username)) {
      list.hidden = true;
      continue;
    }

    const knownPlayers = playerIDs
      .filter((id) => playerInfo.has(id))
      .map((id) => ({ id, ...playerInfo.get(id) }))
      .sort((a, b) => {
        const positionDiff = (positionOrder.indexOf(a.position) < 0 ? positionOrder.length : positionOrder.indexOf(a.position))
          - (positionOrder.indexOf(b.position) < 0 ? positionOrder.length : positionOrder.indexOf(b.position));
        return positionDiff || a.full_name.localeCompare(b.full_name);
      });

    for (const player of knownPlayers) {
      const item = document.createElement("li");
      item.className = "active-player";
      item.dataset.position = player.position;
      const thumbnail = document.createElement("img");
      thumbnail.className = "active-player-thumbnail";
      thumbnail.src = player.position === "DEF"
        ? `https://sleepercdn.com/images/team_logos/nfl/${encodeURIComponent(player.id.toLowerCase())}.png`
        : `https://sleepercdn.com/content/nfl/players/thumb/${encodeURIComponent(player.id)}.jpg`;
      thumbnail.alt = "";
      thumbnail.loading = "lazy";

      const details = document.createElement("div");
      details.className = "active-player-details";
      const name = document.createElement("span");
      name.className = "active-player-name";
      name.textContent = player.full_name;
      const meta = document.createElement("div");
      meta.className = "active-player-meta";
      const position = document.createElement("span");
      position.className = "active-player-position";
      position.textContent = player.position;
      const separator = document.createElement("span");
      separator.className = "active-player-separator";
      separator.textContent = "·";
      const team = document.createElement("span");
      team.className = "active-player-team";
      team.textContent = player.team;
      meta.append(position, separator, team);
      details.append(name, meta);
      const points = document.createElement("span");
      points.className = "active-player-points";
      const currentPoints = players[player.id];
      points.textContent = typeof currentPoints === "number" && Number.isFinite(currentPoints)
        ? currentPoints.toFixed(2)
        : "—";
      const progress = document.createElement("div");
      progress.className = "active-player-progress";
      progress.setAttribute("role", "progressbar");
      progress.setAttribute("aria-label", `${player.full_name} game progress`);
      const completion = gameCompletion[player.team];
      const completionPercent = typeof completion === "number" && Number.isFinite(completion)
        ? Math.min(100, Math.max(0, completion * 100))
        : null;
      progress.setAttribute("aria-valuemin", "0");
      progress.setAttribute("aria-valuemax", "100");
      if (completionPercent === null) {
        progress.setAttribute("aria-valuetext", "Game progress unavailable");
      } else {
        progress.setAttribute("aria-valuenow", String(Math.round(completionPercent)));
        progress.setAttribute("aria-valuetext", `${Math.round(completionPercent)}% complete`);
      }
      const progressFill = document.createElement("span");
      progressFill.className = "active-player-progress-fill";
      progressFill.style.width = `${completionPercent ?? 0}%`;
      progress.append(progressFill);
      item.append(thumbnail, details, points, progress);
      list.append(item);
    }
    list.hidden = false;
  }

}

async function fetchActivePlayerInfo(ids) {
  if (mockMode) return;
  const missing = [...new Set(ids)].filter((id) => !playerInfo.has(id) && !requestedPlayerInfo.has(id));
  if (!missing.length) return;
  missing.forEach((id) => requestedPlayerInfo.add(id));
  const params = new URLSearchParams();
  missing.forEach((id) => params.append("player_id", id));
  const week = activePlayerWeek;
  try {
    const response = await fetch(`/playerInfo?${params}`);
    if (!response.ok) throw new Error("Could not fetch player info");
    const result = await response.json();
    if (week !== activePlayerWeek || !result || typeof result !== "object" || Array.isArray(result)) return;
    for (const [id, info] of Object.entries(result)) {
      if (info && typeof info.full_name === "string" && typeof info.position === "string" && typeof info.team === "string") {
        playerInfo.set(id, info);
      }
    }
  } catch (error) {
    console.error(error);
  } finally {
    if (week === activePlayerWeek) renderActivePlayers();
  }
}

users.addEventListener("click", (event) => {
  const row = event.target.closest(".manager-card");
  if (!row || !event.target.closest(".manager-main") || !row.classList.contains("is-expandable")) return;
  const username = row.dataset.username;
  expandedRows.has(username) ? expandedRows.delete(username) : expandedRows.add(username);
  renderActivePlayers();
});

users.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  const row = event.target.closest(".manager-card");
  if (!row || !row.classList.contains("is-expandable")) return;
  event.preventDefault();
  row.querySelector(".manager-main").click();
});

const lineupNote = document.createElement("p");
lineupNote.id = "lineup-note";
lineupNote.className = "lineup-note";
const lineupNoteBadge = document.createElement("span");
lineupNoteBadge.className = "incomplete-warning";
lineupNoteBadge.textContent = "0 proj";
const lineupNoteExplanation = document.createElement("span");
lineupNoteExplanation.textContent = "Lineup contains players projected for 0.0 points.";
lineupNote.append(lineupNoteBadge, lineupNoteExplanation);
lineupNote.hidden = true;
users.after(lineupNote);

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

function setConnectionState(connected) {
  connection.classList.toggle("is-connected", connected);
  connection.classList.toggle("is-reconnecting", !connected);
  const label = mockMode ? "Mock data preview" : connected ? "Connected" : "Reconnecting to live updates";
  connection.setAttribute("aria-label", latestUpdateTime
    ? `${label}. Latest update ${latestUpdateTime}`
    : label);
  connectionTooltip.textContent = latestUpdateTime
    ? `${label} · Latest update ${latestUpdateTime}`
    : label;
}

if (events) {
  events.onopen = () => {
    setConnectionState(true);
  };

  events.onerror = () => {
    setConnectionState(false);
  };
}

connection.addEventListener("click", () => {
  const isOpen = connectionMeta.classList.toggle("is-open");
  connection.setAttribute("aria-expanded", String(isOpen));
});

document.addEventListener("click", (event) => {
  if (connectionMeta.contains(event.target)) return;
  connectionMeta.classList.remove("is-open");
  connection.setAttribute("aria-expanded", "false");
});

connection.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  connectionMeta.classList.remove("is-open");
  connection.setAttribute("aria-expanded", "false");
  connection.blur();
});

const handleEventMessage = (event) => {
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
    if (typeof update.is_complete !== "boolean") {
      throw new Error("Invalid game completion status");
    }
    if (!Number.isInteger(update.week) || update.week < 1) {
      throw new Error("Invalid week number");
    }
    const playerWeek = `${update.season ?? ""}-${update.week}`;
    if (playerWeek !== activePlayerWeek) {
      activePlayerWeek = playerWeek;
      playerInfo.clear();
      requestedPlayerInfo.clear();
      expandedRows.clear();
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
    const incomplete = update.incomplete ?? {};
    const nextActiveStarters = update.active_starters ?? {};
    const nextGameCompletion = update.game_completion ?? {};
    const yetToPlay = update.yet_to_play ?? {};
    if (typeof yetToPlay !== "object" || yetToPlay === null || Array.isArray(yetToPlay)
      || Object.values(yetToPlay).some((count) => !Number.isInteger(count) || count < 0)) {
      throw new Error("Invalid yet-to-play counts");
    }
    if (
      avatars === null || typeof avatars !== "object" || Array.isArray(avatars) ||
      currentScores === null || typeof currentScores !== "object" || Array.isArray(currentScores) ||
      weeklyProjections === null || typeof weeklyProjections !== "object" || Array.isArray(weeklyProjections) ||
      incomplete === null || typeof incomplete !== "object" || Array.isArray(incomplete) ||
      nextActiveStarters === null || typeof nextActiveStarters !== "object" || Array.isArray(nextActiveStarters) ||
      nextGameCompletion === null || typeof nextGameCompletion !== "object" || Array.isArray(nextGameCompletion)
    ) {
      throw new Error("Invalid user metadata");
    }
    if (Object.values(nextActiveStarters).some((players) => players === null || typeof players !== "object" || Array.isArray(players))) {
      throw new Error("Invalid active player metadata");
    }
    activeStarters = nextActiveStarters;
    if (Object.values(nextGameCompletion).some((value) => typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1)) {
      throw new Error("Invalid game completion metadata");
    }
    gameCompletion = nextGameCompletion;
    fetchActivePlayerInfo(Object.values(activeStarters).flatMap((players) => Object.keys(players)));
    if (Object.values(incomplete).some((value) => typeof value !== "boolean")) {
      throw new Error("Invalid incomplete lineup metadata");
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
    for (const [username, value] of entries) {
      const row = document.createElement("li");
      row.className = "manager-card";
      row.dataset.username = username;
      row.tabIndex = 0;
      const managerMain = document.createElement("div");
      managerMain.className = "manager-main";
      const live = document.createElement("span");
      live.className = "manager-live";
      live.textContent = "LIVE";
      live.hidden = true;
      live.setAttribute("aria-label", "Live players. Activate row to toggle players.");
      const avatarSlot = document.createElement("span");
      avatarSlot.className = "manager-avatar-slot";
      avatarSlot.textContent = username.slice(0, 1).toUpperCase();
      avatarSlot.setAttribute("aria-hidden", "true");
      const name = document.createElement("h3");
      name.className = "manager-name";
      name.textContent = username;
      name.append(live);

      if (incomplete[username] === true) {
        const warning = document.createElement("span");
        warning.className = "incomplete-warning";
        warning.textContent = "0 proj";
        warning.setAttribute("aria-describedby", lineupNote.id);
        name.append(warning);
      }

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
        avatar.addEventListener("error", () => {
          avatarSlot.textContent = username.slice(0, 1).toUpperCase();
        }, { once: true });
        avatarSlot.replaceChildren(avatar);
      }
      identity.append(avatarSlot);

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
      const projectionValue = document.createElement("span");
      projectionValue.className = "projection-value";
      projectionValue.textContent = `${formattedProjection} proj`;
      const currentValue = document.createElement("span");
      currentValue.className = "current-value";
      currentValue.textContent = `${formattedCurrentScore} pts`;
      projectedPoints.append(projectionValue, currentValue);
      projectedPoints.title = `${formattedCurrentScore} current points · ${formattedProjection} projected points`;

      const cell = document.createElement("div");
      cell.className = "manager-detail";
      const probability = document.createElement("div");
      probability.className = "probability";
      const percentage = document.createElement("span");
      percentage.className = "percentage";
      percentage.textContent = value.toFixed() === "0" ? "<1%" : `${value.toFixed()}%`;

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
      const remaining = document.createElement("span");
      remaining.className = "yet-to-play";
      const remainingCount = yetToPlay[username] ?? 0;
      remaining.textContent = remainingCount > 0 ? `Yet to play (${remainingCount})` : "";
      const remainingPositions = update.yet_to_play_positions?.[username];
      if (remainingCount > 0 && Array.isArray(remainingPositions)
        && remainingPositions.length === remainingCount
        && remainingPositions.every((position) => typeof position === "string")) {
        const positions = [...remainingPositions]
          .sort((a, b) => {
            const rank = (position) => {
              const index = positionOrder.indexOf(position);
              return index < 0 ? positionOrder.length : index;
            };
            return rank(a) - rank(b) || a.localeCompare(b);
          })
          .join(", ");
        remaining.textContent += `: ${positions}`;
      }
      const managerHeader = document.createElement("div");
      managerHeader.className = "manager-header";
      identity.append(percentage);
      managerHeader.append(identity, projectedPoints);
      probability.append(managerHeader, bar);
      cell.append(probability, name);
      if (remainingCount > 0) cell.append(remaining);
      managerMain.append(cell);
      const surface = document.createElement("div");
      surface.className = "manager-surface";
      surface.append(managerMain);
      const playerList = document.createElement("ul");
      playerList.className = "active-player-list";
      playerList.hidden = true;
      surface.append(playerList);
      row.append(surface);
      rows.append(row);
    }

    users.replaceChildren(rows);
    renderActivePlayers();
    const loserDecided = entries.length > 0 && entries[0][1] === 100
      && entries.slice(1).every(([, probability]) => probability === 0);
    loserName.textContent = loserDecided ? entries[0][0] : "";
    loserLabel.textContent = loserDecided ? `Week ${update.week} Loser` : "";
    loserCard.hidden = !loserDecided;
    connectionMeta.hidden = loserDecided;
    updateLoserHistory(loserDecided ? entries[0][0] : null, update.season, update.week);
    users.hidden = loserDecided;
    lineupNote.hidden = loserDecided || !entries.some(([username]) => incomplete[username] === true);
    weekNumber.textContent = `Week ${update.week}`;
    weekNumber.hidden = loserDecided;
    latestUpdateTime = created.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    hasResults = entries.length > 0;
    window.latestProjectionUpdate = update;
    document.dispatchEvent(new CustomEvent("projection-update", { detail: update }));
    results.hidden = !hasResults;
    notice.hidden = hasResults;
    notice.textContent = hasResults
      ? ""
      : "No probabilities available yet. Waiting for the next simulation…";
    setConnectionState(true);
  } catch {
    notice.hidden = false;
    notice.textContent = hasResults
      ? "Could not read the latest update. Showing last received results."
      : "Could not read the latest update. Waiting for valid simulation results…";
  }
};

if (mockMode) {
  const loadFixture = (key) => {
    const fixture = fixtures[key];
    playerInfo.clear();
    requestedPlayerInfo.clear();
    expandedRows.clear();
    activePlayerWeek = `${fixture.update.season}-${fixture.update.week}`;
    for (const [id, info] of Object.entries(fixture.player_info)) {
      playerInfo.set(id, info);
    }
    handleEventMessage({ data: JSON.stringify(fixture.update) });
  };
  loadFixture(selectedFixture);
} else {
  events.onmessage = handleEventMessage;
}
