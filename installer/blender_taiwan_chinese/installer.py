"""Backup and replace one existing Blender catalog. Standard library only."""
import gettext
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def find_catalog(locale_root):
    root = Path(locale_root)
    for language in ('zh_HANT', 'zh_TW'):
        path = root / language / 'LC_MESSAGES' / 'blender.mo'
        if path.is_file():
            return path, language
    raise ValueError('找不到 Blender 原有的繁體中文 blender.mo；請使用包含官方語言檔的 Blender。')


def backup_slot(target, backup_root):
    return Path(backup_root) / digest(str(Path(target).resolve()).encode('utf-8'))[:24]


def load_backup(target, backup_root):
    slot = backup_slot(target, backup_root)
    state = json.loads((slot / 'state.json').read_text(encoding='utf-8'))
    original = (slot / 'original.mo').read_bytes()
    if state['target'] != str(Path(target).resolve()) or digest(original) != state['original_sha256']:
        raise ValueError('備份驗證失敗；停止替換，請保留備份並檢查檔案。')
    return slot, state, original


def install(target, payload, backup_root, expected_sha256):
    target, payload = Path(target), Path(payload)
    content = payload.read_bytes()
    if digest(content) != expected_sha256:
        raise ValueError('下載的翻譯檔校驗失敗，請重新下載發行包。')
    gettext.GNUTranslations(io.BytesIO(content))
    current = target.read_bytes()
    slot = backup_slot(target, backup_root)
    if (slot / 'state.json').exists():
        slot, state, _ = load_backup(target, backup_root)
        if digest(current) not in {state['original_sha256'], state['installed_sha256']}:
            raise ValueError('Blender 語言檔已被更新或由其他工具修改；請勿覆蓋。請先停用本工具，確認原版後移存該安裝路徑的舊備份。')
    else:
        if digest(current) == expected_sha256:
            raise ValueError('目前已是此翻譯，但找不到原版備份；請保留現況或先修復 Blender 原版語言檔。')
        if (slot / 'original.mo').exists() and (slot / 'original.mo').read_bytes() != current:
            raise ValueError('發現未完成安裝的不同備份；請先檢查備份，避免覆蓋原版。')
        atomic_write(slot / 'original.mo', current)
        state = {'target': str(target.resolve()), 'original_sha256': digest(current)}
    state['installed_sha256'] = expected_sha256
    atomic_write(target, content)
    try:
        atomic_write(slot / 'state.json', (json.dumps(state, indent=2) + '\n').encode('utf-8'))
    except Exception:
        atomic_write(target, current)
        raise
    return slot


def restore(target, backup_root):
    target = Path(target)
    slot, state, original = load_backup(target, backup_root)
    if digest(target.read_bytes()) not in {state['installed_sha256'], state['original_sha256']}:
        raise ValueError('目前語言檔已被更新或修改；停止還原，避免用舊備份覆蓋新版 Blender。')
    atomic_write(target, original)
    return slot
