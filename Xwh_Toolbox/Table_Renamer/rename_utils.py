import bpy
import csv
import pathlib

from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Context, Operator
from bpy.types import Object

from . import rename_utils_bk as backend

### Operators ###
class Xwh_OP_Rename_Export_Table(Operator, ExportHelper):
    bl_idname = "xwh_rename.export_table"
    bl_label = "Export table"
    bl_description = ""

    filename_ext = ".csv"
    filter_glob : StringProperty(   #type: ignore
        #default="*",
        default="*.csv;*.txt;*.morph;*.bone",
        options={'HIDDEN'}
    )

    filepath : StringProperty(  #type: ignore
        subtype= 'FILE_PATH',
        default="",
        options= {'HIDDEN'}
    )

    #Config
    separator : StringProperty(     #type: ignore
        name= "Separator",
        description= "File Separator",
        default= ",",
        maxlen= 1
    )

    scope : EnumProperty(   #type: ignore
        name = "Scope",
        description= "Where to read",
        items = [
            ('OBJ', "Object", ""),
            ('MORPH', "Shape Keys", ""),
            ("BONE", "Bones", "")
        ],
        default= "OBJ"
    )

    def draw(self, context: Context) -> None:
        layout = self.layout
        layout.alignment = 'CENTER'

        layout.prop(self, "scope")
        layout.prop(self, "separator")

    def execute(self, context: Context):
        backend.export_table(self, context,
                             path_str= self.filepath,
                             separator= self.separator,
                             scope= self.scope)
        return {'FINISHED'}

class Xwh_OP_Rename_Import_Table(Operator, ImportHelper):
    bl_idname = "xwh_rename.import_table"
    bl_label = "Import Table"
    bl_description = "Renames items in the selected scope based on a file"
    bl_options = {'REGISTER', 'UNDO'}

    #filename_ext = ".csv"
    filter_glob : StringProperty(   #type: ignore
            default="*.csv;*.txt;*.morph;*.bone",
            options={'HIDDEN'}
        )

    #Config
    separator : StringProperty(     #type: ignore
        name= "Separator",
        description= "File Separator",
        default= ",",
        maxlen= 1
    )

    filepath : StringProperty(  #type: ignore
        subtype= 'FILE_PATH',
        default="",
        options= {'HIDDEN'}
    )

    scope : EnumProperty(   #type: ignore
        name = "Scope",
        description= "Where to read",
        items = [
            ('OBJ', "Object", ""),
            ('MORPH', "Shape Keys", ""),
            ("BONE", "Bones", "")
        ],
        default= "OBJ"
    )

    
    def draw(self, context: Context):
        layout = self.layout
        layout.alignment = 'CENTER'

        layout.prop(self, "scope")
        layout.prop(self, "separator")
        

    def execute(self, context: Context):
        backend.import_table(self, context,
                             self.filepath,
                             self.separator,
                             self.scope)

        return {'FINISHED'}
