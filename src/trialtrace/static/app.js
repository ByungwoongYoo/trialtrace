const form = document.querySelector("#search-form");
const input = document.querySelector("#nct-id");
const statusBox = document.querySelector("#status");
const results = document.querySelector("#results");
const changedOnly = document.querySelector("#changed-only");
let currentTimeline = [];

const escapeHtml = (value) => String(value ?? "—").replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[character]));

function setStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
}

async function requestJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail?.message || "The request could not be completed.");
  return data;
}

function renderSummary(trial) {
  document.querySelector("#trial-title").textContent = trial.nct_id;
  const sourceLink = document.querySelector("#source-link");
  sourceLink.href = trial.source_url;
  const entries = [
    ["History versions", trial.history_versions],
    ["Derived transitions", trial.transition_count],
    ["First results", trial.first_results_date || "Unavailable"],
    ["Cohort", trial.group || "Unspecified"],
  ];
  document.querySelector("#summary-grid").innerHTML = entries.map(([term, value]) =>
    `<div><dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd></div>`
  ).join("");
}

function renderTimeline(items) {
  const visible = changedOnly.checked ? items.filter((item) => item.changes.length) : items;
  const timeline = document.querySelector("#timeline");
  if (!visible.length) {
    timeline.innerHTML = '<p class="hint">No transitions match this filter.</p>';
    return;
  }
  timeline.innerHTML = visible.map((item) => {
    const changes = item.changes.length
      ? `<ul class="change-list">${item.changes.map((change) => `
          <li><span class="change-field">${escapeHtml(change.field.replaceAll("_", " "))}</span>
          <span class="before">${escapeHtml(change.before)}</span><span class="arrow">→</span>
          <span class="after">${escapeHtml(change.after)}</span></li>`).join("")}</ul>`
      : '<p class="hint">No tracked field changed in this transition.</p>';
    const labels = item.module_labels.map((label) => `<span class="badge">${escapeHtml(label)}</span>`).join("");
    return `<article class="event ${item.first_results_posted_transition ? "first-results" : ""}">
      <div class="event__top"><h3>Version ${item.version}${item.first_results_posted_transition ? " · First posted results" : ""}</h3>
      <time>${escapeHtml(item.history_version_date || item.index_change_date || "Date unavailable")}</time></div>
      <div class="badges">${labels || '<span class="badge">No module label</span>'}</div>
      ${changes}
    </article>`;
  }).join("");
}

async function search(nctId) {
  const normalized = nctId.trim().toUpperCase();
  setStatus(`Loading ${normalized}…`);
  results.hidden = true;
  try {
    const [trial, timeline] = await Promise.all([
      requestJson(`/api/trials/${encodeURIComponent(normalized)}`),
      requestJson(`/api/trials/${encodeURIComponent(normalized)}/timeline`),
    ]);
    currentTimeline = timeline.items;
    renderSummary(trial);
    renderTimeline(currentTimeline);
    results.hidden = false;
    setStatus(`${timeline.count} transitions loaded from the frozen corpus.`);
  } catch (error) {
    currentTimeline = [];
    setStatus(error.message, true);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  search(input.value);
});
changedOnly.addEventListener("change", () => renderTimeline(currentTimeline));
