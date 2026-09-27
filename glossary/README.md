# 專業術語對照與校訂

`terms.json` 是唯一人工維護的術語來源。同步依序執行「官方簡中 PO → OpenCC 台灣繁體 → active 術語修正 → PO 檢查與編譯 → GitHub 提交」。初始表是本專案用詞約定，不代表 Blender 官方審定；可直接修改並透過 Git 記錄討論與修訂。

## 初始對照

| 英文 | OpenCC 後用詞 | 專案用詞 | 範圍／狀態 |
| --- | --- | --- | --- |
| Render / Rendering | 渲染 | 算繪 | 全文啟用 |
| Keyframe | 關鍵幀 | 關鍵影格 | 全文啟用 |
| Frame Rate | 幀率 | 影格率 | 全文啟用 |
| Shader | 著色器 | 著色器 | 保留並追蹤 |
| Mesh | 網格 | 網格 | 保留並追蹤 |
| Vertex / Vertices | 頂點 | 頂點 | 保留並追蹤 |
| Normal | 法向 | 法線 | 完整 msgid 為 Normal，且語境為空、Mesh 或 Render Layer |
| Object | 物體 | 物件 | 僅完整 msgid 為 Object |
| Texture | 紋理 | 貼圖 | draft，不套用，需區分程序紋理與影像貼圖 |
| Interpolation | 插值 | 內插 | draft，不套用，待審 |

此表是初始設定說明，最新有效規則請以 `terms.json` 為準；`report.json` 會自動收錄目前所有規則。

## 編輯規則

```json
{
  "id": "normal",
  "english": "Normal (surface direction)",
  "source": "法向",
  "target": "法線",
  "msgids": ["Normal"],
  "contexts": ["", "Mesh", "Render Layer"],
  "status": "active",
  "note": "限定幾何法線，不更動正常或標準。"
}
```

- `id`：不可重複的穩定識別碼。
- `english`：供人對照的英文術語；不參與比對。需要英文限制請填 `msgids`。
- `source`：**OpenCC 轉換後**要比對的繁體詞；不是簡體詞。採字面子字串比對，非正規表示式。
- `target`：修正後譯詞。可與 source 相同，用來記錄及追蹤已採用的譯名。
- `status`：`active` 套用；`draft` 僅列入清單，待人工審閱後啟用。
- `note`：選詞原因、審閱依據或待確認問題。
- `msgids`（選填）：英文完整 msgid 清單，精確且區分大小寫。複數翻譯依同一條目的單數 msgid 比對。
- `contexts`（選填）：完整 msgctxt 清單；空字串表示沒有語境。省略表示不限。

未設定範圍的規則會比對所有翻譯的文字片段，因此多義字應先設為 draft，或加上 msgids／contexts。字串內重疊詞以較長的 source 優先，僅替換一輪，避免 A→B→C 串接。規則不能包含格式參數、網址或標記；翻譯中的這些片段也不會被替換。

重複 id、無效欄位、重複啟用規則及同一條目內衝突的 source 會使同步失敗，避免發布有歧義的結果。空白翻譯不補寫，過時條目不套用術語，fuzzy 標記保留。

## 校訂流程

1. 在 `terms.json` 新增 draft 項目，記下英文、目前用詞、建議譯詞及原因。
2. 檢查英文 msgid 與 msgctxt，視需要縮小範圍；確認後改成 active。
3. 執行 `python -m unittest discover -s tests -v`，再執行既有同步指令。
4. 檢視 PO 差異與 `report.json`。報告列出每條規則的命中次數及最多三個英文條目／語境範例；命中次數包含保留原譯名的規則，並非改字數。draft 不執行比對，計數固定為 0。
5. 提交 terms.json。GitHub Actions 會立即重新產生翻譯、報告及術語表雜湊，即使上游沒有更新也會套用新用詞。

`report.json` 和 `zh_TW/` 都是自動產物，請勿直接修正；修改 source 或 scope 後命中數為 0，代表本次資料沒有符合條件的文字，應檢查範圍與上游譯詞。報告不是完整語言品質檢查，也不會自動判定尚未收錄的術語。
