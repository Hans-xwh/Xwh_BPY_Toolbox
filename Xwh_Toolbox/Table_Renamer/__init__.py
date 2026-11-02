# Copyright (C) 2026 Hans_Xwh - Licensed under the MIT license.

import bpy

from . import rename_utils
from . import rename_ui


classes = [
    rename_utils.Xwh_OP_Rename_Import_Table,
    rename_utils.Xwh_OP_Rename_Export_Table,
    rename_ui.Xwh_Rename_PT_Main
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
