import bpy


from bpy.types import Context, Panel

class Xwh_Rename_PT_Main(Panel):
    bl_label = "Xwh Renamer"
    bl_idname = "XWH_PT_Rename_Main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Xwh"

    def draw(self, context: Context) -> None:
        layout = self.layout

        layout.operator("xwh_rename.import_table")
        layout.operator("xwh_rename.export_table")