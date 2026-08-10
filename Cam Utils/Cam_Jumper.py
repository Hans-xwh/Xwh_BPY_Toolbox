import bpy
from bpy.types import Operator, Panel, Object, Camera, Keyframe, FCurve

from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty

## To enable, run from text editor ##

### Stuff stolen from a3da parser ###
def getChannelbag(target:bpy.types.ID, anim_data:bpy.types.AnimData|None=None, ensure=False) -> bpy.types.ActionChannelbag | None: #Should work on anything
    if anim_data is None:
        anim_data = target.animation_data
    if not anim_data: return None

    action = anim_data.action
    if not action or not action.layers or not action.layers[0].strips: return None #Idk if this can even trigger, but better safe than sorry
    
    return action.layers[0].strips[0].channelbag(anim_data.action_slot, ensure=ensure)


### Operators ###
class XWH_Cam_OT_Fix_Jumps(Operator):
    bl_idname = "xwh_cam.fix_jumps"
    bl_label = "Fix Camera Jumps"
    bl_description = "Fixes camera jumps being screwed up by scaling animation"
    bl_options = {"REGISTER", "UNDO"}

    op_mode: EnumProperty(      #type: ignore
        name= "Mode",
        description="",
        items=[
            ('FCURVE', "Fcurve", "Treats fcurves individually"),
            ('OBJECT', "Object", "Checks for jumps at all fcurves of an object at the same time")
        ],
        default= 'OBJECT'
    )

    use_trans: BoolProperty(    #type: ignore
        name="Translation",
        default= True
    )

    use_rot: BoolProperty(    #type: ignore
        name="Rotation",
        default= True
    )

    use_scale: BoolProperty(    #type: ignore
        name="Scale",
        default= True
    )

    use_cam: BoolProperty(  #type: ignore
        name = "Cam",
        default= True
    )

    use_other: BoolProperty(  #type: ignore
        name = "Other",
        default= True
    )

    trns_threshold: FloatProperty(      #type: ignore
        name="Distance Sensitive",
        default=1,
        min=0.0,
        subtype='DISTANCE'
    )

    rot_threshold: FloatProperty(      #type: ignore
        name="Angle Sensitive",
        default=0.087266,   #5 degrees in radians
        min=0.0,
        subtype='ANGLE'
    )

    frame_threshold: FloatProperty(      #type: ignore
        name="Frame Threshold",
        description= "Distance the moved keyframes will keep from their neighbours",
        default = 0.05,
        min = 0.05,
        max = 1
    )

    curve_tolerance: FloatProperty( #type: ignore
        name = "Curve tolerance",
        description= "Forgiveness on acceleration, like an elasticity factor. Higher values makes the algorithm more strict on changes, and prone to false positives",
        default= 2.0,
        min= 0.1,
        max= 10
    )

    make_constant: BoolProperty(    #type:ignore
        name="Make Constant",
        description="Make moved keyframes constant. Ensures 0 jumpiness",
        default=False
    )

    min_keys:IntProperty(   #type:ignore
        name= "Minimum scope size",
        description="",
        min= 0,
        default= 3
    )

    max_keys:IntProperty(   #type:ignore
        name= "Maximum scope size",
        description="",
        min= 2,
        default= 10
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self,
                width=250,
                title="Fix Camera Jumps",
                )

    def draw(self, context):
        layout = self.layout

        layout.label(text="Affected Curves")
        row1 = layout.row()
        row1.emboss = 'PIE_MENU'
        row1.alignment = 'CENTER'
        row1.prop(self, 'use_trans')
        row1.prop(self, 'use_rot')
        row1.prop(self, 'use_scale')
        row2 = layout.row()
        row2.emboss = 'PIE_MENU'
        row2.alignment = 'CENTER'
        row2.prop(self, 'use_cam')
        row2.prop(self, 'use_other')

        layout.separator()
        layout.prop(self, 'op_mode')

        layout.label(text="Sensitivity")
        layout.prop(self, "trns_threshold")
        layout.prop(self, "rot_threshold")
        layout.prop(self, "frame_threshold")
        layout.prop(self, 'curve_tolerance')

        layout.separator()

        layout.label(text= "Configuration")
        layout.prop(self, 'min_keys')
        layout.prop(self, 'max_keys')
        layout.prop(self, 'make_constant')

    def execute(self, context):
        def get_rate(k1:Keyframe, k2:Keyframe) -> float:
            return (k2.co.y - k1.co.y) / (k2.co.x - k1.co.x)

        def get_avg(lst:list[float]):
            return sum(lst) / len(lst)

        def fix_handles(key:Keyframe, prev_key:Keyframe, next_key:Keyframe):
            def fix_handle_side(key:Keyframe, neighbour:Keyframe, is_left:bool):
                if not neighbour or not key: return

                handle = key.handle_left if is_left else key.handle_right

                #Calc old slope
                old_dx = (key.co.x - handle.x) if is_left else (handle.x - key.co.x)
                old_dy = (key.co.y - handle.y) if is_left else (handle.y - key.co.y)
                slope = (old_dy / old_dx) if old_dx else 0.0

                new_dx = abs(key.co.x - neighbour.co.x) / 3.0   #This ensure resulting data is a3da compatible
                new_dy = slope * new_dx

                if is_left:
                    key.handle_left.x = key.co.x - new_dx
                    key.handle_left.y = key.co.y - new_dy
                else:
                    key.handle_right.x = key.co.x + new_dx
                    key.handle_right.y = key.co.y + new_dy

                return

            key.handle_left_type = key.handle_right_type = 'FREE'
            fix_handle_side(key, prev_key, True)
            fix_handle_side(key, next_key, False)

            return

        def unjump_fcurve(fcurve:bpy.types.FCurve, threshold:float):
            min_rate = self.min_keys
            max_rate = self.max_keys

            if min_rate > max_rate: max_rate = min_rate + 2

            rates:list[float] = []

            for i in range(len(fcurve.keyframe_points)-1):
                key1:Keyframe = fcurve.keyframe_points[i]
                key2:Keyframe = fcurve.keyframe_points[i+1]

                #Skip keys on the same frame
                if (key1.co.x == key2.co.x): continue

                #Build min ammount of rates
                if len(rates) < min_rate:
                    rates.append(get_rate(key1, key2))
                    continue

                #Check rate of change
                change_rate = get_rate(key1, key2)
                avg_rate = get_avg(rates)

                dynamic_threshold = threshold + (abs(avg_rate) * self.curve_tolerance)

                if abs(change_rate - avg_rate) < dynamic_threshold:  #Case OK
                    rates.append(change_rate)
                else:                                              #Case nono
                    key1.co.x = key2.co.x - self.frame_threshold    #Move key
                    if self.make_constant: key1.interpolation = "CONSTANT"

                    #Ensure handles are ok
                    key0 = fcurve.keyframe_points[i-1] if i > 0 else None
                    key3 = fcurve.keyframe_points[i+2] if i+2 < len(fcurve.keyframe_points) else None

                    fix_handles(key1, key0, key2)
                    fix_handles(key2, key1, key3)

                    if key0:
                        key0_prev = fcurve.keyframe_points[i-2] if i > 1 else None
                        fix_handles(key0, key0_prev, key1)

                    rates.clear()
                    continue

                if len(rates) > max_rate:
                    rates.pop(0)

            fcurve.update()
            return

##################################################
        corrected = 0

        for obj in context.selected_objects:
            channelbag = getChannelbag(obj)
            if not channelbag: continue

            trans_list:list[str] = []
            if self.use_trans: trans_list.append('location')
            if self.use_rot: 
                trans_list.append('rotation_euler')
                trans_list.append('quaternion')
            if self.use_scale: trans_list.append('scale')

            #Build list with all fcurves to operate
            fcurve_list:list[tuple[FCurve, float]] = []       #Each fcurve is saved with the tolerance threshold it will use
            for transform in trans_list:
                for i in range(3):
                    fcurve = channelbag.fcurves.find(transform, index=i)
                    if not fcurve: continue

                    if transform in ('rotation_euler', 'quaternion'):
                        threshold = self.rot_threshold
                    else:
                        threshold = self.trns_threshold

                    fcurve_list.append((fcurve, threshold))

            #Treat camera differently
            if obj.type == 'CAMERA':
                #A3DA FOV
                fcurve = channelbag.fcurves.find('auth3d_cam.fov')
                if fcurve:
                    fcurve_list.append((fcurve, self.rot_threshold))
                    

                cam_channelbag = getChannelbag(obj.data)
                if cam_channelbag: 
                    fcurve = cam_channelbag.fcurves.find('lens')
                    if fcurve: fcurve_list.append((fcurve, self.trns_threshold))

            ## Transforms ##
            #for transform in ('location', 'rotation_euler', 'scale'):
            #    if transform in ('rotation_euler', 'quaternion'):
            #        threshold = self.rot_threshold
            #    else:
            #        threshold = self.trns_threshold
#
            #    for i in range(3):
            #        fcurve:bpy.types.FCurve = channelbag.fcurves.find(transform, index=i)
            #        if not fcurve: continue
#
            #        unjump_fcurve(fcurve, threshold)
#
            #        corrected += 1

            #Case camera
            #if obj.type == 'CAMERA':
            #    #A3DA FOV
            #    fcurve = channelbag.fcurves.find('auth3d_cam.fov')
            #    if fcurve:
            #        unjump_fcurve(fcurve, self.rot_threshold)
            #        corrected += 1
#
            #    cam_channelbag = getChannelbag(obj.data)
            #    if not cam_channelbag: continue
#
            #    #Focal length
            #    fcurve = cam_channelbag.fcurves.find('lens')
            #    if fcurve:
            #        unjump_fcurve(fcurve, self.trns_threshold)
            #        corrected += 1

            #########################
            #### Operate Fcurves ####
            #########################
            if self.op_mode == 'FCURVE':
                for fc_set in fcurve_list:
                    unjump_fcurve(fc_set[0], fc_set[1])

            elif self.op_mode == 'OBJECT':

                pass



        self.report({'INFO'}, f"Fixed {corrected} fcurves")
        return {'FINISHED'}

### Panels ###
class XWH_PT_Cam_Fix_Jumps(Panel):
    bl_label = "Fix jumps"
    bl_idname = "XWH_PT_Cam_Fix_Jumps"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    bl_category = 'XWH'

    def draw(self, context):
        layout = self.layout
        layout.operator("xwh_cam.fix_jumps", text="Fix Camera Jumps")


classes = [
    XWH_Cam_OT_Fix_Jumps,
    XWH_PT_Cam_Fix_Jumps
]


##########################
def register():
    if hasattr(bpy.types, "XWH_Cam_OT_Fix_Jumps"): unregister()

    for cls in classes:
        bpy.utils.register_class(cls)

    print("XWH Cam Jumper registered")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# Run from Blender's text editor
if __name__ == "<run_path>" or __name__ == '__main__':
    register()
