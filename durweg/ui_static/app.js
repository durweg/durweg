// Durweg management page. The start token lives only in this variable: it is taken from the
// start link once, removed from the address bar, and never stored (plan UI-R-008).
"use strict";
const token = (() => {
  const params = new URLSearchParams(location.search);
  const t = params.get("t");
  if (location.search) history.replaceState(null, "", location.pathname);
  return t || "";
})();

function show(id, text) { document.getElementById(id).textContent = text; }   // text only, never HTML

async function read(path) {
  const r = await fetch(path, { credentials: "omit", cache: "no-store" });
  return r.json();
}

async function write(path, body) {
  const r = await fetch(path, {
    method: "POST", credentials: "omit", cache: "no-store",
    headers: { "Content-Type": "application/json", "X-Durweg-Token": token },
    body: JSON.stringify(body || {}),
  });
  return r.json();
}

document.addEventListener("DOMContentLoaded", async () => {
  const noop = document.getElementById("noop");
  if (!token) {
    document.getElementById("notoken").hidden = false;
    noop.disabled = true;
  }
  try {
    const v = await read("/api/ping");
    show("version", v.ok ? "v" + v.version : "");
  } catch (e) { show("out", "The page service is not reachable: " + e); }
  noop.addEventListener("click", async () => {
    noop.disabled = true;
    try {
      const r = await write("/api/noop", {});
      show("out", r.ok ? "OK: " + r.done : "Refused: " + r.error);
    } catch (e) { show("out", "Failed: " + e); }
    noop.disabled = !token;
  });
});
