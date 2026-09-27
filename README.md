# Blender 台灣繁體中文自動同步

追蹤 [Blender 官方 zh_HANS 翻譯](https://projects.blender.org/blender/blender-ui-translations/src/branch/main/zh_HANS)，以 OpenCC `s2twp` 轉換成台灣繁體中文，輸出至 `zh_TW/`。

## 自動更新

GitHub Actions 每 6 小時檢查一次（台灣時間 02:17、08:17、14:17、20:17，實際執行可能延遲），也可從 Actions → Sync Taiwan Traditional Chinese → Run workflow 手動執行。只有翻譯或來源雜湊變更時才提交。下載或解析失敗不會提交，錯誤可在 Actions 查看。

流程需要儲存庫允許 Actions 與 `GITHUB_TOKEN` 的 contents write 權限，且 main 分支允許 Actions bot 推送。依 [GitHub 排程文件](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)，公開儲存庫若連續 60 天沒有活動，GitHub 會停用排程，需要重新啟用；因此此排程並非永不停機的保證。

## 轉換原則

- 僅轉換 PO 的 msgstr／複數翻譯；保留 msgid、msgctxt、註解與 fuzzy 標記。
- 使用台灣詞彙，例如「软件」→「軟體」、「鼠标」→「滑鼠」。格式參數、URL 與標記受到保護。
- 保留空白翻譯；不以機器翻譯補寫缺少的內容。
- `sync-state.json` 記錄每個來源 PO 檔的 SHA-256。
- 自動轉換不等同人工校訂，也不是 Blender 官方繁中版本；專業術語與多義字仍需審閱。

產物為 PO 翻譯原始檔，不是可直接安裝的 Blender 語言包。上游翻譯之著作權及授權仍屬原作者，散布與使用須遵循上游授權；本專案不重新授權上游內容。

## 本機執行

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
git clone --depth 1 --filter=blob:none --sparse --branch main https://projects.blender.org/blender/blender-ui-translations.git .upstream
git -C .upstream sparse-checkout set zh_HANS
python scripts/sync.py --source .upstream/zh_HANS
```

`zh_TW/` 是自動產物，下次同步會覆寫手動變更。轉換規則請修改 `scripts/sync.py` 並新增測試。

## 原作者與授權

上游授權全文收錄於 `LICENSE.upstream`，產出 PO 保留原始作者聲明。原始檔聲明：the original file is released and copyrighted by www.blendercn.org。
