"""Rebuild the two Excel ledgers from the web ledgers' exported database rows.

Usage: python sync/build_xlsx.py <export_dir> [repo_dir]
       python sync/build_xlsx.py --from-data [repo_dir]   (rebuild Excel from data/*.json,
       e.g. after editing with the GitHub edition of the pages in web/)
<export_dir> holds trades/*.json and expenses/*.json (one JSON file per row,
as exported from 股票損益帳本 and 花費紀錄帳本). Writes:
  股票買賣紀錄.xlsx, 花費紀錄.xlsx, data/trades.json, data/expenses.json
"""
import json, sys
from datetime import date
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

F = "Arial"
thin = Side(style="thin", color="BFBFBF")
BD = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="305496")
LAB = PatternFill("solid", fgColor="D9E1F2")


def load(d):
    rows = []
    for p in sorted(Path(d).glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        r["id"] = p.stem
        rows.append(r)
    return rows


def to_date(s):
    """'YYYY-MM-DD' -> date; 'YYYY-MM' -> 'YYYY/MM' text; '' -> None."""
    if not s:
        return None
    parts = s.split("-")
    if len(parts) == 3:
        return date(*map(int, parts))
    return s.replace("-", "/")


def header(ws, row, titles):
    for i, h in enumerate(titles, 1):
        c = ws.cell(row, i, h)
        c.font = Font(name=F, bold=True, color="FFFFFF")
        c.fill = HEAD
        c.alignment = Alignment(horizontal="center")
        c.border = BD


def summary(ws, start, items):
    for j, (lab, fm, nf) in enumerate(items):
        r = start + j
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
        a = ws.cell(r, 1, lab)
        a.font = Font(name=F, bold=True); a.fill = LAB; a.border = BD
        c = ws.cell(r, 3, fm)
        c.font = Font(name=F, bold=True); c.number_format = nf; c.border = BD
        c.alignment = Alignment(horizontal="right")


def build_trades(rows, out):
    rows = sorted(rows, key=lambda t: (t["date"], t.get("created", 0)))
    wb = Workbook(); ws = wb.active; ws.title = "買賣紀錄"
    ws["A1"] = "股票買賣損益紀錄"; ws["A1"].font = Font(name=F, size=14, bold=True)
    ws["A2"] = "由網頁「股票損益帳本」自動同步；要新增或刪除請在網頁上操作。"
    ws["A2"].font = Font(name=F, italic=True, size=9, color="808080")
    header(ws, 3, ["#", "日期", "股票名稱", "代號", "損益 (NT$)", "結果"])
    r0 = 4
    for k, t in enumerate(rows):
        r = r0 + k
        neg = t["pnl"] < 0
        vals = [k + 1, to_date(t["date"]), t["name"], t["code"], t["pnl"],
                f'=IF(E{r}>0,"賺",IF(E{r}<0,"賠","持平"))']
        for i, v in enumerate(vals, 1):
            c = ws.cell(r, i, v); c.border = BD
            c.font = Font(name=F, color="C00000" if neg and i >= 5 else "000000")
            c.alignment = Alignment(horizontal="right" if i == 5 else "center")
        ws.cell(r, 2).number_format = "yyyy/mm/dd"
        ws.cell(r, 5).number_format = '#,##0;-#,##0;"-"'
    last = max(r0, r0 + len(rows) - 1)
    s = last + 2
    E = f"E{r0}:E{last}"
    summary(ws, s, [
        ("總交易筆數", f"=COUNT({E})", "0"),
        ("賺錢筆數", f'=COUNTIF({E},">0")', "0"),
        ("賠錢筆數", f'=COUNTIF({E},"<0")', "0"),
        ("勝率", f"=IF(C{s}=0,0,C{s+1}/C{s})", "0.0%"),
        ("獲利合計 (NT$)", f'=SUMIF({E},">0")', "#,##0"),
        ("虧損合計 (NT$)", f'=SUMIF({E},"<0")', "#,##0;-#,##0"),
        ("淨損益 (NT$)", f"=SUM({E})", "#,##0;-#,##0"),
        ("平均每筆損益 (NT$)", f"=IF(C{s}=0,0,C{s+6}/C{s})", "#,##0;-#,##0"),
    ])
    ws.cell(s + 6, 3).fill = PatternFill("solid", fgColor="FFF2CC")
    for col, w in zip("ABCDEF", [6, 13, 16, 10, 14, 8]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A4"; ws.auto_filter.ref = f"A3:F{last}"
    wb.save(out)


def build_expenses(rows, out):
    base = ["醫美", "奢侈品", "其它"]
    cats = base + sorted({r["cat"] for r in rows} - set(base))
    rows = sorted(rows, key=lambda t: (t["date"] == "", t["date"], t.get("created", 0)))
    wb = Workbook(); ws = wb.active; ws.title = "花費紀錄"
    ws["A1"] = "花費紀錄"; ws["A1"].font = Font(name=F, size=14, bold=True)
    ws["A2"] = "由網頁「花費紀錄帳本」自動同步；要新增或刪除請在網頁上操作。"
    ws["A2"].font = Font(name=F, italic=True, size=9, color="808080")
    header(ws, 3, ["類別", "項目", "金額 (NT$)", "日期", "備註"])
    r0 = 4
    for k, t in enumerate(rows):
        r = r0 + k
        d = to_date(t.get("date", ""))
        for i, v in enumerate([t["cat"], t["item"], t["amount"], d, t.get("note", "")], 1):
            c = ws.cell(r, i, v); c.border = BD; c.font = Font(name=F)
            c.alignment = Alignment(horizontal="left" if i in (2, 5) else "center",
                                    vertical="top", wrap_text=(i == 5))
        ws.cell(r, 3).number_format = "#,##0"; ws.cell(r, 3).alignment = Alignment(horizontal="right", vertical="top")
        ws.cell(r, 4).number_format = "yyyy/mm/dd"
    last = max(r0, r0 + len(rows) - 1)
    s = last + 2
    A, C = f"$A${r0}:$A${last}", f"$C${r0}:$C${last}"
    items = [("總支出 (NT$)", f"=SUM({C})", "#,##0"), ("筆數", f"=COUNTA({C})", "0")]
    items += [(f"{c} (NT$)", f'=SUMIF({A},"{c}",{C})', "#,##0") for c in cats]
    summary(ws, s, items)
    ws.cell(s, 3).fill = PatternFill("solid", fgColor="FFF2CC")
    for col, w in zip("ABCDE", [10, 26, 14, 13, 60]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A4"; ws.auto_filter.ref = f"A3:E{last}"
    wb.save(out)


def main():
    repo = Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    if sys.argv[1] == "--from-data":
        read = lambda n: json.loads((repo / "data" / f"{n}.json").read_text(encoding="utf-8"))
        trades, expenses = read("trades"), read("expenses")
    else:
        exp = Path(sys.argv[1])
        trades, expenses = load(exp / "trades"), load(exp / "expenses")
    if not trades or not expenses:
        sys.exit("export is missing trades or expenses rows; nothing written")
    (repo / "data").mkdir(exist_ok=True)
    for name, rows in (("trades", trades), ("expenses", expenses)):
        clean = sorted(({k: v for k, v in r.items()} for r in rows), key=lambda r: r["id"])
        (repo / "data" / f"{name}.json").write_text(
            json.dumps(clean, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    build_trades(trades, repo / "股票買賣紀錄.xlsx")
    build_expenses(expenses, repo / "花費紀錄.xlsx")
    print(f"trades={len(trades)} expenses={len(expenses)}")


if __name__ == "__main__":
    main()
