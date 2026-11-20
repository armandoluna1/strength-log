"use strict";
const el = id => document.getElementById(id);
let sets = [];
let editing = null;
let busy = false;

function today() {
  const d = new Date();
  return [d.getFullYear(), String(d.getMonth()+1).padStart(2,"0"), String(d.getDate()).padStart(2,"0")].join("-");
}

async function request(path, method = "GET", body) {
  const response = await fetch(path, {
    method, headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}

function resetForm() {
  editing = null;
  el("entry").reset();
  el("day").value = today();
  el("cancel").hidden = true;
  el("formTitle").textContent = "Log a set";
  el("save").textContent = "Save set";
}

function action(text, handler) {
  const button = document.createElement("button");
  button.textContent = text;
  button.onclick = handler;
  return button;
}

function render() {
  el("sets").replaceChildren();
  const visible = sets.filter(s => !el("filter").value || s.day === el("filter").value);
  const volume = visible.reduce((sum,s) => sum + s.weight * s.reps, 0);
  el("summary").textContent = visible.length ?
    visible.length + (visible.length === 1 ? " set" : " sets") + " · " + volume.toLocaleString() + " lb total volume" :
    (el("filter").value ? "No sets logged on this date." : "Your journal is empty. Log your first set.");
  for (const set of visible) {
    const row = document.createElement("li");
    row.className = "row";
    const detail = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = set.exercise;
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = set.day + " · " + set.reps + " reps × " + set.weight + " lb";
    detail.append(name, meta);
    const controls = document.createElement("div");
    const edit = action("Edit", () => {
      if (busy) return;
      editing = set.id;
      for (const field of ["day","exercise","reps","weight"]) el(field).value = set[field];
      el("formTitle").textContent = "Edit set";
      el("save").textContent = "Save changes";
      el("cancel").hidden = false;
      el("exercise").focus();
    });
    const remove = action("Delete", () => {
      if (busy || !confirm("Delete this set of " + set.exercise + "?")) return;
      mutate(async () => {
        await request("/api/sets/" + set.id, "DELETE");
        sets = sets.filter(s => s.id !== set.id);
        if (editing === set.id) resetForm();
      }, "Set deleted.");
    });
    remove.className = "remove";
    controls.append(edit, remove);
    row.append(detail, controls);
    el("sets").append(row);
  }
}

async function mutate(change, message) {
  if (busy) return;
  busy = true;
  el("save").disabled = true;
  try {
    await change();
    render();
    el("message").textContent = message;
  } catch (error) {
    el("message").textContent = error.message;
  } finally {
    busy = false;
    el("save").disabled = false;
  }
}

el("entry").onsubmit = event => {
  event.preventDefault();
  const set = {day: el("day").value, exercise: el("exercise").value.trim(),
    reps: el("reps").valueAsNumber, weight: el("weight").valueAsNumber};
  const id = editing;
  mutate(async () => {
    const result = await request(id === null ? "/api/sets" : "/api/sets/" + id, id === null ? "POST" : "PUT", set);
    sets = sets.filter(s => s.id !== result.id);
    sets.push({...set, id: result.id});
    sets.sort((a,b) => b.day.localeCompare(a.day) || b.id - a.id);
    if (el("filter").value) el("filter").value = set.day;
    resetForm();
  }, id === null ? "Set logged." : "Changes saved.");
};
el("cancel").onclick = () => { if (!busy) resetForm(); };
el("filter").oninput = render;
resetForm();
mutate(async () => { sets = await request("/api/sets"); }, "").then(() => {
  if (el("summary").textContent === "Loading sets…") el("summary").textContent = "Reload the page to retry loading your journal.";
});
