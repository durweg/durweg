// Durweg management page. The start token lives only in this variable: it is taken from the
// start link once, removed from the address bar, and never stored (plan UI-R-008).
// Everything from the server is shown as text (textContent), never as HTML (plan section 5).
"use strict";
const token = (() => {
  const t = new URLSearchParams(location.search).get("t");
  if (location.search) history.replaceState(null, "", location.pathname);
  return t || "";
})();

const TEXT = {
  en: {
    notoken: "This page was refreshed or opened in a new tab, so it cannot make changes. Open it again with the link printed in the terminal, or run durweg ui again.",
    tab_browse: "Browse", tab_installed: "Installed", tab_env: "This computer",
    browse_hint: "Workflows in the catalogs that are switched on.",
    installed_hint: "Workflows in your library. To run one, open your agent in your project folder and say the sentence below.",
    catalogs: "Catalogs", recheck: "Check again", copy: "Copy",
    loading: "Loading…", none: "Nothing here.", installed_as: "installed as", not_installed: "not installed",
    platforms: "platforms", after_install: "shown after installing", add_cmd: "add it in a terminal",
    run: "Run", run_where: "Open your agent (Claude Code, Codex or Antigravity) in the folder of your project, then say:",
    run_sentence: (n) => `Run ${n} with durweg.`, copied: "copied", copy_failed: "select the text and copy it",
    invalid: "missing or invalid", failed: "Could not load", on: "on", off: "off", fetched: "last downloaded",
    agent_has: { plugin: "has the Durweg plugin", skills: "has Durweg's skills", null: "does not have Durweg yet" },
    agent_missing: "not installed", agent_found: "installed", agent_not_on_path: "not on PATH",
    gh_missing: "gh is not installed (needed only for private catalogs and publishing)",
    gh_in: (a) => `GitHub: signed in as ${a}`, gh_out: "GitHub: not signed in. In a terminal run:",
    gh_unknown: "GitHub: could not tell", version: (v) => `v${v}`,
    update_all: "Update everything", restart: "Durweg was updated. Close this page, stop durweg ui (Ctrl-C) and run durweg ui again.",
    catalog_id: "catalog name, e.g. team", catalog_url: "https://… or git@host:path (empty for public)", catalog_add: "Add catalog",
    private_preview: "Make my private catalog…", private_create: "Yes, do it", tasks: "Changes",
    name_taken: (n) => `Your library already has a workflow named ${n} (from your own folder or another address).`,
    builtin: "comes with Durweg", add: "Add", remove: "Remove", update: "Update", switch_off: "Switch off",
    confirm_remove: (n) => `Remove ${n} from your library? Its folder stays on this computer.`,
    confirm_catalog_remove: (id) => id === "public" ? "Switch the public catalog off? You can switch it on again." : `Remove catalog ${id}? Workflows installed from it stay.`,
    confirm_update_all: "Update Durweg itself, the catalogs and all workflows? This can take some minutes.",
    would: (w, a) => `As ${a || "?"}, this would ${w}. Nothing has been done yet.`,
    state: { queued: "waiting", running: "running…", success: "done", partial: "partly done", failed: "failed", timeout: "took too long" },
    busy: "Another change is running; the buttons come back when it ends.",
  },
  zh: {
    notoken: "这个页面被刷新过或是在新标签页打开的，不能做修改。请用终端里打印的链接重新打开，或者再运行一次 durweg ui。",
    tab_browse: "浏览", tab_installed: "已装", tab_env: "这台电脑",
    browse_hint: "已打开的目录里的工作流。",
    installed_hint: "你方法库里的工作流。要运行，在你的项目文件夹里打开 agent，说下面这句话。",
    catalogs: "目录", recheck: "重新检查", copy: "复制",
    loading: "加载中…", none: "这里还没有。", installed_as: "已装为", not_installed: "未装",
    platforms: "平台", after_install: "装后可见", add_cmd: "在终端里加入",
    run: "运行", run_where: "在你的项目文件夹里打开 agent（Claude Code、Codex 或 Antigravity），然后说：",
    run_sentence: (n) => `用 durweg 运行 ${n}。`, copied: "已复制", copy_failed: "请选中文字自己复制",
    invalid: "缺失或无效", failed: "加载失败", on: "开", off: "关", fetched: "上次下载",
    agent_has: { plugin: "装了 Durweg 插件", skills: "有 Durweg 的技能", null: "还没有 Durweg" },
    agent_missing: "未安装", agent_found: "已安装", agent_not_on_path: "不在 PATH 上",
    gh_missing: "没有装 gh（只有私人目录和发布要用）",
    gh_in: (a) => `GitHub：已登录 ${a}`, gh_out: "GitHub：未登录。在终端里运行：",
    gh_unknown: "GitHub：查不到", version: (v) => `v${v}`,
    update_all: "全部更新", restart: "Durweg 已更新。请关闭这个页面，在终端里停掉 durweg ui（Ctrl-C），再运行一次 durweg ui。",
    catalog_id: "目录名，例如 team", catalog_url: "https://… 或 git@主机:路径（公开目录留空）", catalog_add: "加入目录",
    private_preview: "建我的私人目录…", private_create: "确认，照做", tasks: "改动",
    name_taken: (n) => `你的方法库里已经有一个叫 ${n} 的工作流（来自你自己的文件夹或别的地址）。`,
    builtin: "Durweg 自带", add: "加入", remove: "移除", update: "更新", switch_off: "关掉",
    confirm_remove: (n) => `从方法库移除 ${n}？它的文件夹会留在这台电脑上。`,
    confirm_catalog_remove: (id) => id === "public" ? "关掉公开目录？以后可以再打开。" : `移除目录 ${id}？从它装的工作流会留着。`,
    confirm_update_all: "更新 Durweg 本身、所有目录和所有工作流？可能要几分钟。",
    would: (w, a) => `以 ${a || "?"} 的身份，将会：${w}。现在还什么都没做。`,
    state: { queued: "排队中", running: "进行中…", success: "完成", partial: "部分完成", failed: "失败", timeout: "超时" },
    busy: "另一个改动正在进行；结束后按钮会恢复。",
  },
};
let T = TEXT.en;

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined && text !== null) e.textContent = String(text);
  return e;
}
function clear(id) { const n = document.getElementById(id); n.replaceChildren(); return n; }
function code(text) { return el("code", null, text); }

async function read(path) {
  const r = await fetch(path, { credentials: "omit", cache: "no-store" });
  return r.json();
}

let busy = false;
function button(label, onClick) {
  const b = el("button", "write", label); b.type = "button";
  b.addEventListener("click", onClick);
  return b;
}
function setWritable() {   // no token, or a change running: every change button is grey
  for (const b of document.querySelectorAll("button.write")) b.disabled = !token || busy;
}
async function change(body) {
  if (!token || busy) return null;
  busy = true; setWritable();
  try {
    const r = await fetch("/api/task", {
      method: "POST", credentials: "omit", cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Durweg-Token": token },
      body: JSON.stringify(body),
    });
    const j = await r.json();
    if (!j.ok) { alert(j.error || "?"); busy = false; setWritable(); return null; }
    pollTasks();
    return j.task;
  } catch (e) { alert(String(e)); busy = false; setWritable(); return null; }
}

let polling = null;
const RELOAD = { "library-add": ["browse", "installed"], "library-remove": ["browse", "installed"],
  "library-update": ["browse", "installed"], "update": ["browse", "installed", "env"],
  "catalog-add": ["browse", "env"], "catalog-remove": ["browse", "env"], "private-create": ["browse", "env"] };
const seenDone = new Set();
async function pollTasks() {
  if (polling) return;
  polling = true;
  try {
    for (;;) {
      const j = await read("/api/tasks");
      showTasks(j);
      const running = j.tasks.some((t) => t.state === "queued" || t.state === "running");
      for (const t of j.tasks) {
        if (running || seenDone.has(t.id) || t.state === "queued" || t.state === "running") continue;
        seenDone.add(t.id);
        for (const tab of RELOAD[t.action] || []) loaded[tab] = false;
        if (t.action === "private-preview") showPreview(t.result);
      }
      busy = running; setWritable();
      if (!running) { reloadOpenTab(); break; }
      await new Promise((r) => setTimeout(r, 1500));
    }
  } finally { polling = null; }
}

function showTasks(j) {
  document.getElementById("restart").hidden = !j.restart_ui;
  const box = clear("tasks_list");
  document.getElementById("tasks_box").hidden = !j.tasks.length;
  for (const t of j.tasks) {
    const card = el("div", "card task " + t.state);
    const h = el("div", "row");
    h.append(el("strong", null, t.label), el("span", t.state === "success" ? "good" : t.state === "running" || t.state === "queued" ? "muted" : "error", T.state[t.state] || t.state));
    card.append(h);
    const r = t.result;
    if (r) {
      if (r.error) card.append(el("p", "error", r.error));
      if (r.durweg) card.append(el("p", null, `Durweg: ${r.durweg.status} — ${r.durweg.detail}`));
      for (const it of r.items || []) if (it.status) card.append(el("p", it.status === "failed" ? "error" : "muted", `${it.name}: ${it.status}${it.detail ? " — " + it.detail : ""}`));
      for (const n of [].concat(r.notes || [], r.note ? [r.note] : [])) card.append(el("p", "warn", n));
      if (r.folder_kept) card.append(el("p", "muted path", r.folder_kept));
      if (r.output) card.append(el("pre", null, r.output));
    }
    box.append(card);
  }
}

function showPreview(r) {
  const box = document.getElementById("private_box");
  if (!r || !r.ok || !r.would) { box.hidden = true; return; }
  box.hidden = false;
  box.dataset.would = r.would;
  document.getElementById("private_would").textContent = T.would(r.would, r.account);
}

function failed(box, j) {
  const p = el("p", "error", `${T.failed}: ${j.error || "?"}`);
  box.append(p);
  if (j.output) box.append(el("pre", null, j.output));
}

function showCopy(name) {
  const box = document.getElementById("copybox");
  box.hidden = false;
  document.getElementById("copy_where").textContent = T.run_where;
  const input = document.getElementById("copy_text");
  input.value = T.run_sentence(name);
  document.getElementById("copy_state").textContent = "";
  input.focus(); input.select();
  box.scrollIntoView({ block: "nearest" });
}

async function loadBrowse() {
  const box = clear("browse_list"), notes = clear("browse_notes");
  box.append(el("p", "hint", T.loading));
  const j = await read("/api/available");
  box.replaceChildren();
  if (!j.ok) return failed(box, j);
  for (const n of j.notes || []) notes.append(el("p", "warn", n));
  if (!j.items.length) box.append(el("p", "hint", T.none));
  for (const it of j.items) {
    const card = el("div", "card");
    const h = el("div", "row");
    h.append(el("strong", null, it.title || it.name), el("span", "muted", it.ref));
    card.append(h);
    if (it.summary) card.append(el("p", null, it.summary));
    const meta = el("p", "muted");
    meta.textContent = (it.installed_as ? `${T.installed_as} ${it.installed_as}` : T.not_installed) + " · " +
      `${T.platforms}: ${it.platforms ? it.platforms.join(", ") : T.after_install}`;
    card.append(meta);
    if (it.installed_as) {
      const b = el("button", null, T.run); b.type = "button";
      b.addEventListener("click", () => showCopy(it.installed_as));
      card.append(b);
    } else if (it.name_in_library) {
      card.append(el("p", "muted", T.name_taken(it.name)));
    } else {
      card.append(button(T.add, () => change({ action: "library-add", ref: it.ref })));
    }
    box.append(card);
  }
  setWritable();
}

async function loadInstalled() {
  const box = clear("installed_list");
  box.append(el("p", "hint", T.loading));
  const j = await read("/api/installed");
  box.replaceChildren();
  if (!j.ok) return failed(box, j);
  if (!j.items.length) box.append(el("p", "hint", T.none));
  for (const it of j.items) {
    const card = el("div", "card");
    const h = el("div", "row");
    h.append(el("strong", null, it.name), el("span", "muted", it.valid ? (it.platforms || []).join(", ") : T.invalid));
    card.append(h, el("p", "muted path", it.url || it.path));
    const b = el("button", null, T.run); b.type = "button";
    b.addEventListener("click", () => showCopy(it.name));
    const row = el("div", "row");
    row.append(b, button(T.update, () => change({ action: "library-update", name: it.name })));
    if (it.builtin) row.append(el("span", "muted", T.builtin));
    else row.append(button(T.remove, () => { if (confirm(T.confirm_remove(it.name))) change({ action: "library-remove", name: it.name }); }));
    card.append(row);
    box.append(card);
  }
  setWritable();
}

async function loadEnv() {
  const box = clear("env_list"), cats = clear("catalog_list");
  box.append(el("p", "hint", T.loading));
  const [d, c] = await Promise.all([read("/api/doctor"), read("/api/catalogs")]);
  box.replaceChildren();
  if (!d.ok) failed(box, d);
  else {
    for (const a of d.agents) {
      const state = !a.installed && !a.durweg ? T.agent_missing
        : `${a.installed ? T.agent_found : T.agent_not_on_path}; ${T.agent_has[a.durweg]}`;
      const row = el("div", "row");
      row.append(el("strong", null, a.name), el("span", a.durweg ? "good" : "muted", state));
      box.append(row);
    }
    const g = d.github, p = el("p");
    if (!g.gh) p.textContent = T.gh_missing;
    else if (g.signed_in) p.textContent = T.gh_in(g.account || "?");
    else if (g.signed_in === null) p.textContent = `${T.gh_unknown}: ${g.note || ""}`;
    else { p.textContent = T.gh_out + " "; p.append(code("gh auth login --web")); }
    box.append(p);
  }
  if (!c.ok) return failed(cats, c);
  for (const it of c.items) {
    const row = el("div", "row");
    row.append(el("strong", null, it.id), el("span", it.on ? "good" : "muted", it.on ? T.on : T.off),
      el("span", "muted path", it.url + (it.fetched ? ` · ${T.fetched} ${it.fetched}` : "")));
    if (it.on) row.append(button(it.id === "public" ? T.switch_off : T.remove,
      () => { if (confirm(T.confirm_catalog_remove(it.id))) change({ action: "catalog-remove", id: it.id }); }));
    else if (it.id === "public") row.append(button(T.add, () => change({ action: "catalog-add", id: "public" })));
    cats.append(row);
  }
  setWritable();
}

const LOAD = { browse: loadBrowse, installed: loadInstalled, env: loadEnv };
const loaded = {};
let current = "browse";
function reloadOpenTab() { if (!loaded[current]) openTab(current, true); }
function openTab(name, keepCopy) {
  current = name;
  for (const s of document.querySelectorAll("main > section")) s.hidden = s.id !== name;
  for (const b of document.querySelectorAll(".tab")) b.setAttribute("aria-pressed", String(b.dataset.tab === name));
  if (!keepCopy) document.getElementById("copybox").hidden = true;
  if (!loaded[name]) { loaded[name] = true; LOAD[name]().catch((e) => failed(clear(name + "_list"), { error: String(e) })); }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!token) document.getElementById("notoken").hidden = false;
  try {
    const v = await read("/api/ping");
    T = TEXT[v.language] || TEXT.en;
    document.documentElement.lang = v.language || "en";
    document.getElementById("version").textContent = T.version(v.version);
  } catch (e) { /* the tabs show their own errors */ }
  for (const n of document.querySelectorAll("[data-t]")) n.textContent = T[n.dataset.t];
  for (const n of document.querySelectorAll("[data-ph]")) n.placeholder = T[n.dataset.ph];
  document.getElementById("update_all").addEventListener("click", () => { if (confirm(T.confirm_update_all)) change({ action: "update" }); });
  document.getElementById("catalog_form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const id = document.getElementById("catalog_id").value.trim(), url = document.getElementById("catalog_url").value.trim();
    change(url ? { action: "catalog-add", id, url } : { action: "catalog-add", id });
  });
  document.getElementById("private_preview").addEventListener("click", () => {
    document.getElementById("private_box").hidden = true;
    change({ action: "private-preview" });
  });
  document.getElementById("private_create").addEventListener("click", () => {
    change({ action: "private-create", would: document.getElementById("private_box").dataset.would || "" });
    document.getElementById("private_box").hidden = true;
  });
  setWritable();
  pollTasks();
  for (const b of document.querySelectorAll(".tab")) b.addEventListener("click", () => openTab(b.dataset.tab));
  document.getElementById("recheck").addEventListener("click", () => { loaded.env = false; openTab("env"); });
  document.getElementById("copy_btn").addEventListener("click", async () => {
    const input = document.getElementById("copy_text"), state = document.getElementById("copy_state");
    try { await navigator.clipboard.writeText(input.value); state.textContent = T.copied; }
    catch (e) { input.select(); state.textContent = T.copy_failed; }   // no clipboard: the text stays selectable
  });
  openTab("browse");
});
