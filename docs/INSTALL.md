# 安裝台灣繁體中文翻譯

## 下載與安裝（建議）

1. 到 [最新發行版本](https://github.com/shuwn/Blender-Traditional-Chinese/releases/latest)，下載 **Blender-Taiwan-Chinese.zip**，不要選 GitHub 自動提供的 Source code ZIP，也不必解壓縮。
2. 開啟 Blender → **Edit／編輯 → Preferences／偏好設定 → Add-ons／附加元件**。
3. 點右上角選單 → **Install from Disk／從磁碟安裝**，選取下載的 ZIP。這是傳統附加元件 ZIP，不是從 Get Extensions 搜尋下載的擴充套件。
4. 搜尋 **Taiwan Chinese**，勾選啟用並展開設定。
5. 按 **套用台灣繁體中文**。工具會顯示並自動找到原有的繁體中文語言檔，保留首次替換前的備份，再寫入新翻譯並選擇繁體中文介面。
6. **重新啟動 Blender**。若未自動切換，請在 Interface → Translation 選擇 Chinese (Traditional)，並啟用 Interface、Tooltips。

本工具目標為 Blender 4.2 以上，使用各平台共通的 Blender Python API，無須另裝 Python 或 OpenCC。發布前的實機驗證平台會記錄於專案 README；未測平台仍須依實際權限及安裝方式確認。

## 相容性與權限

- 翻譯追蹤官方 **main**，不代表每一版 Blender 的完整對應語言包。請查看發行說明或 metadata.json 的來源版本；不同版本的字串可能缺譯。fuzzy、空白及過時翻譯不編譯進 MO，缺少的項目可能顯示英文。
- 工具會修改 Blender 安裝目錄中的原有 `.mo` 檔，不會改動 `.blend` 專案。電腦上多個 Blender 安裝各有獨立備份，僅套用目前執行中的安裝。
- **Windows**：Program Files 通常需要寫入權限。可使用官方 ZIP 可攜版解壓至自己可寫入的資料夾，再安裝工具；也可關閉 Blender 後以系統管理員執行，套用完成後關閉並恢復一般方式使用。
- **macOS**：修改 `.app` 內的資源可能影響應用程式簽章驗證。建議先保留官方下載的 Blender 安裝檔；若目錄不可寫，可使用自己帳號擁有的 Blender 副本。工具不會自動提升權限、移除隔離屬性或停用系統防護；若系統拒絕啟動，請重新安裝官方 Blender。
- **Linux**：套件管理器安裝的 `/usr/share` 通常不可由一般使用者寫入。建議將 Blender 官方壓縮包解壓至自己擁有的資料夾使用；本工具不會自動執行 sudo。
- 安裝、套用及還原前請先儲存工作並關閉其他 Blender 視窗，完成後重新啟動。不要在不同權限帳號之間切換，否則可能讀不到原先使用者設定內的備份。

## 還原與更新

在同一工具設定按 **還原原版繁體中文**，重新啟動 Blender。備份保存在該 Blender 版本的使用者設定資料夾 `taiwan_chinese_backups/`，工具設定會顯示完整路徑。備份不放在附加元件資料夾，因此更新附加元件不會刪掉原版備份。

**停用或刪除附加元件不會自動還原**。若要移除，請先按還原再移除工具。

取得新版翻譯後，可從磁碟安裝新的 ZIP，再按套用；原版備份不會被新版翻譯覆蓋。若 Blender 更新或其他工具已修改語言檔，工具會拒絕用舊備份覆蓋它。此時先關閉 Blender、確認新版官方語言檔正確，將設定中顯示的該安裝專屬備份資料夾**移存**到其他位置，再重新套用以建立新版備份。請勿刪除不明備份。

## 手動安裝

發行版本也提供 `blender.mo`，不需要自行編譯。先關閉 Blender，將原有檔案複製到安全位置，再以下載檔替換下列位置的同名檔：

- Windows：`<Blender 安裝目錄>/<版本>/datafiles/locale/zh_HANT/LC_MESSAGES/blender.mo`
- macOS：`Blender.app/Contents/Resources/<版本>/datafiles/locale/zh_HANT/LC_MESSAGES/blender.mo`
- Linux 官方壓縮包：`<Blender 目錄>/<版本>/datafiles/locale/zh_HANT/LC_MESSAGES/blender.mo`

部分版本使用 `zh_TW`，請替換**已存在**的繁體中文目錄，不要任意新增或覆蓋簡體中文 `zh_HANS`。套件管理器與自訂版本的路徑可能不同，可在 Blender Python Console 執行 `bpy.utils.system_resource('DATAFILES', path='locale')` 查詢。

重新啟動後在偏好設定選擇繁體中文。手動還原時將備份檔複製回同一位置。

## 檔案校驗

發行版本附 `SHA256SUMS.txt`。macOS 可使用 `shasum -a 256 Blender-Taiwan-Chinese.zip`；Linux 使用 `sha256sum`；Windows PowerShell 使用 `Get-FileHash .\Blender-Taiwan-Chinese.zip -Algorithm SHA256`，與清單比對。工具套用時也會檢查內附 MO 的雜湊。
