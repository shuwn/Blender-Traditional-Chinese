import importlib.util
from pathlib import Path
import tempfile
import unittest
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
