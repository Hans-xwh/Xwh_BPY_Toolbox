# Copyright (C) 2026 Hans_Xwh - Licensed under the MIT license.

import bpy
import csv

from pathlib import Path
from bpy.types import Context, Operator
from bpy.types import Object

def export_table(op:Operator, context:Context, path_str:str, separator:str, scope:str):
    #Context
    if context.active_object is None or not context.selected_objects: return
    objects:list[Object] = [obj for obj in context.selected_objects]

    #Prevent overwrite
    filepath = Path(path_str)
    if filepath.suffix == ".blend": filepath = filepath.with_suffix(".csv")

    #Now do stuff
    with filepath.open(mode='w', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=separator, lineterminator="\n")

        writer.writerow(["#Old Name", "New Name"])

        if scope == 'OBJ':
            for obj in objects:
                writer.writerow([obj.name, obj.name])

        elif scope == 'MORPH':
            for obj in objects:
                if obj.type != 'MESH' or not obj.data or not obj.data.shape_keys: continue

                for key_block in obj.data.shape_keys.key_blocks:
                    if key_block.name == "Basis" : continue

                    writer.writerow([key_block.name, key_block.name])

        elif scope == 'BONE':
            for obj in objects:
                if obj.type != 'ARMATURE' or not obj.data: continue

                for bone in obj.data.bones:
                    writer.writerow([bone.name, bone.name])

    print(f"Exported to: {path_str}")
    return

def import_table(op:Operator, context:Context, path_str:str, separator:str, scope:str):
    filepath = Path(path_str)
    if not filepath.exists(): return

    obj = context.active_object
    if not obj: return

    with filepath.open(mode="r") as file:
        reader = csv.reader(file, delimiter=separator)
        namings:dict[str, str] = dict()

        #Rread
        for row in reader:
            if len(row) < 2 or row[0].startswith("#"): continue

            namings[row[0]] = row[1]

    #Rename
    if scope == 'OBJ':
        for obj in context.selected_objects:
            new_name = namings.get(obj.name, None)
            if new_name is not None:
                print(f"Renamed: {obj.name} -> {new_name}")
                obj.name = new_name

    elif scope == 'MORPH':    #This one just on active object
        if obj.type != 'MESH' or not obj.data or not obj.data.shape_keys: return
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name == "Basis": continue

            new_name = namings.get(key_block.name, None)
            if new_name is not None:
                print(f"Renamed: {key_block.name} -> {new_name}")
                key_block.name = new_name

    elif scope == 'BONES':
        if obj.type != 'ARMATURE' or not obj.data: return
        for bone in obj.data.bones:
            new_name = namings.get(bone.name, None)
            if new_name is not None:
                print(f"Renamed: {bone.name} -> {new_name}")
                bone.name = new_name

    return
