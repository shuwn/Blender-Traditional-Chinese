import gettext
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import polib

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load('installer', ROOT / 'installer/blender_taiwan_chinese/installer.py')
builder = load('builder', ROOT / 'scripts/build_release.py')


def catalog(text):
    po = polib.POFile()
    po.metadata = {'Content-Type': 'text/plain; charset=UTF-8'}
    po.append(polib.POEntry(msgid='Render', msgstr=text))
    return po.to_binary()


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.target = self.root / 'locale/zh_HANT/LC_MESSAGES/blender.mo'
        self.target.parent.mkdir(parents=True)
        self.original = catalog('原版')
        self.target.write_bytes(self.original)
        self.payload = self.root / 'blender.mo'
        self.payload.write_bytes(catalog('算繪'))
        self.backup = self.root / 'backup'

    def install(self):
        return installer.install(self.target, self.payload, self.backup, installer.digest(self.payload.read_bytes()))

    def test_install_update_restore_and_independent_backups(self):
        slot = self.install()
        self.assertEqual(self.target.read_bytes(), self.payload.read_bytes())
        self.install()
        self.payload.write_bytes(catalog('新版算繪'))
        self.install()
        self.assertEqual((slot / 'original.mo').read_bytes(), self.original)
        installer.restore(self.target, self.backup)
        installer.restore(self.target, self.backup)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertNotEqual(slot, installer.backup_slot(self.root / 'other/blender.mo', self.backup))
        self.install()
        self.assertEqual(self.target.read_bytes(), self.payload.read_bytes())

    def test_tampering_and_external_update_are_rejected(self):
        with self.assertRaises(ValueError):
            installer.install(self.target, self.payload, self.backup, 'wrong')
        self.assertEqual(self.target.read_bytes(), self.original)
        self.install()
        self.target.write_bytes(catalog('Blender 已更新'))
        before = self.target.read_bytes()
        with self.assertRaises(ValueError):
            self.install()
        with self.assertRaises(ValueError):
            installer.restore(self.target, self.backup)
        self.assertEqual(self.target.read_bytes(), before)

    def test_corrupt_backup_is_rejected(self):
        slot = self.install()
        (slot / 'original.mo').write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            installer.restore(self.target, self.backup)

    def test_state_write_failure_rolls_back_catalog(self):
        real_write = installer.atomic_write
        def fail_state(path, data):
            if Path(path).name == 'state.json':
                raise PermissionError('test')
            return real_write(path, data)
        with patch.object(installer, 'atomic_write', side_effect=fail_state), self.assertRaises(PermissionError):
            self.install()
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_locale_detection(self):
        self.assertEqual(installer.find_catalog(self.root / 'locale'), (self.target, 'zh_HANT'))
        (self.root / 'locale/zh_HANT').rename(self.root / 'locale/zh_TW')
        self.assertEqual(installer.find_catalog(self.root / 'locale')[1], 'zh_TW')
        with self.assertRaises(ValueError):
            installer.find_catalog(self.root / 'missing')


class ReleaseTests(unittest.TestCase):
    def test_reproducible_archive_and_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['installer', 'docs', 'glossary']:
                shutil.copytree(ROOT / name, root / name)
            shutil.copyfile(ROOT / 'LICENSE.upstream', root / 'LICENSE.upstream')
            (root / 'zh_TW').mkdir()
            po = polib.POFile()
            po.metadata = {'Content-Type': 'text/plain; charset=UTF-8', 'Project-Id-Version': 'Blender test'}
            po.append(polib.POEntry(msgid='Render', msgstr='算繪'))
            po.append(polib.POEntry(msgid='Fuzzy', msgstr='模糊', flags=['fuzzy']))
            po.append(polib.POEntry(msgid='Old', msgstr='舊', obsolete=True))
            po.append(polib.POEntry(msgid='Empty', msgstr=''))
            po.save(str(root / 'zh_TW/zh_TW.po'))
            tag = builder.build(root)
            package = root / 'dist/Blender-Taiwan-Chinese.zip'
            initial = package.read_bytes()
            self.assertEqual(builder.build(root), tag)
            self.assertEqual(package.read_bytes(), initial)
            with zipfile.ZipFile(package) as archive:
                self.assertIn('blender_taiwan_chinese/__init__.py', archive.namelist())
                mo = archive.read('blender_taiwan_chinese/blender.mo')
                metadata = json.loads(archive.read('blender_taiwan_chinese/metadata.json'))
                self.assertEqual(metadata['mo_sha256'], hashlib.sha256(mo).hexdigest())
                translation = gettext.GNUTranslations(io.BytesIO(mo))
                self.assertEqual(translation.gettext('Render'), '算繪')
                for text in ['Fuzzy', 'Old', 'Empty']:
                    self.assertEqual(translation.gettext(text), text)
            for line in (root / 'dist/SHA256SUMS.txt').read_text().splitlines():
                digest, name = line.split('  ')
                self.assertEqual(digest, hashlib.sha256((root / 'dist' / name).read_bytes()).hexdigest())
