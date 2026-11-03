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
    browse_hint: "Workflows in the catalogs that are switched on. Adding and removing come in the next version of this page; for now the command is shown.",
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
  },
  zh: {
    notoken: "这个页面被刷新过或是在新标签页打开的，不能做修改。请用终端里打印的链接重新打开，或者再运行一次 durweg ui。",
    tab_browse: "浏览", tab_installed: "已装", tab_env: "这台电脑",
    browse_hint: "已打开的目录里的工作流。加入和移除在这个页面的下一版里做；现在先给出命令。",
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
    } else {
      const p = el("p", "muted", `${T.add_cmd}: `);
      p.append(code(`durweg library add ${it.ref}`));
      card.append(p);
    }
    box.append(card);
  }
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
    card.append(b);
    box.append(card);
  }
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
    cats.append(row);
  }
}

const LOAD = { browse: loadBrowse, installed: loadInstalled, env: loadEnv };
const loaded = {};
function openTab(name) {
  for (const s of document.querySelectorAll("main > section")) s.hidden = s.id !== name;
  for (const b of document.querySelectorAll(".tab")) b.setAttribute("aria-pressed", String(b.dataset.tab === name));
  document.getElementById("copybox").hidden = true;
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
  for (const b of document.querySelectorAll(".tab")) b.addEventListener("click", () => openTab(b.dataset.tab));
  document.getElementById("recheck").addEventListener("click", () => { loaded.env = false; openTab("env"); });
  document.getElementById("copy_btn").addEventListener("click", async () => {
    const input = document.getElementById("copy_text"), state = document.getElementById("copy_state");
    try { await navigator.clipboard.writeText(input.value); state.textContent = T.copied; }
    catch (e) { input.select(); state.textContent = T.copy_failed; }   // no clipboard: the text stays selectable
  });
  openTab("browse");
});
