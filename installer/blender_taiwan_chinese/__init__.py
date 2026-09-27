bl_info = {
    'name': 'Blender 台灣繁體中文 / Taiwan Chinese',
    'author': 'Blender Traditional Chinese contributors',
    'version': (1, 0, 0),
    'blender': (4, 2, 0),
    'location': 'Preferences > Add-ons > Taiwan Chinese',
    'description': '安裝台灣繁體中文翻譯，保留原版備份並提供還原',
    'category': 'Interface',
}

from pathlib import Path
import json
import bpy
from . import installer

PACKAGE = Path(__file__).parent


def locations():
    locale_root = bpy.utils.system_resource('DATAFILES', path='locale')
    if not locale_root:
        raise ValueError('找不到 Blender 系統語言資料夾。')
    target, language = installer.find_catalog(locale_root)
    backup = Path(bpy.utils.user_resource('CONFIG', path='taiwan_chinese_backups', create=True))
    return target, language, backup


class TAIWAN_OT_install(bpy.types.Operator):
    bl_idname = 'taiwan_chinese.install'
    bl_label = '套用台灣繁體中文'
    bl_description = '備份並替換 Blender 繁體中文語言檔；重新啟動後生效'

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        try:
            target, language, backup = locations()
            metadata = json.loads((PACKAGE / 'metadata.json').read_text(encoding='utf-8'))
            installer.install(target, PACKAGE / 'blender.mo', backup, metadata['mo_sha256'])
        except PermissionError:
            self.report({'ERROR'}, '無法寫入 Blender 安裝目錄。請參閱發行包 INSTALL.md 的權限處理方式。')
            return {'CANCELLED'}
        except (OSError, ValueError, KeyError) as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        try:
            context.preferences.view.language = language
            context.preferences.view.use_translate_interface = True
            context.preferences.view.use_translate_tooltips = True
            bpy.ops.wm.save_userpref()
        except Exception:
            self.report({'WARNING'}, '翻譯已安裝；請手動選擇繁體中文並儲存偏好設定，然後重新啟動 Blender。')
            return {'FINISHED'}
        self.report({'INFO'}, '已備份並安裝台灣繁體中文。請重新啟動 Blender。')
        return {'FINISHED'}


class TAIWAN_OT_restore(bpy.types.Operator):
    bl_idname = 'taiwan_chinese.restore'
    bl_label = '還原原版繁體中文'
    bl_description = '還原首次安裝前的語言檔；重新啟動後生效'

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        try:
            target, _, backup = locations()
            installer.restore(target, backup)
        except (OSError, ValueError, KeyError) as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        self.report({'INFO'}, '已還原原版繁體中文。請重新啟動 Blender。')
        return {'FINISHED'}


class TAIWAN_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        layout.label(text='替換原有繁體中文；套用前會保留原版備份。')
        layout.label(text='停用或移除工具不會還原翻譯，請先按「還原原版」。')
        try:
            metadata = json.loads((PACKAGE / 'metadata.json').read_text(encoding='utf-8'))
            layout.label(text='翻譯來源：' + metadata['upstream_project'])
            layout.label(text='來源版本與目前 Blender 不同時，部分字串可能保留英文。')
            target, _, backup = locations()
            layout.label(text='語言檔：' + str(target))
            layout.label(text='備份：' + str(installer.backup_slot(target, backup)))
        except (OSError, ValueError, KeyError) as error:
            layout.label(text=str(error), icon='ERROR')
        layout.operator('taiwan_chinese.install', icon='IMPORT')
        layout.operator('taiwan_chinese.restore', icon='LOOP_BACK')


CLASSES = (TAIWAN_OT_install, TAIWAN_OT_restore, TAIWAN_preferences)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
