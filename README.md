# Blender 台灣繁體中文自動同步

追蹤 [Blender 官方 zh_HANS 翻譯](https://projects.blender.org/blender/blender-ui-translations/src/branch/main/zh_HANS)，以 OpenCC `s2twp` 轉換成台灣繁體中文，輸出至 `zh_TW/`。

## 下載安裝

到 **[最新發行版本](https://github.com/shuwn/Blender-Traditional-Chinese/releases/latest)** 下載 **Blender-Taiwan-Chinese.zip**。

Blender → 編輯 → 偏好設定 → 附加元件 → 右上選單「從磁碟安裝」→ 選取 ZIP → 啟用 Taiwan Chinese → 展開設定按「套用台灣繁體中文」→ 重新啟動。

工具自動辨識 `zh_HANT`／`zh_TW`，備份後替換原有繁體中文，提供「還原原版」按鈕。目標為 Blender 4.2+；寫入安裝目錄需要權限。**移除工具前先還原；停用工具不會自動還原翻譯。** 版本相容性、各平台權限與手動安裝請看 [安裝說明](docs/INSTALL.md)。

發行版本同時提供 `blender.mo`、`zh_TW.po`、來源版本資訊與 SHA-256 校驗碼。翻譯或安裝工具變更後，Actions 會自動打包並建立新 Release；相同安裝包不重複發布。

已在 macOS 的 Blender 5.2.2 LTS，以隔離的語言檔及偏好設定驗證安裝工具註冊、安裝、重新啟動後的「Render → 算繪」載入與原版還原。Windows／Linux 尚未做 Blender 實機驗證。

## 自動更新

GitHub Actions 每 6 小時檢查一次（台灣時間 02:17、08:17、14:17、20:17，實際執行可能延遲），也可從 Actions → Sync Taiwan Traditional Chinese → Run workflow 手動執行。只有翻譯或來源雜湊變更時才提交。下載或解析失敗不會提交，錯誤可在 Actions 查看。

流程需要儲存庫允許 Actions 與 `GITHUB_TOKEN` 的 contents write 權限，且 main 分支允許 Actions bot 推送。依 [GitHub 排程文件](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)，公開儲存庫若連續 60 天沒有活動，GitHub 會停用排程，需要重新啟用；因此此排程並非永不停機的保證。

## 轉換原則

- 僅轉換 PO 的 msgstr／複數翻譯；保留 msgid、msgctxt、註解與 fuzzy 標記。
- 使用台灣詞彙，例如「软件」→「軟體」、「鼠标」→「滑鼠」。格式參數、URL 與標記受到保護。
- 保留空白翻譯；不以機器翻譯補寫缺少的內容。
- `sync-state.json` 記錄每個來源 PO 檔的 SHA-256。
- OpenCC 轉換後會套用 [專業術語表](glossary/terms.json)，支援英文條目與語境限制；術語表變更會自動觸發同步。
- [術語套用報告](glossary/report.json) 記錄命中次數及範例，`sync-state.json` 同時記錄術語表 SHA-256。
- 自動轉換不等同人工校訂，也不是 Blender 官方繁中版本；專業術語與多義字仍需審閱。

儲存庫保留 PO 翻譯原始檔；Release 提供編譯後 MO 與安裝工具。上游翻譯之著作權及授權仍屬原作者，散布與使用須遵循上游授權；本專案不重新授權上游內容。

## 本機執行

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
git clone --depth 1 --filter=blob:none --sparse --branch main https://projects.blender.org/blender/blender-ui-translations.git .upstream
git -C .upstream sparse-checkout set zh_HANS
python scripts/sync.py --source .upstream/zh_HANS
python scripts/build_release.py
```

`zh_TW/` 是自動產物，下次同步會覆寫手動變更。專業術語請修改 `glossary/terms.json`，參閱 [術語維護與校訂流程](glossary/README.md)；不必修改 Python 程式。轉換邏輯的變更才需要修改 `scripts/sync.py` 並新增測試。

## 原作者與授權

上游授權全文收錄於 `LICENSE.upstream`，產出 PO 保留原始作者聲明。原始檔聲明：the original file is released and copyrighted by www.blendercn.org。
