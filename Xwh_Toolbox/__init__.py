# Copyright (C) 2026 Hans_Xwh - Licensed under the MIT license.

from . import Single_Files
from . import Table_Renamer

def register():
    Single_Files.register()
    Table_Renamer.register()
    
    print("\nXwh Toolbox registered")

def unregister():
    Single_Files.unregister()
    Table_Renamer.unregister()

    print("Xwh Toolbox unregistered")
