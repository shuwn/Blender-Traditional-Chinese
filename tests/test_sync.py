import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
import polib

spec = importlib.util.spec_from_file_location('sync', Path(__file__).resolve().parents[1] / 'scripts/sync.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SyncTests(unittest.TestCase):
    def test_taiwan_and_placeholders(self):
        self.assertEqual(module.convert_text('软件和鼠标'), '軟體和滑鼠')
        for token in ['%(名称)s', '{名称}', '%04d', 'https://example.com/软件', '<标签>']:
            self.assertIn(token, module.convert_text('软件 ' + token))

    def test_roundtrip_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            po = polib.POFile()
            po.metadata = {'Language': 'zh_CN', 'Content-Type': 'text/plain; charset=UTF-8'}
            po.append(polib.POEntry(msgid='Software %s', msgctxt='Context', msgstr='软件 %s', flags=['fuzzy']))
            po.append(polib.POEntry(msgid='Empty', msgstr=''))
            po.append(polib.POEntry(msgid='Mouse', msgid_plural='Mice', msgstr_plural={0: '鼠标'}))
            po.save(str(source / 'zh_HANS.po'))
            output, state = root / 'output', root / 'state.json'
            module.sync(source, output, state)
            result = polib.pofile(str(output / 'zh_TW.po'))
            self.assertEqual(result[0].msgstr, '軟體 %s')
            self.assertEqual(result[0].msgid, 'Software %s')
            self.assertEqual(result[0].msgctxt, 'Context')
            self.assertEqual(result[0].flags, ['fuzzy'])
            self.assertEqual(result[1].msgstr, '')
            self.assertEqual(result[2].msgstr_plural, {0: '滑鼠'})
            before = (output / 'zh_TW.po').read_bytes(), state.read_bytes()
            module.sync(source, output, state)
            self.assertEqual(before, ((output / 'zh_TW.po').read_bytes(), state.read_bytes()))
            (source / 'zh_HANS.po').unlink()
            with self.assertRaises(ValueError):
                module.sync(source, output, state)
            self.assertEqual(before[0], (output / 'zh_TW.po').read_bytes())


class GlossaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / 'terms.json'

    def rule(self, source, target, **extra):
        return {'id': source, 'english': 'Example', 'source': source, 'target': target,
                'status': 'active', 'note': 'Test rule', **extra}

    def glossary(self, rules):
        self.path.write_text(json.dumps({'version': 1, 'terms': rules}), encoding='utf-8')
        return module.Glossary(self.path)

    def test_longest_match_single_pass_and_protected_tokens(self):
        glossary = self.glossary([self.rule('渲染', '算繪'), self.rule('渲染器', '算繪引擎'),
                                  self.rule('算繪', '不應串接'), self.rule('紋理', '貼圖', status='draft')])
        replace = glossary.replacement('Renderer', None, 'source.po')
        text = '渲染器 渲染 紋理 {渲染} %(渲染)s <渲染> https://example.com/渲染'
        result = module.convert_text(text, replace)
        self.assertEqual(result, '算繪引擎 算繪 紋理 {渲染} %(渲染)s <渲染> https://example.com/渲染')
        self.assertEqual(glossary.hits, {'渲染器': 1, '渲染': 1})

    def test_exact_msgid_and_context(self):
        glossary = self.glossary([self.rule('法向', '法線', msgids=['Normal'], contexts=['Mesh'])])
        for msgid, context, expected in [('Normal', 'Mesh', '法線'), ('Normal', 'Brush', '法向'),
                                          ('Normal', None, '法向'), ('Normal Map', 'Mesh', '法向')]:
            self.assertEqual(module.convert_text('法向', glossary.replacement(msgid, context, 'x.po')), expected)

    def test_invalid_rules_fail_before_output(self):
        invalid = [
            [self.rule('', '算繪')],
            [self.rule('渲染', '算繪', status='typo')],
            [self.rule('渲染', '算繪', msgids='Render')],
            [self.rule('渲染', '{name}')],
            [self.rule('渲染', '算繪'), self.rule('渲染', '其他', id='duplicate')],
            [self.rule('渲染', '算繪', unexpected=True)],
        ]
        for rules in invalid:
            with self.subTest(rules=rules), self.assertRaises(ValueError):
                self.glossary(rules)
        glossary = self.glossary([self.rule('渲染', '算繪'),
                                  self.rule('渲染', '其他', id='scoped', msgids=['Render'])])
        with self.assertRaises(ValueError):
            glossary.replacement('Render', None, 'x.po')

    def test_report_plural_and_glossary_only_update(self):
        source = self.root / 'source'
        source.mkdir()
        po = polib.POFile()
        po.metadata = {'Content-Type': 'text/plain; charset=UTF-8'}
        po.append(polib.POEntry(msgid='Keyframe', msgid_plural='Keyframes', msgstr_plural={0: '关键帧'}))
        po.append(polib.POEntry(msgid='Empty', msgstr=''))
        po.save(str(source / 'zh_HANS.po'))
        output, state, report = self.root / 'output', self.root / 'state.json', self.root / 'report.json'
        self.glossary([self.rule('關鍵幀', '關鍵影格')])
        module.sync(source, output, state, self.path, report)
        result = polib.pofile(str(output / 'zh_TW.po'))
        self.assertEqual(result[0].msgstr_plural, {0: '關鍵影格'})
        self.assertEqual(result[1].msgstr, '')
        self.assertEqual(json.loads(report.read_text())['terms'][0]['occurrences'], 1)
        self.assertEqual(json.loads(report.read_text())['terms'][0]['samples'][0]['msgid'], 'Keyframe')
        files = [output / 'zh_TW.po', state, report]
        before = [file.read_bytes() for file in files]
        module.sync(source, output, state, self.path, report)
        self.assertEqual(before, [file.read_bytes() for file in files])
        self.glossary([self.rule('關鍵幀', '關鍵影格', status='draft')])
        module.sync(source, output, state, self.path, report)
        self.assertEqual(polib.pofile(str(output / 'zh_TW.po'))[0].msgstr_plural, {0: '關鍵幀'})
        self.assertNotEqual(before[1], state.read_bytes())

    def test_repository_glossary_is_valid(self):
        glossary = module.Glossary(module.ROOT / 'glossary/terms.json')
        self.assertGreater(len(glossary.rules), 0)
