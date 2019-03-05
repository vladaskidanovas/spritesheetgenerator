# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import pip
from bpy.props import *

from mathutils import Euler

import os, math, time



bl_info = {
    "name" : "Sprite Sheet Generator",
    "author" : "Vladislovas Kidanovas",
    "description" : "Sprite sheet generator, Addon for Blender 2.8",
    "blender" : (2, 80, 0),
    "location" : "",
    "warning" : "",
    "category" : "Render"
}

bpy.types.Scene.num_angles = IntProperty(
    name = "Z Angles Per Rotation",
    description = "Enter an integer",
    default = 0)

bpy.types.Scene.render_object = StringProperty()

bpy.types.Scene.tmp_image_output = StringProperty(
    name = "Temporary Storage",
    description = "Temporary Image Storage",
    subtype = "DIR_PATH",
    default = "/tmp/")

bpy.types.Scene.sprite_sheet_padding = IntProperty(
    name = "Padding",
    description = "Sets a padding between sprites",
    default = 2)

bpy.types.Scene.sprite_sheet_image_output = StringProperty(
    name = "Sprite Sheet Image",
    description = "Output file for sprite sheet image",
    subtype = "FILE_PATH",
    default = "/tmp/sprite_sheet.png")

class SSG_OT_sprite_sheet_generator(bpy.types.Operator):
    bl_idname = "render.sprite_sheet_generator"
    bl_label = "Sprite sheet generator"

    @classmethod
    def poll(cls, context):
        return context.scene != None

    def execute(self, context):
        scene = context.scene

        if scene.render_object == None or scene.render_object == '' or scene.objects[scene.render_object] == None:
            self.report({'ERROR_INVALID_INPUT'}, "Missing render object")
            return {'CANCELLED'}

        obj = scene.objects[scene.render_object]
        angles = scene.num_angles
        output = scene.tmp_image_output

        org_rotation = obj.rotation_euler.copy()
        files = []
        all_angles = []

        if angles == 0:
            all_angles = [0]
        else:
            all_angles = range(0, 360, angles)

        for i in all_angles:

            zangle = i * math.pi / 180.0
            obj.rotation_euler = Euler((org_rotation.x, org_rotation.y, org_rotation.z + zangle), 'XYZ')

            bpy.context.scene.render.filepath = output + "%d_####" % i
            bpy.ops.render.render(animation=True)
            for frame in range(int(scene.frame_start), int(scene.frame_end) + 1):
                filename = "{filepath}{frame:04d}{extension}".format(
                    filepath = scene.render.filepath.replace("#", ""),
                    frame = frame,
                    extension = scene.render.file_extension)
                files.append(filename)

        # Restore rotation
        obj.rotation_euler = org_rotation

        max_frames_row = 10.0
        frames = []
        tile_width = 0
        tile_height = 0

        spritesheet_width = 0
        spritesheet_height = 0

        files = os.listdir(output)
        files.sort()

        for current_file in files :
            try:
                print(current_file)
                with Image.open(output + current_file) as im :
                    frames.append(im.getdata())
            except:
                print(current_file + " is not a valid image")
        
        tile_width = frames[0].size[0]
        tile_height = frames[0].size[1]

        if len(frames) > max_frames_row :
            spritesheet_width = tile_width * max_frames_row
            required_rows = math.ceil(len(frames)/max_frames_row)
            spritesheet_height = tile_height * required_rows
        else:
            spritesheet_width = tile_width*len(frames)
            spritesheet_height = tile_height
            
        print(spritesheet_height)
        print(spritesheet_width)

        spritesheet = Image.new("RGBA",(int(spritesheet_width), int(spritesheet_height)))

        for current_frame in frames :
            top = tile_height * math.floor((frames.index(current_frame))/max_frames_row)
            left = tile_width * (frames.index(current_frame) % max_frames_row)
            bottom = top + tile_height
            right = left + tile_width
            
            box = (left,top,right,bottom)
            box = [int(i) for i in box]
            cut_frame = current_frame.crop((0,0,tile_width,tile_height))
            
            spritesheet.paste(cut_frame, box)
            
        spritesheet.save("spritesheet" + time.strftime("%Y-%m-%dT%H-%M-%S") + ".png", "PNG")


        return {'FINISHED'}

class SSG_PT_sprite_sheet_panel(bpy.types.Panel):
    bl_idname = "SSG_PT_sprite_sheet_panel"
    bl_label = "Sprite Sheet Generator"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context  = "render"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        if scene == None:
            return

        row = layout.row()

        row.label(text='Animation settings')

        row = layout.row()
        row.prop(scene, "frame_start")

        row = layout.row()
        row.prop(scene, "frame_end")

        row = layout.row()
        row.prop(scene, "num_angles")

        layout.prop_search(scene, "render_object", context.scene, "objects", text="Object:")

        layout.separator()
        layout.label(text='Output')

        row = layout.row()
        row.prop(scene, 'tmp_image_output')

        row = layout.row()
        row.prop(scene, 'sprite_sheet_image_output')

        row = layout.row()
        row.prop(scene, 'sprite_sheet_padding')

        row = layout.row()
        layout.separator()
        layout.label(text="Render")

        row = layout.row()
        row.scale_y = 3.0

        row.operator(SSG_OT_sprite_sheet_generator.bl_idname)

classes = (SSG_OT_sprite_sheet_generator, SSG_PT_sprite_sheet_panel)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    

    if int(pip.__version__.split('.')[0])>9:
        from pip._internal import main
    else:
        from pip import main

    main(['install', 'Pillow'])

    from PIL import Image

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":register()