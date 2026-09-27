"""Convert upstream PO translations; never modify source identifiers."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

import polib
from opencc import OpenCC

ROOT = Path(__file__).resolve().parents[1]
CONVERTER = OpenCC('s2twp')
# Preserve interpolation fields, markup, URLs, and Blender keyboard notation.
PROTECTED = re.compile(r'https?://[^\s<>]+|%\([^)]+\)[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z]|%[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z%]|\{[^{}]*\}|<[^>]*>')


def convert_text(text):
    parts = []
    start = 0
    for match in PROTECTED.finditer(text):
        parts.extend((CONVERTER.convert(text[start:match.start()]), match.group()))
        start = match.end()
    parts.append(CONVERTER.convert(text[start:]))
    return ''.join(parts)


def convert_po(source, destination):
    po = polib.pofile(str(source), check_for_duplicates=True)
    po.metadata['Language'] = 'zh_TW'
    po.metadata['Language-Team'] = 'Traditional Chinese (Taiwan)'
    po.metadata['Plural-Forms'] = 'nplurals=1; plural=0;'
    po.metadata['X-Generator'] = 'OpenCC s2twp (automatic conversion)'
    for entry in po:
        entry.msgstr = convert_text(entry.msgstr)
        entry.msgstr_plural = {key: convert_text(value) for key, value in entry.msgstr_plural.items()}
    destination.parent.mkdir(parents=True, exist_ok=True)
    po.save(str(destination))
    # Reparse and compile to catch structural failures before publishing.
    result = polib.pofile(str(destination), check_for_duplicates=True)
    assert len(result) == len(po)
    result.to_binary()


def sync(source, output, state):
    files = sorted(source.rglob('*.po'))
    if not files:
        raise ValueError(f'No PO files in {source}; refusing to erase existing translations')
    inputs = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    manifest = {'source': 'https://projects.blender.org/blender/blender-ui-translations/src/branch/main/zh_HANS',
                'converter': 'OpenCC s2twp', 'files': inputs}
    # Always regenerate so converter/script updates also take effect. Git detects no-ops.
    with tempfile.TemporaryDirectory() as directory:
        staging = Path(directory)
        for file in files:
            relative = file.relative_to(source)
            if relative.name == 'zh_HANS.po':
                relative = relative.with_name('zh_TW.po')
            convert_po(file, staging / relative)
        output.mkdir(parents=True, exist_ok=True)
        expected = set()
        for file in staging.rglob('*.po'):
            relative = file.relative_to(staging)
            expected.add(relative)
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(file.read_bytes())
        for file in output.rglob('*.po'):
            if file.relative_to(output) not in expected:
                file.unlink()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    sync(args.source, ROOT / 'zh_TW', ROOT / 'sync-state.json')
