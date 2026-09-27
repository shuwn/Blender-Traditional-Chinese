"""Convert upstream PO translations; never modify source identifiers."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
from collections import Counter

import polib
from opencc import OpenCC

ROOT = Path(__file__).resolve().parents[1]
CONVERTER = OpenCC('s2twp')
# Preserve interpolation fields, markup, URLs, and Blender keyboard notation.
PROTECTED = re.compile(r'https?://[^\s<>]+|%\([^)]+\)[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z]|%[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z%]|\{[^{}]*\}|<[^>]*>')


class Glossary:
    """Validated, scoped, single-pass terminology replacements."""

    def __init__(self, path):
        raw = path.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        if not isinstance(data, dict) or set(data) != {'version', 'terms'} or data['version'] != 1 or not isinstance(data['terms'], list):
            raise ValueError('Glossary must contain version: 1 and a terms list')
        self.rules = data['terms']
        self.hits = Counter()
        self.samples = {}
        ids = set()
        selectors = set()
        required = {'id', 'english', 'source', 'target', 'status', 'note'}
        for rule in self.rules:
            if not isinstance(rule, dict) or not required <= rule.keys() or rule.keys() - required - {'msgids', 'contexts'}:
                raise ValueError('Unknown or missing glossary fields')
            if any(not isinstance(rule[key], str) or not rule[key].strip() for key in required):
                raise ValueError('Glossary text fields must be nonempty strings')
            if rule['id'] in ids or rule['status'] not in {'active', 'draft'}:
                raise ValueError(f"Duplicate id or invalid status: {rule['id']}")
            ids.add(rule['id'])
            for scope in ('msgids', 'contexts'):
                if scope in rule and (not isinstance(rule[scope], list) or not rule[scope] or
                                      any(not isinstance(value, str) for value in rule[scope])):
                    raise ValueError(f'{scope} must be a nonempty list of strings')
            if PROTECTED.search(rule['source']) or PROTECTED.search(rule['target']):
                raise ValueError('Glossary terms cannot contain protected tokens')
            selector = (rule['source'], tuple(sorted(rule.get('msgids', []))), tuple(sorted(rule.get('contexts', []))))
            if rule['status'] == 'active':
                if selector in selectors:
                    raise ValueError(f"Duplicate active selector: {rule['id']}")
                selectors.add(selector)

    def replacement(self, msgid, context, location):
        selected = {}
        for rule in self.rules:
            if rule['status'] != 'active':
                continue
            if 'msgids' in rule and msgid not in rule['msgids']:
                continue
            if 'contexts' in rule and (context or '') not in rule['contexts']:
                continue
            if rule['source'] in selected:
                raise ValueError(f'Overlapping glossary rules for {msgid!r}: {rule["source"]}')
            selected[rule['source']] = rule
        if not selected:
            return lambda text: text
        pattern = re.compile('|'.join(re.escape(term) for term in sorted(selected, key=lambda term: (-len(term), term))))

        def replace(text):
            def match_term(match):
                rule = selected[match.group()]
                self.hits[rule['id']] += 1
                sample = {'file': location, 'msgid': msgid, 'msgctxt': context or ''}
                samples = self.samples.setdefault(rule['id'], [])
                if sample not in samples and len(samples) < 3:
                    samples.append(sample)
                return rule['target']
            # One pass: replacement output is never fed into another rule.
            return pattern.sub(match_term, text)
        return replace

    def report(self):
        return {'glossary_sha256': self.sha256, 'terms': [
            {**rule, 'occurrences': self.hits[rule['id']], 'samples': self.samples.get(rule['id'], [])}
            for rule in self.rules]}


def convert_text(text, replace=lambda value: value):
    parts = []
    start = 0
    for match in PROTECTED.finditer(text):
        parts.extend((replace(CONVERTER.convert(text[start:match.start()])), match.group()))
        start = match.end()
    parts.append(replace(CONVERTER.convert(text[start:])))
    return ''.join(parts)


def convert_po(source, destination, glossary=None, location=''):
    po = polib.pofile(str(source), check_for_duplicates=True)
    po.metadata['Language'] = 'zh_TW'
    po.metadata['Language-Team'] = 'Traditional Chinese (Taiwan)'
    po.metadata['Plural-Forms'] = 'nplurals=1; plural=0;'
    po.metadata['X-Generator'] = 'OpenCC s2twp (automatic conversion)'
    for entry in po:
        replace = glossary.replacement(entry.msgid, entry.msgctxt, location) if glossary and not entry.obsolete else lambda value: value
        entry.msgstr = convert_text(entry.msgstr, replace)
        entry.msgstr_plural = {key: convert_text(value, replace) for key, value in entry.msgstr_plural.items()}
    destination.parent.mkdir(parents=True, exist_ok=True)
    po.save(str(destination))
    # Reparse and compile to catch structural failures before publishing.
    result = polib.pofile(str(destination), check_for_duplicates=True)
    assert len(result) == len(po)
    result.to_binary()


def sync(source, output, state, glossary_path=None, report_path=None):
    glossary = Glossary(glossary_path) if glossary_path else None
    files = sorted(source.rglob('*.po'))
    if not files:
        raise ValueError(f'No PO files in {source}; refusing to erase existing translations')
    inputs = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    manifest = {'source': 'https://projects.blender.org/blender/blender-ui-translations/src/branch/main/zh_HANS',
                'converter': 'OpenCC s2twp', 'files': inputs}
    if glossary:
        manifest['glossary_sha256'] = glossary.sha256
    # Always regenerate so converter/script updates also take effect. Git detects no-ops.
    with tempfile.TemporaryDirectory() as directory:
        staging = Path(directory)
        for file in files:
            relative = file.relative_to(source)
            if relative.name == 'zh_HANS.po':
                relative = relative.with_name('zh_TW.po')
            convert_po(file, staging / relative, glossary, str(file.relative_to(source)))
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
    if glossary and report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(glossary.report(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--glossary', type=Path, default=ROOT / 'glossary/terms.json')
    args = parser.parse_args()
    sync(args.source, ROOT / 'zh_TW', ROOT / 'sync-state.json', args.glossary, ROOT / 'glossary/report.json')
