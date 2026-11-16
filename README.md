# 記帳本

### [▶ 打開花費紀錄帳本](https://claude.ai/artifact/XARnPyQCAGmknijHy7obMF)
### [▶ 打開股票損益帳本](https://claude.ai/artifact/UxgPWC8xDdghnMTfKgHyDQ)

（點上面的連結會直接打開網頁，可以新增、編輯、刪除。需要登入 Claude。）

兩本帳：**股票損益帳本**（每筆已實現損益）和 **花費紀錄帳本**（醫美、奢侈品、其它大額花費）。

## 連結

| 帳本 | Claude 版（登入 Claude 即可用） | GitHub 版（下載後用瀏覽器打開） |
|---|---|---|
| 股票損益帳本 | https://claude.ai/artifact/UxgPWC8xDdghnMTfKgHyDQ | [web/股票損益帳本.html](web/股票損益帳本.html) |
| 花費紀錄帳本 | https://claude.ai/artifact/XARnPyQCAGmknijHy7obMF | [web/花費紀錄帳本.html](web/花費紀錄帳本.html) |

## 檔案

| 檔案 | 用途 |
|---|---|
| `web/股票損益帳本.html`、`web/花費紀錄帳本.html` | **GitHub 版網頁**：下載後用瀏覽器打開，可新增、編輯、刪除，資料直接存回本倉庫的 `data/` |
| `data/trades.json`、`data/expenses.json` | 兩本帳的原始資料（GitHub 版網頁讀寫的就是這兩個檔） |
| `股票買賣紀錄.xlsx`、`花費紀錄.xlsx` | Excel 版，含勝率、淨損益、各類別合計等公式 |
| `web/claude/` | Claude 版網頁的原始碼（在 Claude 上重新發布用） |
| `sync/` | 產生 Excel 和 GitHub 版網頁的程式 |

## 使用 GitHub 版網頁

1. **建立權杖（只做一次）**：GitHub → 右上頭像 → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token。
   - Repository access 選 **Only select repositories** → `LEE`
   - Permissions → Repository permissions → **Contents: Read and write**
   - 產生後複製 `github_pat_…` 開頭的字串。
2. **打開網頁**：在 GitHub 上點 `web/股票損益帳本.html` → 右上角 **Download raw file** → 用 Chrome、Safari 或 Edge 打開下載的檔案。
3. **第一次打開**：在「GitHub 連線設定」貼上權杖，按「儲存並連線」。之後這台電腦就會記住。
4. 新增、編輯、刪除都會直接存回 GitHub（每次修改是一個 commit，訊息以「網頁編輯：」開頭）。

注意：
- 權杖只存在你這台電腦的瀏覽器，不會上傳到任何地方。用公用電腦時，用完請按「從這台電腦移除權杖」。
- 權杖等於倉庫的鑰匙，不要傳給別人或貼在公開的地方。
- GitHub 版網頁修改後，Excel 不會自動更新。需要時在電腦上執行 `python sync/build_xlsx.py --from-data .`。

## Claude 版與 GitHub 版

- Claude 版（claude.ai 上的網頁）資料存在 Claude，每天晚上 9:13 自動同步到這裡。
- 兩邊各自有一份資料。**同一段時間請只用其中一邊**，以免互相覆蓋。
- 自動同步若發現 GitHub 版有人改過，會停下來不覆蓋，並提醒你。
