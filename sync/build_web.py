"""Build the GitHub editions of the two ledger pages.

Usage: python sync/build_web.py [repo_dir]
Reads web/claude/*.html (the Claude versions) and web/github-store.js, and writes
single-file pages web/股票損益帳本.html and web/花費紀錄帳本.html that keep their
data in data/trades.json and data/expenses.json in this GitHub repository.
"""
import sys
from pathlib import Path

PAGES = [
    ("trade-log.html", "股票損益帳本.html", "trades", "交易紀錄",
     't => `${t.name||""}(${t.code||""}) ${t.date||""} ${t.pnl??""}`'),
    ("spend-log.html", "花費紀錄帳本.html", "expenses", "花費紀錄",
     't => `${t.cat||""} ${t.item||""} ${t.amount??""}`'),
]

HEAD = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"></head><body>\n')


def build(repo):
    web = repo / "web"
    store = (web / "github-store.js").read_text(encoding="utf-8")
    for src, out, coll, label, describe in PAGES:
        html = (web / "claude" / src).read_text(encoding="utf-8")
        html = html.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
        swaps = [
            ('await window.claude?.use?.("db") ?? null', f'await GH.connect("{coll}", {describe})'),
            ('const user = await window.claude.use("user");', "const user = null;"),
            ("無法連到資料庫（請登入後開啟）", "尚未連線 GitHub"),
            (f"登入後才能看到{label}。", "請在上方「GitHub 連線設定」貼上權杖後，就會載入資料。"),
            ("已同步 · 自動儲存", "已連線 GitHub · 每次修改會直接存回倉庫"),
        ]
        for old, new in swaps:
            if old not in html:
                sys.exit(f"{src}: expected text not found: {old}")
            html = html.replace(old, new)
        html = html.replace("<script>\n", f"<script>\n{store}\n", 1)
        (web / out).write_text(HEAD + html + "\n</body></html>\n", encoding="utf-8")
        print("wrote", web / out)


if __name__ == "__main__":
    build(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
