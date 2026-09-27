"""Build deterministic, dependency-free Blender add-on and manual catalogs."""
import hashlib
import json
from pathlib import Path
import zipfile

import polib

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    output = root / 'dist'
    output.mkdir(exist_ok=True)
    po_path = root / 'zh_TW/zh_TW.po'
    po = polib.pofile(str(po_path), check_for_duplicates=True)
    mo = po.to_binary()  # polib omits fuzzy, untranslated and obsolete entries.
    metadata = {
        'upstream_project': po.metadata.get('Project-Id-Version', 'unknown'),
        'po_sha256': hashlib.sha256(po_path.read_bytes()).hexdigest(),
        'mo_sha256': hashlib.sha256(mo).hexdigest(),
        'glossary_sha256': hashlib.sha256((root / 'glossary/terms.json').read_bytes()).hexdigest(),
        'catalog_entries': len(po),
        'compiled_entries': len(po.translated_entries()),
        'supported_locale_names': ['zh_HANT', 'zh_TW'],
        'minimum_blender_version': '4.2',
    }
    metadata_bytes = (json.dumps(metadata, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    files = {file.name: file.read_bytes() for file in (root / 'installer/blender_taiwan_chinese').glob('*.py')}
    files.update({'blender.mo': mo, 'metadata.json': metadata_bytes,
                  'LICENSE.upstream': (root / 'LICENSE.upstream').read_bytes(),
                  'INSTALL.md': (root / 'docs/INSTALL.md').read_bytes()})
    package = output / 'Blender-Taiwan-Chinese.zip'
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo('blender_taiwan_chinese/' + name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    (output / 'blender.mo').write_bytes(mo)
    (output / 'zh_TW.po').write_bytes(po_path.read_bytes())
    (output / 'metadata.json').write_bytes(metadata_bytes)
    (output / 'INSTALL.md').write_bytes((root / 'docs/INSTALL.md').read_bytes())
    (output / 'LICENSE.upstream').write_bytes((root / 'LICENSE.upstream').read_bytes())
    names = ['Blender-Taiwan-Chinese.zip', 'blender.mo', 'zh_TW.po', 'metadata.json', 'INSTALL.md', 'LICENSE.upstream']
    checksums = ''.join(f'{hashlib.sha256((output / name).read_bytes()).hexdigest()}  {name}\n' for name in names)
    (output / 'SHA256SUMS.txt').write_text(checksums, encoding='utf-8')
    tag = 'tw-' + hashlib.sha256(package.read_bytes()).hexdigest()[:16]
    (output / 'release-tag.txt').write_text(tag + '\n', encoding='utf-8')
    notes = f'''台灣繁體中文翻譯，含專業術語修正。

下載 **Blender-Taiwan-Chinese.zip**，在 Blender「編輯 → 偏好設定 → 附加元件」選擇「從磁碟安裝 / Install from Disk」，選取 ZIP，啟用 Taiwan Chinese，展開設定後按「套用台灣繁體中文」，再重新啟動 Blender。

工具會備份並替換原有繁體中文，也提供「還原原版繁體中文」。翻譯會寫入 Blender 安裝目錄，需要該目錄的寫入權限。更新 Blender 後可能需要重新套用；移除工具前請先還原。

翻譯來源：{metadata['upstream_project']}。此包追蹤上游 main，並非各版 Blender 的專屬翻譯；版本不符時部分字串可能保留英文。編譯收錄 {metadata['compiled_entries']:,} 筆，排除 fuzzy、空白及過時條目。

安裝工具目標為 Blender 4.2+；原生檔名自動辨識 zh_HANT / zh_TW。詳閱 [安裝與還原說明](https://github.com/shuwn/Blender-Traditional-Chinese/blob/main/docs/INSTALL.md)。

也提供 blender.mo（手動替換）、zh_TW.po（翻譯來源）、metadata.json（版本資訊）、SHA256SUMS.txt（校驗碼）及上游授權。
'''
    (output / 'RELEASE_NOTES.md').write_text(notes, encoding='utf-8')
    return tag


if __name__ == '__main__':
    print(build())
