"""Exercise the release inside Blender using temporary catalogs/settings only."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def test(blender, locale_root):
    with tempfile.TemporaryDirectory(prefix='blender-taiwan-smoke-') as directory:
        root = Path(directory)
        locale = root / 'datafiles/locale'
        locale.mkdir(parents=True)
        shutil.copyfile(locale_root / 'languages', locale / 'languages')
        language = next(name for name in ('zh_HANT', 'zh_TW') if (locale_root / name / 'LC_MESSAGES/blender.mo').is_file())
        target = locale / language / 'LC_MESSAGES/blender.mo'
        target.parent.mkdir(parents=True)
        original = locale_root / language / 'LC_MESSAGES/blender.mo'
        shutil.copyfile(original, target)
        with zipfile.ZipFile(ROOT / 'dist/Blender-Taiwan-Chinese.zip') as archive:
            archive.extractall(root / 'addons')
        env = dict(os.environ, BLENDER_SYSTEM_DATAFILES=str(root / 'datafiles'),
                   BLENDER_USER_CONFIG=str(root / 'config'), BLENDER_USER_SCRIPTS=str(root / 'scripts'))
        shared = f'''
import bpy, sys
from pathlib import Path
sys.path.insert(0, {str(root / 'addons')!r})
import blender_taiwan_chinese as addon
assert Path(bpy.utils.system_resource('DATAFILES', path='locale')).resolve() == Path({str(locale)!r}).resolve()
assert Path(bpy.utils.user_resource('CONFIG', create=True)).resolve() == Path({str(root / 'config')!r}).resolve()
addon.register()
'''
        install = shared + f'''
assert bpy.ops.taiwan_chinese.install() == {{'FINISHED'}}
assert Path({str(target)!r}).read_bytes() == Path({str(root / 'addons/blender_taiwan_chinese/blender.mo')!r}).read_bytes()
addon.unregister()
print('INSTALL_SMOKE_OK')
'''
        restore = shared + f'''
bpy.context.preferences.view.language = {language!r}
bpy.context.preferences.view.use_translate_interface = True
assert bpy.app.translations.pgettext('Render') == '算繪', bpy.app.translations.pgettext('Render')
assert bpy.ops.taiwan_chinese.restore() == {{'FINISHED'}}
assert Path({str(target)!r}).read_bytes() == Path({str(original)!r}).read_bytes()
addon.unregister()
print('TRANSLATION_AND_RESTORE_SMOKE_OK')
'''
        for code in (install, restore):
            script = root / 'smoke.py'
            script.write_text(code, encoding='utf-8')
            subprocess.run([str(blender), '--background', '--factory-startup', '--python-exit-code', '1',
                            '--python', str(script)], env=env, check=True, timeout=120)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--blender', type=Path, required=True)
    parser.add_argument('--locale-root', type=Path, required=True)
    args = parser.parse_args()
    test(args.blender, args.locale_root)
