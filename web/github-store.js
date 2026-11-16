/* GitHub 版資料層：把帳本資料存在 GitHub 倉庫的 data/<集合>.json。
 * 提供與 Claude 網頁版相同的介面：collection(name).add / doc(id).update / doc(id).delete / onSnapshot。
 * 權杖只存在這台電腦的瀏覽器（localStorage），不會寫進任何檔案。 */
const GH = (() => {
  const KEY = "lee-ledger-github";
  const DEFAULTS = { owner: "SHUTINGLEE", repo: "LEE", branch: "claude/gallant-rubin-7oq112", token: "" };
  let cfg = { ...DEFAULTS };
  try { Object.assign(cfg, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) {}

  const enc = s => { const b = new TextEncoder().encode(s); let bin = ""; for (let i = 0; i < b.length; i += 0x8000) bin += String.fromCharCode(...b.subarray(i, i + 0x8000)); return btoa(bin); };
  const dec = b64 => new TextDecoder().decode(Uint8Array.from(atob(b64.replace(/\s/g, "")), c => c.charCodeAt(0)));
  const api = (path, opts = {}) => fetch(`https://api.github.com/repos/${cfg.owner}/${cfg.repo}/contents/${path}`, {
    cache: "no-store", ...opts,
    headers: { Accept: "application/vnd.github+json", Authorization: `Bearer ${cfg.token}`, ...(opts.headers || {}) },
  });

  async function readFile(path) {
    const r = await api(`${path}?ref=${encodeURIComponent(cfg.branch)}`);
    if (r.status === 404) return { rows: [], sha: null };
    if (r.status === 401 || r.status === 403) throw new Error("auth");
    if (!r.ok) throw new Error("http " + r.status);
    const j = await r.json();
    return { rows: JSON.parse(dec(j.content)), sha: j.sha };
  }

  async function writeFile(path, rows, sha, message) {
    const sorted = [...rows].sort((a, b) => String(a.id).localeCompare(String(b.id)));
    const body = { message, branch: cfg.branch, content: enc(JSON.stringify(sorted, null, 1) + "\n") };
    if (sha) body.sha = sha;
    const r = await api(path, { method: "PUT", body: JSON.stringify(body), headers: { "Content-Type": "application/json" } });
    if (r.status === 409 || r.status === 422) return null; // 檔案剛被別處改過，重抓再試
    if (r.status === 401 || r.status === 403) throw new Error("auth");
    if (!r.ok) throw new Error("http " + r.status);
    return (await r.json()).content.sha;
  }

  function panel(open, note) {
    let el = document.getElementById("gh-panel");
    if (!el) {
      el = document.createElement("details");
      el.id = "gh-panel";
      el.innerHTML = `
        <summary>GitHub 連線設定</summary>
        <div class="gh-body">
          <p class="gh-note" id="gh-note"></p>
          <label for="gh-token">GitHub 權杖（fine-grained token，需要 LEE 倉庫的 Contents 讀寫權限）<input id="gh-token" type="password" autocomplete="off" placeholder="github_pat_…"></label>
          <div class="gh-row">
            <label for="gh-owner">帳號<input id="gh-owner"></label>
            <label for="gh-repo">倉庫<input id="gh-repo"></label>
            <label for="gh-branch">分支<input id="gh-branch"></label>
          </div>
          <div class="gh-row gh-btns"><button type="button" class="primary" id="gh-save">儲存並連線</button><button type="button" id="gh-clear">從這台電腦移除權杖</button></div>
          <p class="gh-note">權杖只存在這台電腦的瀏覽器裡。在公用電腦上用完請按「移除權杖」。</p>
        </div>`;
      const st = document.createElement("style");
      st.textContent = `#gh-panel{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 16px}
        #gh-panel summary{cursor:pointer;font-weight:500}
        .gh-body{display:flex;flex-direction:column;gap:10px;margin-top:10px}
        .gh-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
        .gh-btns{grid-template-columns:auto auto;justify-content:start}
        .gh-note{margin:0;font-size:13px;color:var(--muted)}`;
      document.head.appendChild(st);
      document.querySelector("header").after(el);
      el.querySelector("#gh-save").onclick = () => {
        cfg = { token: el.querySelector("#gh-token").value.trim(), owner: el.querySelector("#gh-owner").value.trim() || DEFAULTS.owner,
                repo: el.querySelector("#gh-repo").value.trim() || DEFAULTS.repo, branch: el.querySelector("#gh-branch").value.trim() || DEFAULTS.branch };
        try { localStorage.setItem(KEY, JSON.stringify(cfg)); } catch (e) {}
        location.reload();
      };
      el.querySelector("#gh-clear").onclick = () => { try { localStorage.removeItem(KEY); } catch (e) {} location.reload(); };
    }
    el.querySelector("#gh-token").value = cfg.token;
    el.querySelector("#gh-owner").value = cfg.owner;
    el.querySelector("#gh-repo").value = cfg.repo;
    el.querySelector("#gh-branch").value = cfg.branch;
    el.querySelector("#gh-note").textContent = note || "";
    el.open = !!open;
  }

  async function connect(name, describe) {
    const path = `data/${name}.json`;
    if (!cfg.token) { panel(true, "第一次使用：請貼上 GitHub 權杖，資料會從你的私人倉庫讀取和儲存。"); return null; }
    let state;
    try { state = await readFile(path); }
    catch (e) { panel(true, e.message === "auth" ? "權杖無效或沒有這個倉庫的權限，請重新設定。" : "連不到 GitHub，請檢查網路後重新整理。"); return null; }
    panel(false, `已連線 ${cfg.owner}/${cfg.repo}（${cfg.branch}）`);
    const listeners = [];
    const snap = () => ({ docs: state.rows.map(r => { const { id, ...d } = r; return { id, data: () => d }; }), metadata: { fromCache: false, hasPendingWrites: false } });
    const emit = () => listeners.forEach(fn => fn(snap()));

    async function mutate(apply, message) {
      for (let attempt = 0; attempt < 3; attempt++) {
        const fresh = await readFile(path);
        const rows = apply(fresh.rows.map(r => ({ ...r })));
        const sha = await writeFile(path, rows, fresh.sha, message);
        if (sha) { state = { rows, sha }; emit(); return; }
      }
      throw new Error("conflict");
    }
    const newId = () => "w" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

    return {
      collection: () => ({
        onSnapshot(next) { listeners.push(next); next(snap()); return () => {}; },
        async add(data) { const id = newId(); await mutate(rows => [...rows, { id, ...data }], `網頁編輯：新增 ${describe(data)}`); return { id }; },
        doc: id => ({
          async update(patch) { await mutate(rows => rows.map(r => r.id === id ? { ...r, ...patch } : r), `網頁編輯：修改 ${describe(patch)}`); },
          async delete() { let gone = ""; await mutate(rows => rows.filter(r => { if (r.id === id) { gone = describe(r); return false; } return true; }), `網頁編輯：刪除 ${id}`); },
        }),
      }),
    };
  }
  return { connect, panel: () => panel(true) };
})();
